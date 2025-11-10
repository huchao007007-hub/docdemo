from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    """用户注册模型"""
    username: str
    password: str
    email: str = None

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str
    remember_me: bool = False

class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str

class UserInfo(BaseModel):
    """用户信息模型"""
    id: int
    username: str
    email: str = None
    created_at: str

    class Config:
        from_attributes = True

