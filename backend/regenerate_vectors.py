#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新生成所有PDF文件的向量
用于模型切换后重新生成向量
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_db
from models import PDFFile
from services.vector_service import VectorService
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_all_vectors():
    """为所有已上传的PDF文件重新生成向量"""
    
    # 初始化向量服务
    try:
        vector_service = VectorService()
        if not vector_service.qdrant_client:
            logger.error("Qdrant客户端未初始化，无法生成向量")
            return False
    except Exception as e:
        logger.error(f"向量服务初始化失败: {str(e)}")
        return False
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 获取所有有文本内容的PDF文件
        pdf_files = db.query(PDFFile).filter(
            PDFFile.text_content.isnot(None),
            PDFFile.text_content != ""
        ).all()
        
        if not pdf_files:
            logger.warning("没有找到需要生成向量的PDF文件")
            return True
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件需要生成向量")
        
        success_count = 0
        fail_count = 0
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"正在为文件生成向量: {pdf_file.original_filename} (ID: {pdf_file.id})")
                
                # 先删除旧的向量（如果存在）
                try:
                    vector_service.delete_document(pdf_file.id, pdf_file.user_id)
                    logger.debug(f"已删除文件 {pdf_file.id} 的旧向量")
                except Exception as e:
                    logger.debug(f"删除旧向量失败（可能不存在）: {str(e)}")
                
                # 生成新向量
                success = vector_service.add_document(
                    pdf_file_id=pdf_file.id,
                    user_id=pdf_file.user_id,
                    filename=pdf_file.original_filename,
                    text_content=pdf_file.text_content
                )
                
                if success:
                    success_count += 1
                    logger.info(f"✓ 文件 {pdf_file.original_filename} 向量生成成功")
                else:
                    fail_count += 1
                    logger.warning(f"✗ 文件 {pdf_file.original_filename} 向量生成失败")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"✗ 文件 {pdf_file.original_filename} 处理失败: {str(e)}")
        
        logger.info("=" * 60)
        logger.info(f"向量生成完成:")
        logger.info(f"  成功: {success_count} 个文件")
        logger.info(f"  失败: {fail_count} 个文件")
        logger.info("=" * 60)
        
        return fail_count == 0
        
    except Exception as e:
        logger.error(f"重新生成向量失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()

def regenerate_user_vectors(user_id: int):
    """为指定用户的所有PDF文件重新生成向量"""
    
    # 初始化向量服务
    try:
        vector_service = VectorService()
        if not vector_service.qdrant_client:
            logger.error("Qdrant客户端未初始化，无法生成向量")
            return False
    except Exception as e:
        logger.error(f"向量服务初始化失败: {str(e)}")
        return False
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 获取指定用户的所有有文本内容的PDF文件
        pdf_files = db.query(PDFFile).filter(
            PDFFile.user_id == user_id,
            PDFFile.text_content.isnot(None),
            PDFFile.text_content != ""
        ).all()
        
        if not pdf_files:
            logger.warning(f"用户 {user_id} 没有找到需要生成向量的PDF文件")
            return True
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件需要生成向量（用户ID: {user_id}）")
        
        success_count = 0
        fail_count = 0
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"正在为文件生成向量: {pdf_file.original_filename} (ID: {pdf_file.id})")
                
                # 先删除旧的向量（如果存在）
                try:
                    vector_service.delete_document(pdf_file.id, pdf_file.user_id)
                    logger.debug(f"已删除文件 {pdf_file.id} 的旧向量")
                except Exception as e:
                    logger.debug(f"删除旧向量失败（可能不存在）: {str(e)}")
                
                # 生成新向量
                success = vector_service.add_document(
                    pdf_file_id=pdf_file.id,
                    user_id=pdf_file.user_id,
                    filename=pdf_file.original_filename,
                    text_content=pdf_file.text_content
                )
                
                if success:
                    success_count += 1
                    logger.info(f"✓ 文件 {pdf_file.original_filename} 向量生成成功")
                else:
                    fail_count += 1
                    logger.warning(f"✗ 文件 {pdf_file.original_filename} 向量生成失败")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"✗ 文件 {pdf_file.original_filename} 处理失败: {str(e)}")
        
        logger.info("=" * 60)
        logger.info(f"向量生成完成（用户ID: {user_id}）:")
        logger.info(f"  成功: {success_count} 个文件")
        logger.info(f"  失败: {fail_count} 个文件")
        logger.info("=" * 60)
        
        return fail_count == 0
        
    except Exception as e:
        logger.error(f"重新生成向量失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="重新生成PDF文件的向量")
    parser.add_argument(
        "--user-id",
        type=int,
        default=None,
        help="只重新生成指定用户的向量（可选）"
    )
    
    args = parser.parse_args()
    
    if args.user_id:
        logger.info(f"开始为用户 {args.user_id} 重新生成向量...")
        success = regenerate_user_vectors(args.user_id)
    else:
        logger.info("开始为所有用户重新生成向量...")
        success = regenerate_all_vectors()
    
    if success:
        logger.info("所有向量重新生成成功！")
        sys.exit(0)
    else:
        logger.error("部分向量生成失败，请查看日志")
        sys.exit(1)

