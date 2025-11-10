# 环境变量配置说明

## 创建.env文件

在 `backend` 目录下创建 `.env` 文件，内容如下：

```env
# DeepSeek API配置（已配置，无需修改）
DEEPSEEK_API_KEY=sk-e79c5ddba7324e58bbffa901ea368756
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 数据库配置（需要根据实际情况修改）
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/pdf_summary?charset=utf8mb4

# 文件存储配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# 服务器配置
HOST=0.0.0.0
PORT=8000

# OCR配置（可选，如果Tesseract和Poppler不在PATH中）
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
# POPPLER_PATH=C:\poppler\Library\bin
```

## 重要说明

1. **DeepSeek API Key**: 已经配置好了，无需修改
2. **数据库连接**: 需要修改为你的MySQL用户名和密码
   - 格式：`mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4`
   - 示例：`mysql+pymysql://root:123456@localhost:3306/pdf_summary?charset=utf8mb4`

## 快速创建方法

### Windows PowerShell
```powershell
cd backend
@"
DEEPSEEK_API_KEY=sk-e79c5ddba7324e58bbffa901ea368756
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DATABASE_URL=mysql+pymysql://root:你的密码@localhost:3306/pdf_summary?charset=utf8mb4
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
HOST=0.0.0.0
PORT=8000
# OCR配置（可选，如果不在PATH中）
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
# POPPLER_PATH=C:\poppler\Library\bin
"@ | Out-File -FilePath .env -Encoding utf8
```

### Linux/Mac
```bash
cd backend
cat > .env << EOF
DEEPSEEK_API_KEY=sk-e79c5ddba7324e58bbffa901ea368756
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DATABASE_URL=mysql+pymysql://root:你的密码@localhost:3306/pdf_summary?charset=utf8mb4
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
HOST=0.0.0.0
PORT=8000
# OCR配置（可选，如果不在PATH中）
# TESSERACT_CMD=/usr/bin/tesseract
# POPPLER_PATH=/usr/bin
EOF
```

**记得将"你的密码"替换为实际的MySQL密码！**

