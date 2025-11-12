# Embedding 向量生成配置说明

## 问题说明

DeepSeek API 目前可能不支持标准的 `embeddings` 接口。本实现提供了两种方案：

### 方案1：使用 DeepSeek（当前实现）

代码会尝试：
1. 首先尝试使用标准的 `embeddings` 接口
2. 如果失败，尝试使用 `chat` 模型生成向量（可能不稳定）

### 方案2：使用其他 Embedding 服务（推荐）

如果 DeepSeek 不支持 embeddings，建议使用以下服务之一：

#### 选项A：使用 OpenAI Embeddings（推荐）

1. 在 `.env` 文件中添加：
```env
OPENAI_API_KEY=your_openai_api_key
USE_OPENAI_EMBEDDINGS=true
```

2. 修改 `vector_service.py` 中的 `_generate_embedding` 方法：
```python
def _generate_embedding(self, text: str) -> Optional[List[float]]:
    if Config.USE_OPENAI_EMBEDDINGS:
        from openai import OpenAI
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    # ... 其他代码
```

#### 选项B：使用本地 Sentence Transformers

1. 安装依赖：
```bash
pip install sentence-transformers
```

2. 修改 `vector_service.py`：
```python
from sentence_transformers import SentenceTransformer

class VectorService:
    def __init__(self):
        # ... 其他初始化代码
        self.local_embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')  # 支持中文
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        try:
            embedding = self.local_embedder.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"本地embedding生成失败: {str(e)}")
            return None
```

#### 选项C：使用其他 Embedding 服务

- **智谱AI**: 提供中文优化的 embeddings
- **百度文心**: 提供中文 embeddings
- **阿里云**: 提供 embeddings 服务

## 当前实现说明

当前代码会：
1. 尝试使用 DeepSeek 的 embeddings 接口（如果支持）
2. 如果失败，尝试使用 chat 模型（可能不稳定）
3. 如果都失败，记录警告但不影响其他功能

## 验证 Embedding 是否工作

查看日志：
```bash
# 上传PDF后，查看日志
docker-compose logs backend | grep "向量"

# 应该看到：
# "生成向量成功" 或 "无法生成向量"
```

## 推荐配置

对于生产环境，建议：
1. 使用 OpenAI 的 `text-embedding-3-small`（成本低，效果好）
2. 或使用本地的 `sentence-transformers`（免费，但需要服务器资源）

## 向量维度

- OpenAI text-embedding-3-small: 1536 维
- sentence-transformers: 通常 384 或 768 维（需要修改 `EMBEDDING_DIMENSION`）

如果使用不同的 embedding 服务，记得修改 `config.py` 中的 `EMBEDDING_DIMENSION`。

