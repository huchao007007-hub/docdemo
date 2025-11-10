# PDF文档智能总结小程序

基于Vue3 + FastAPI + DeepSeek AI的PDF文档总结工具

## 技术栈

### 前端
- Vue 3 (Composition API)
- Element Plus
- Vite
- Axios

### 后端
- Python 3.9+
- FastAPI
- pdfplumber (PDF解析)
- DeepSeek API (AI总结)
- SQLAlchemy (ORM)
- MySQL (数据库)

## 项目结构

```
docdemo/
├── backend/              # 后端代码
│   ├── main.py          # FastAPI主应用
│   ├── config.py        # 配置文件
│   ├── database.py      # 数据库配置
│   ├── models.py        # 数据模型
│   ├── services/        # 业务服务
│   │   ├── pdf_parser.py    # PDF解析服务
│   │   └── ai_service.py    # AI总结服务
│   ├── requirements.txt # Python依赖
│   └── .env            # 环境变量（需要创建）
├── frontend/           # 前端代码
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── api/        # API接口
│   │   ├── router/     # 路由配置
│   │   └── App.vue     # 根组件
│   ├── package.json    # 前端依赖
│   └── vite.config.js  # Vite配置
└── README.md           # 项目说明
```

## 快速开始

### 1. 环境要求

- Python 3.9+
- Node.js 16+
- MySQL 8.0+

### 2. 后端设置

#### 2.1 创建虚拟环境

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 2.2 安装依赖

```bash
pip install -r requirements.txt
```

#### 2.3 配置数据库

创建MySQL数据库：

```sql
CREATE DATABASE pdf_summary CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2.4 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，修改以下配置：
- `DEEPSEEK_API_KEY`: 你的DeepSeek API密钥（已配置）
- `DATABASE_URL`: 数据库连接字符串（根据实际情况修改）

#### 2.5 创建上传目录

```bash
mkdir uploads
```

#### 2.6 启动后端服务

```bash
python main.py
```

或者使用uvicorn：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动

### 3. 前端设置

#### 3.1 安装依赖

```bash
cd frontend
npm install
```

#### 3.2 启动开发服务器

```bash
npm run dev
```

前端服务将在 `http://localhost:3000` 启动

#### 3.3 构建生产版本

```bash
npm run build
```

## 功能特性

- ✅ PDF文件上传
- ✅ 自动提取PDF文本内容
- ✅ AI智能总结（基于DeepSeek）
- ✅ 文件列表管理
- ✅ 总结结果展示
- ✅ 文件删除功能

## API接口

### 上传PDF文件
```
POST /api/upload
Content-Type: multipart/form-data
```

### 生成总结
```
POST /api/summarize/{file_id}
```

### 获取文件列表
```
GET /api/files?skip=0&limit=10
```

### 获取文件详情
```
GET /api/files/{file_id}
```

### 删除文件
```
DELETE /api/files/{file_id}
```

## 注意事项

1. **API密钥安全**: `.env` 文件包含敏感信息，不要提交到Git仓库
2. **文件大小限制**: 默认最大10MB，可在配置中修改
3. **数据库**: 确保MySQL服务已启动
4. **DeepSeek API**: 需要有效的API密钥才能使用AI总结功能

## 开发说明

### 后端开发

- 使用FastAPI框架，支持自动API文档
- 访问 `http://localhost:8000/docs` 查看Swagger文档
- 数据库模型使用SQLAlchemy ORM

### 前端开发

- 使用Vue 3 Composition API
- Element Plus组件库
- Vite作为构建工具

## 常见问题

### Q: 上传PDF后无法提取文本？
A: 可能是扫描版PDF，需要OCR功能（当前版本不支持）

### Q: AI总结失败？
A: 检查DeepSeek API密钥是否正确，以及网络连接是否正常

### Q: 数据库连接失败？
A: 检查MySQL服务是否启动，以及数据库连接字符串是否正确

## License

MIT

