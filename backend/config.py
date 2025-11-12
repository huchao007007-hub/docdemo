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
    
    # Qdrant向量数据库配置
    QDRANT_HOST = os.getenv("QDRANT_HOST", "118.89.121.9")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "pdf_summary_vectors")
    QDRANT_TIMEOUT = int(os.getenv("QDRANT_TIMEOUT", 30))  # 超时时间（秒）
    
    # 向量配置
    # Embedding模型配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")  # 默认使用中文优化模型
    # 注意：不同模型的向量维度不同
    # text2vec-base-chinese: 768维
    # paraphrase-multilingual-MiniLM-L12-v2: 384维
    # OpenAI text-embedding-3-small: 1536维
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", 768))  # 默认768（text2vec-base-chinese）
    TEXT_CHUNK_SIZE = int(os.getenv("TEXT_CHUNK_SIZE", 1000))  # 文本分块大小（字符数）
    TEXT_CHUNK_OVERLAP = int(os.getenv("TEXT_CHUNK_OVERLAP", 200))  # 分块重叠大小（字符数）
    
    # HuggingFace镜像源配置（解决网络访问问题）
    HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")  # 例如: https://hf-mirror.com
    
    # 确保上传目录存在
    @staticmethod
    def ensure_upload_dir():
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)

