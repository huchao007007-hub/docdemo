from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database import Base

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)  # 加密后的密码
    email = Column(String(100), nullable=True)  # 可选邮箱
    is_active = Column(Boolean, default=True)  # 账户是否激活
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class PDFFile(Base):
    """PDF文件表"""
    __tablename__ = "pdf_files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # 所属用户
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=True)  # 提取的文本内容
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Summary(Base):
    """总结表"""
    __tablename__ = "summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_file_id = Column(Integer, ForeignKey("pdf_files.id"), nullable=False)
    summary_content = Column(Text, nullable=False)
    token_used = Column(Integer, nullable=True)  # 使用的token数量
    created_at = Column(DateTime, server_default=func.now())

