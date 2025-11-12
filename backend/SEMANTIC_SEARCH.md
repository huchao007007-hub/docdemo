# 语义搜索功能说明

## 功能概述

实现了基于向量数据库的语义搜索功能，可以搜索PDF文件的内容和文件名。

## 技术架构

- **向量生成**: sentence-transformers（本地）或 DeepSeek Embeddings API
- **向量存储**: Qdrant 向量数据库
- **搜索算法**: 余弦相似度搜索

## 安装和配置

### 1. 安装依赖

```bash
pip install qdrant-client sentence-transformers
```

### 2. 配置 Qdrant

确保 Qdrant 服务运行在 `localhost:6333`（或配置其他地址）

在 `.env` 文件中配置：

```env
# Qdrant配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=pdf_summary_vectors

# 向量配置
EMBEDDING_DIMENSION=384  # sentence-transformers默认384维
TEXT_CHUNK_SIZE=1000    # 文本分块大小
TEXT_CHUNK_OVERLAP=200  # 分块重叠大小
```

### 3. 验证配置

启动后端服务后，查看日志确认：
- Qdrant连接成功
- 向量服务初始化成功

## 使用说明

### API接口

#### 语义搜索

```
GET /api/search?q=搜索关键词&limit=10&score_threshold=0.5
```

**参数**:
- `q` (必需): 搜索查询文本
- `limit` (可选): 返回结果数量，默认10
- `score_threshold` (可选): 相似度阈值（0-1），默认0.5

**响应示例**:
```json
{
  "success": true,
  "data": {
    "query": "搜索关键词",
    "results": [
      {
        "id": 1,
        "filename": "文档.pdf",
        "file_size": 1024000,
        "text_length": 5000,
        "has_text": true,
        "has_summary": true,
        "created_at": "2024-01-01T00:00:00",
        "match_type": "content",
        "match_text": "匹配的文本片段...",
        "similarity_score": 0.85
      }
    ],
    "total": 1
  }
}
```

## 工作流程

### 1. 上传PDF时

1. 提取PDF文本内容
2. 将文本分块（长文本需要分块）
3. 为每个文本块生成向量
4. 为文件名生成向量
5. 存储所有向量到Qdrant

### 2. 搜索时

1. 将查询文本转换为向量
2. 在Qdrant中搜索相似向量
3. 过滤只返回当前用户的文档
4. 按相似度排序
5. 返回匹配的文档信息

## 向量生成方案

### 方案1：本地 sentence-transformers（推荐）

**优点**:
- 免费，无需API调用
- 速度快
- 支持中文

**缺点**:
- 需要下载模型（首次运行）
- 占用一定内存

**模型**: `paraphrase-multilingual-MiniLM-L12-v2`（支持中文和英文）

### 方案2：DeepSeek Embeddings API

**优点**:
- 无需本地资源
- 可能支持更好的中文理解

**缺点**:
- 需要API调用（可能有成本）
- DeepSeek可能不支持标准embeddings接口

### 方案3：OpenAI Embeddings

如果需要使用OpenAI的embeddings，修改 `vector_service.py`：

```python
# 在 _generate_embedding 方法中添加
if Config.USE_OPENAI_EMBEDDINGS:
    from openai import OpenAI
    client = OpenAI(api_key=Config.OPENAI_API_KEY)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding
```

## 性能优化

### 文本分块

长文本会被分块处理：
- 每块大小：1000字符（可配置）
- 重叠：200字符（可配置）

这样可以：
- 提高搜索精度
- 支持长文档
- 减少单个向量的大小

### 索引优化

Qdrant会自动为向量创建索引，支持快速相似度搜索。

## 故障排查

### 问题1：向量生成失败

**检查**:
1. 查看日志中的错误信息
2. 确认sentence-transformers已安装
3. 确认模型下载成功

**解决**:
```bash
# 手动下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

### 问题2：Qdrant连接失败

**检查**:
1. Qdrant服务是否运行
2. 端口是否正确（默认6333）
3. 防火墙是否开放

**解决**:
```bash
# 检查Qdrant状态
curl http://localhost:6333/health

# 查看Qdrant日志
docker logs qdrant
```

### 问题3：搜索结果为空

**可能原因**:
1. 向量维度不匹配
2. 相似度阈值太高
3. 文档还未生成向量

**解决**:
1. 检查 `EMBEDDING_DIMENSION` 配置
2. 降低 `score_threshold`
3. 重新上传文档以生成向量

## 注意事项

1. **向量维度**: 如果更换embedding模型，需要：
   - 修改 `EMBEDDING_DIMENSION` 配置
   - 删除旧的Qdrant集合
   - 重新上传文档生成向量

2. **数据隔离**: 每个用户只能搜索自己的文档（通过user_id过滤）

3. **性能**: 大量文档时，搜索速度仍然很快（Qdrant优化）

4. **存储**: 向量数据存储在Qdrant中，删除PDF时也会删除相关向量

