# 后端服务说明

## 启动方式

### 方式1: 直接运行
```bash
python main.py
```

### 方式2: 使用uvicorn
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API文档

启动服务后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 环境变量说明

在 `.env` 文件中配置：

- `DEEPSEEK_API_KEY`: DeepSeek API密钥（必需）
- `DEEPSEEK_BASE_URL`: DeepSeek API地址（默认：https://api.deepseek.com/v1）
- `DATABASE_URL`: MySQL数据库连接字符串
- `UPLOAD_DIR`: 上传文件存储目录（默认：./uploads）
- `MAX_FILE_SIZE`: 最大文件大小，单位字节（默认：10485760，即10MB）

## 数据库初始化

首次运行会自动创建数据库表。

如需手动创建：
```python
from database import Base, engine
from models import PDFFile, Summary
Base.metadata.create_all(bind=engine)
```

