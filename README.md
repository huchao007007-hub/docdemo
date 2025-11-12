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
- Qdrant (向量数据库，用于语义搜索)
- sentence-transformers (向量生成)
- pytesseract (OCR识别，可选)

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
│   │   ├── ai_service.py    # AI总结服务
│   │   ├── auth_service.py  # 认证服务
│   │   └── vector_service.py # 向量搜索服务
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
- Qdrant (向量数据库，用于语义搜索)
  - 可以通过Docker运行：`docker run -p 6333:6333 qdrant/qdrant`
  - 或使用远程Qdrant服务

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
- `QDRANT_HOST`: Qdrant服务地址（默认：118.89.121.9）
- `QDRANT_PORT`: Qdrant服务端口（默认：6333）
- `HF_ENDPOINT`: HuggingFace镜像源（如果无法访问huggingface.co，推荐：https://hf-mirror.com）

详细配置说明请参考 `backend/ENV_SETUP.md`

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
- ✅ OCR识别（支持扫描版PDF）
- ✅ AI智能总结（基于DeepSeek）
- ✅ 语义搜索（基于向量数据库）
- ✅ 用户登录/注册
- ✅ 文件列表管理
- ✅ 总结结果展示（Markdown转HTML）
- ✅ 在线PDF查看
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

### 语义搜索
```
GET /api/search?q=搜索关键词&limit=10&score_threshold=0.5
```

### 用户认证
```
POST /api/auth/register    # 注册
POST /api/auth/login       # 登录
GET  /api/auth/me          # 获取当前用户信息
```

### 查看PDF文件
```
GET /api/files/{file_id}/view?token=JWT_TOKEN
```

## 注意事项

1. **API密钥安全**: `.env` 文件包含敏感信息，不要提交到Git仓库
2. **文件大小限制**: 默认最大10MB，可在配置中修改
3. **数据库**: 确保MySQL服务已启动
4. **DeepSeek API**: 需要有效的API密钥才能使用AI总结功能
5. **Qdrant服务**: 确保Qdrant服务运行，用于语义搜索功能
6. **HuggingFace镜像**: 如果无法访问huggingface.co，需要在`.env`中配置`HF_ENDPOINT`
7. **OCR功能**: 扫描版PDF需要安装Tesseract和Poppler（可选）

## 开发说明

### 后端开发

- 使用FastAPI框架，支持自动API文档
- 访问 `http://localhost:8000/docs` 查看Swagger文档
- 数据库模型使用SQLAlchemy ORM
- 向量搜索使用Qdrant向量数据库
- 支持JWT认证

### 前端开发

- 使用Vue 3 Composition API
- Element Plus组件库
- Vite作为构建工具
- 支持Markdown渲染
- 支持语义搜索和高亮显示

## 语义搜索功能

### 功能说明

基于向量数据库的语义搜索，可以搜索PDF文件的内容和文件名。

### 技术架构

- **向量生成**: sentence-transformers（本地模型）
- **向量存储**: Qdrant 向量数据库
- **搜索算法**: 余弦相似度搜索

### 配置要求

1. **Qdrant服务**：确保Qdrant服务运行
2. **模型下载**：首次使用需要下载embedding模型（约400MB）
3. **镜像源**：如果无法访问huggingface.co，配置`HF_ENDPOINT=https://hf-mirror.com`

### 使用方法

1. 上传PDF文件（会自动生成向量）
2. 在搜索框输入关键词
3. 查看搜索结果（显示相似度和匹配内容）

详细说明请参考：
- `backend/SEMANTIC_SEARCH.md` - 语义搜索功能说明
- `backend/SEARCH_TROUBLESHOOTING.md` - 搜索问题排查指南

## 相关文档

- `backend/ENV_SETUP.md` - 环境变量配置说明
- `backend/OCR_SETUP.md` - OCR功能安装指南
- `backend/FIX_OCR.md` - OCR问题排查
- `backend/SEMANTIC_SEARCH.md` - 语义搜索功能说明
- `backend/SEARCH_TROUBLESHOOTING.md` - 搜索问题排查指南
- `backend/DATABASE_MIGRATION.md` - 数据库迁移说明
- `DEPLOY.md` - Docker部署指南

## 常见问题

### Q: 上传PDF后无法提取文本？
A: 
- 普通PDF：检查pdfplumber是否正确安装
- 扫描版PDF：需要安装OCR工具（Tesseract和Poppler），参考 `backend/OCR_SETUP.md`

### Q: AI总结失败？
A: 检查DeepSeek API密钥是否正确，以及网络连接是否正常

### Q: 数据库连接失败？
A: 检查MySQL服务是否启动，以及数据库连接字符串是否正确

### Q: 搜索功能查询不到结果？
A: 可能的原因：
1. **模型未加载**：网络无法访问huggingface.co，需要在`.env`中配置`HF_ENDPOINT=https://hf-mirror.com`
2. **Qdrant集合为空**：需要重新上传PDF文件生成向量
3. **相似度阈值过高**：可以降低搜索阈值（默认0.5）
4. **Qdrant服务未运行**：检查Qdrant服务是否正常

详细排查步骤请参考 `backend/SEARCH_TROUBLESHOOTING.md`

### Q: 模型下载失败？
A: 
- 配置HuggingFace镜像源：在`.env`中添加`HF_ENDPOINT=https://hf-mirror.com`
- 或使用代理/VPN访问huggingface.co

### Q: OCR识别失败？
A: 
- 检查Tesseract和Poppler是否正确安装
- 如果不在PATH中，需要在`.env`中配置路径
- 参考 `backend/OCR_SETUP.md` 和 `backend/FIX_OCR.md`

## License

MIT

