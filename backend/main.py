from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
import uuid
import shutil
import urllib.parse
from typing import Optional
import logging

from config import Config
from database import get_db, Base, engine
from models import PDFFile, Summary, User
from services.pdf_parser import PDFParser
from services.ai_service import AIService
from services.auth_service import AuthService
from schemas.auth import UserRegister, UserLogin, Token, UserInfo

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 确保上传目录存在
Config.ensure_upload_dir()

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title="PDF总结小程序API",
    description="基于DeepSeek AI的PDF文档总结服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该设置具体的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
pdf_parser = PDFParser()
ai_service = AIService()
auth_service = AuthService()

# JWT认证
security = HTTPBearer(auto_error=False)  # 允许可选认证，用于PDF查看
security_required = HTTPBearer()  # 必需认证

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_required),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户"""
    token = credentials.credentials
    user = auth_service.get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@app.get("/")
async def root():
    """根路径"""
    return {"message": "PDF总结小程序API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}

# ==================== 认证相关接口 ====================

@app.get("/api/auth/check-users")
async def check_users_exist(db: Session = Depends(get_db)):
    """检查数据库中是否存在用户"""
    has_users = auth_service.check_user_exists(db)
    return JSONResponse({
        "success": True,
        "has_users": has_users
    })

@app.post("/api/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名长度
    if len(user_data.username) < 3:
        raise HTTPException(status_code=400, detail="用户名至少需要3个字符")
    
    if len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少需要6个字符")
    
    user = auth_service.register_user(
        db=db,
        username=user_data.username,
        password=user_data.password,
        email=user_data.email
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="用户名已存在或注册失败")
    
    # 自动登录，返回token
    token = auth_service.create_user_token(user)
    
    return JSONResponse({
        "success": True,
        "message": "注册成功",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
    })

@app.post("/api/auth/login")
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = auth_service.authenticate_user(
        db=db,
        username=user_data.username,
        password=user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    token = auth_service.create_user_token(user, remember_me=user_data.remember_me)
    
    return JSONResponse({
        "success": True,
        "message": "登录成功",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }
    })

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return JSONResponse({
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat()
        }
    })

# ==================== PDF相关接口（需要认证） ====================

@app.post("/api/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传PDF文件并提取文本
    
    Args:
        file: 上传的PDF文件
        db: 数据库会话
        
    Returns:
        上传结果和文件信息
    """
    try:
        # 检查文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
        # 检查文件大小
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, 
                detail=f"文件大小超过限制（最大 {Config.MAX_FILE_SIZE / 1024 / 1024}MB）"
            )
        
        # 生成唯一文件名
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(Config.UPLOAD_DIR, saved_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
        
        # 提取PDF文本（先不使用OCR，如果失败再尝试）
        text_content = pdf_parser.extract_text(file_path, use_ocr=False)
        use_ocr = False
        
        # 如果无法提取文本，尝试OCR识别（用于扫描版PDF）
        if not text_content:
            logger.info(f"尝试使用OCR识别PDF文本: {file.filename}")
            text_content = pdf_parser.extract_text(file_path, use_ocr=True)
            use_ocr = True
        
        # 即使无法提取文本，也允许上传（用户至少可以查看PDF）
        # 保存到数据库
        pdf_record = PDFFile(
            user_id=current_user.id,
            filename=saved_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            text_content=text_content  # 可以为None
        )
        db.add(pdf_record)
        db.commit()
        db.refresh(pdf_record)
        
        logger.info(f"PDF文件上传成功: {file.filename}, ID: {pdf_record.id}")
        
        # 根据是否提取到文本返回不同的消息
        if not text_content:
            message = "文件上传成功，但无法提取文本内容（可能是扫描版PDF或文件损坏），无法生成AI总结，但可以查看PDF文件"
        elif use_ocr:
            message = "文件上传成功，已通过OCR识别提取文本内容"
        else:
            message = "文件上传成功"
        
        return JSONResponse({
            "success": True,
            "message": message,
            "data": {
                "id": pdf_record.id,
                "filename": pdf_record.original_filename,
                "file_size": pdf_record.file_size,
                "text_length": len(text_content) if text_content else 0,
                "has_text": text_content is not None,
                "used_ocr": use_ocr,
                "created_at": pdf_record.created_at.isoformat()
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"上传文件失败: {str(e)}")

@app.post("/api/summarize/{file_id}")
async def summarize_pdf(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    对PDF文件进行AI总结
    
    Args:
        file_id: PDF文件ID
        db: 数据库会话
        
    Returns:
        总结结果
    """
    try:
        # 查找PDF文件（确保属于当前用户）
        pdf_file = db.query(PDFFile).filter(
            PDFFile.id == file_id,
            PDFFile.user_id == current_user.id
        ).first()
        
        if not pdf_file:
            raise HTTPException(status_code=404, detail="PDF文件不存在")
        
        # 检查是否已有总结
        existing_summary = db.query(Summary).filter(
            Summary.pdf_file_id == file_id
        ).first()
        
        if existing_summary:
            logger.info(f"返回已有总结，文件ID: {file_id}")
            return JSONResponse({
                "success": True,
                "message": "总结已存在",
                "data": {
                    "id": existing_summary.id,
                    "summary": existing_summary.summary_content,
                    "token_used": existing_summary.token_used,
                    "created_at": existing_summary.created_at.isoformat()
                }
            })
        
        # 检查是否有文本内容
        if not pdf_file.text_content:
            raise HTTPException(
                status_code=400, 
                detail="该PDF文件无法提取文本内容（可能是扫描版PDF或文件损坏），无法生成AI总结。即使使用了OCR识别也无法提取文本，请检查PDF文件或使用其他工具处理。"
            )
        
        # 调用AI服务进行总结
        logger.info(f"开始AI总结，文件ID: {file_id}, 文本长度: {len(pdf_file.text_content)}")
        
        summary_text, token_used = ai_service.summarize_text(pdf_file.text_content)
        
        if not summary_text:
            raise HTTPException(status_code=500, detail="AI总结失败，请稍后重试")
        
        # 保存总结到数据库
        summary_record = Summary(
            pdf_file_id=file_id,
            summary_content=summary_text,
            token_used=token_used
        )
        db.add(summary_record)
        db.commit()
        db.refresh(summary_record)
        
        logger.info(f"AI总结成功，文件ID: {file_id}, 总结ID: {summary_record.id}")
        
        return JSONResponse({
            "success": True,
            "message": "总结生成成功",
            "data": {
                "id": summary_record.id,
                "summary": summary_record.summary_content,
                "token_used": summary_record.token_used,
                "created_at": summary_record.created_at.isoformat()
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成总结失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成总结失败: {str(e)}")

@app.get("/api/files")
async def get_files(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取文件列表
    
    Args:
        skip: 跳过数量
        limit: 返回数量
        db: 数据库会话
        
    Returns:
        文件列表
    """
    try:
        # 只查询当前用户的文件
        files = db.query(PDFFile).filter(
            PDFFile.user_id == current_user.id
        ).offset(skip).limit(limit).all()
        
        total = db.query(PDFFile).filter(
            PDFFile.user_id == current_user.id
        ).count()
        
        file_list = []
        for file in files:
            has_summary = db.query(Summary).filter(
                Summary.pdf_file_id == file.id
            ).first() is not None
            
            file_list.append({
                "id": file.id,
                "filename": file.original_filename,
                "file_size": file.file_size,
                "text_length": len(file.text_content) if file.text_content else 0,
                "has_text": file.text_content is not None,
                "has_summary": has_summary,
                "created_at": file.created_at.isoformat()
            })
        
        return JSONResponse({
            "success": True,
            "data": {
                "files": file_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
        })
    
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件列表失败: {str(e)}")

@app.get("/api/files/{file_id}")
async def get_file_detail(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取文件详情
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        文件详情和总结
    """
    try:
        pdf_file = db.query(PDFFile).filter(
            PDFFile.id == file_id,
            PDFFile.user_id == current_user.id
        ).first()
        
        if not pdf_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        summary = db.query(Summary).filter(
            Summary.pdf_file_id == file_id
        ).first()
        
        result = {
            "id": pdf_file.id,
            "filename": pdf_file.original_filename,
            "file_size": pdf_file.file_size,
            "text_length": len(pdf_file.text_content) if pdf_file.text_content else 0,
            "created_at": pdf_file.created_at.isoformat(),
            "summary": None
        }
        
        if summary:
            result["summary"] = {
                "id": summary.id,
                "content": summary.summary_content,
                "token_used": summary.token_used,
                "created_at": summary.created_at.isoformat()
            }
        
        return JSONResponse({
            "success": True,
            "data": result
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取文件详情失败: {str(e)}")

@app.get("/api/files/{file_id}/view")
async def view_pdf_file(
    file_id: int,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    查看PDF文件
    
    Args:
        file_id: 文件ID
        token: 可选的token查询参数（用于iframe访问）
        db: 数据库会话
        credentials: HTTP认证凭证
        
    Returns:
        PDF文件流
    """
    try:
        # 支持从查询参数或HTTP header获取token
        auth_token = None
        if token:
            auth_token = token
        elif credentials:
            auth_token = credentials.credentials
        
        if not auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="需要认证"
            )
        
        # 验证用户
        user = auth_service.get_current_user(db, auth_token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
        
        pdf_file = db.query(PDFFile).filter(
            PDFFile.id == file_id,
            PDFFile.user_id == user.id
        ).first()
        
        if not pdf_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        if not os.path.exists(pdf_file.file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 处理中文文件名编码（RFC 5987格式）
        encoded_filename = urllib.parse.quote(pdf_file.original_filename.encode('utf-8'))
        
        # 返回PDF文件
        return FileResponse(
            path=pdf_file.file_path,
            filename=pdf_file.original_filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查看PDF文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查看PDF文件失败: {str(e)}")

@app.delete("/api/files/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除文件
    
    Args:
        file_id: 文件ID
        db: 数据库会话
        
    Returns:
        删除结果
    """
    try:
        pdf_file = db.query(PDFFile).filter(
            PDFFile.id == file_id,
            PDFFile.user_id == current_user.id
        ).first()
        
        if not pdf_file:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 删除文件
        if os.path.exists(pdf_file.file_path):
            os.remove(pdf_file.file_path)
        
        # 删除数据库记录（级联删除总结）
        db.query(Summary).filter(Summary.pdf_file_id == file_id).delete()
        db.delete(pdf_file)
        db.commit()
        
        logger.info(f"文件删除成功: {file_id}")
        
        return JSONResponse({
            "success": True,
            "message": "文件删除成功"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)

