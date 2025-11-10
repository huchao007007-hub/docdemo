from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User
from utils.auth import verify_password, get_password_hash, create_access_token, verify_token
from datetime import timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务"""
    
    @staticmethod
    def register_user(db: Session, username: str, password: str, email: str = None) -> Optional[User]:
        """
        注册新用户
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            
        Returns:
            创建的用户对象，如果失败返回None
        """
        try:
            # 检查用户名是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                logger.warning(f"用户名已存在: {username}")
                return None
            
            # 创建新用户
            hashed_password = get_password_hash(password)
            new_user = User(
                username=username,
                password_hash=hashed_password,
                email=email
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            logger.info(f"用户注册成功: {username}")
            return new_user
        
        except IntegrityError:
            db.rollback()
            logger.error(f"用户注册失败: 数据库约束错误")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"用户注册失败: {str(e)}")
            return None
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户身份
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            用户对象，如果验证失败返回None
        """
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                logger.warning(f"用户不存在: {username}")
                return None
            
            if not verify_password(password, user.password_hash):
                logger.warning(f"密码错误: {username}")
                return None
            
            if not user.is_active:
                logger.warning(f"用户账户未激活: {username}")
                return None
            
            logger.info(f"用户认证成功: {username}")
            return user
        
        except Exception as e:
            logger.error(f"用户认证失败: {str(e)}")
            return None
    
    @staticmethod
    def create_user_token(user: User, remember_me: bool = False) -> str:
        """
        为用户创建JWT token
        
        Args:
            user: 用户对象
            remember_me: 是否记住我（影响token过期时间）
            
        Returns:
            JWT token字符串
        """
        # 记住我：30天，否则7天
        expires_delta = timedelta(days=30) if remember_me else timedelta(days=7)
        
        token_data = {
            "sub": str(user.id),
            "username": user.username
        }
        
        return create_access_token(token_data, expires_delta)
    
    @staticmethod
    def get_current_user(db: Session, token: str) -> Optional[User]:
        """
        从token获取当前用户
        
        Args:
            db: 数据库会话
            token: JWT token
            
        Returns:
            用户对象，如果验证失败返回None
        """
        payload = verify_token(token)
        if not payload:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user
        except Exception as e:
            logger.error(f"获取用户失败: {str(e)}")
            return None
    
    @staticmethod
    def check_user_exists(db: Session) -> bool:
        """
        检查数据库中是否存在用户
        
        Returns:
            如果存在用户返回True，否则返回False
        """
        try:
            count = db.query(User).count()
            return count > 0
        except Exception as e:
            logger.error(f"检查用户失败: {str(e)}")
            return False

