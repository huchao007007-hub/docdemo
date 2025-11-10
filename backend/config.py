import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/pdf_summary?charset=utf8mb4")
    
    # 文件存储配置
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # OCR配置（可选，如果不在PATH中）
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", None)  # Tesseract可执行文件路径，如: C:\Program Files\Tesseract-OCR\tesseract.exe
    POPPLER_PATH = os.getenv("POPPLER_PATH", None)  # Poppler bin目录路径，如: C:\poppler\Library\bin
    
    # 确保上传目录存在
    @staticmethod
    def ensure_upload_dir():
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

