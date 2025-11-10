# 快速设置指南

## 环境准备

### 1. 安装Python 3.9+
```bash
python --version
```

### 2. 安装Node.js 16+
```bash
node --version
npm --version
```

### 3. 安装MySQL 8.0+
确保MySQL服务已启动

## 后端设置（5分钟）

### 步骤1: 进入后端目录
```bash
cd backend
```

### 步骤2: 创建虚拟环境
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 步骤3: 安装依赖
```bash
pip install -r requirements.txt
```

### 步骤4: 创建数据库
打开MySQL，执行：
```sql
CREATE DATABASE pdf_summary CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 步骤5: 配置环境变量
编辑 `backend/.env` 文件，修改数据库连接：
```
DATABASE_URL=mysql+pymysql://用户名:密码@localhost:3306/pdf_summary?charset=utf8mb4
```

例如：
```
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/pdf_summary?charset=utf8mb4
```

**注意**: DeepSeek API Key已经配置好了，无需修改。

### 步骤6: 创建上传目录
```bash
mkdir uploads
```

### 步骤7: 启动后端
```bash
# Windows
python main.py
# 或双击 start.bat

# Linux/Mac
python main.py
# 或 chmod +x start.sh && ./start.sh
```

后端将在 `http://localhost:8000` 启动

## 前端设置（3分钟）

### 步骤1: 进入前端目录
```bash
cd frontend
```

### 步骤2: 安装依赖
```bash
npm install
```

### 步骤3: 启动前端
```bash
# Windows
npm run dev
# 或双击 start.bat

# Linux/Mac
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 验证安装

1. 打开浏览器访问 `http://localhost:3000`
2. 尝试上传一个PDF文件
3. 点击"生成总结"按钮
4. 查看AI生成的总结

## 常见问题

### Q: 后端启动失败，提示数据库连接错误
**A**: 检查 `.env` 文件中的数据库连接字符串是否正确，MySQL服务是否启动

### Q: 前端无法连接后端
**A**: 确保后端服务已启动在 `http://localhost:8000`，检查防火墙设置

### Q: 上传PDF后提示无法提取文本
**A**: 可能是扫描版PDF（图片），当前版本不支持OCR，请使用文本版PDF

### Q: AI总结失败
**A**: 检查DeepSeek API Key是否正确，网络连接是否正常

## 下一步

- 查看API文档：`http://localhost:8000/docs`
- 阅读完整README：查看根目录的 `README.md`

