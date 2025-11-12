# 模型切换指南

## 当前使用的模型

**模型名称**：`shibing624/text2vec-base-chinese`

**特点**：
- 专门针对中文优化
- 向量维度：768
- 中文语义理解效果更好
- 适合中文文档搜索

## 重要提示：更换模型后的操作

⚠️ **更换模型后，向量维度会变化，必须执行以下操作**：

### 1. 删除旧的 Qdrant 集合

由于向量维度不匹配，需要删除旧的集合：

```python
# 方法1：通过代码删除
from qdrant_client import QdrantClient
client = QdrantClient(host="118.89.121.9", port=6333)
client.delete_collection("pdf_summary_vectors")
```

或者通过 Qdrant 的 Web UI：
- 访问 `http://118.89.121.9:6333/dashboard`
- 找到 `pdf_summary_vectors` 集合
- 点击删除

### 2. 更新配置

确保 `.env` 文件中的维度配置正确：

```env
EMBEDDING_MODEL=shibing624/text2vec-base-chinese
EMBEDDING_DIMENSION=768
```

### 3. 重新上传 PDF 文件

删除旧文件，重新上传所有 PDF 文件，让新模型生成向量。

## 可用的模型选项

### 选项1：text2vec-base-chinese（当前，推荐）

```env
EMBEDDING_MODEL=shibing624/text2vec-base-chinese
EMBEDDING_DIMENSION=768
```

**优点**：
- 专门针对中文优化
- 中文语义理解效果好
- 搜索准确性高

**缺点**：
- 仅支持中文
- 向量维度较高（768）

### 选项2：paraphrase-multilingual-MiniLM-L12-v2

```env
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384
```

**优点**：
- 支持多语言
- 模型较小，速度快
- 内存占用低

**缺点**：
- 中文效果一般
- 搜索准确性较低

### 选项3：BGE 中文模型（推荐，效果最好）

需要安装额外依赖：
```bash
pip install FlagEmbedding
```

```env
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5
EMBEDDING_DIMENSION=768
```

**优点**：
- 中文效果最好
- 在中文语义搜索任务上表现优异

**缺点**：
- 需要安装额外库
- 模型较大

### 选项4：m3e-base（轻量级中文模型）

```env
EMBEDDING_MODEL=moka-ai/m3e-base
EMBEDDING_DIMENSION=768
```

**优点**：
- 轻量级，速度快
- 中文效果较好
- 资源占用低

**缺点**：
- 效果略低于 text2vec-base-chinese

## 模型对比

| 模型 | 维度 | 中文效果 | 多语言 | 速度 | 推荐度 |
|------|------|---------|--------|------|--------|
| text2vec-base-chinese | 768 | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| BGE-base-zh-v1.5 | 768 | ⭐⭐⭐⭐⭐ | ❌ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| m3e-base | 768 | ⭐⭐⭐⭐ | ❌ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| paraphrase-multilingual-MiniLM-L12-v2 | 384 | ⭐⭐ | ✅ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

## 切换模型步骤

1. **停止后端服务**

2. **更新配置**
   - 修改 `.env` 文件中的 `EMBEDDING_MODEL` 和 `EMBEDDING_DIMENSION`

3. **删除旧集合**（重要！）
   ```python
   from qdrant_client import QdrantClient
   client = QdrantClient(host="118.89.121.9", port=6333)
   client.delete_collection("pdf_summary_vectors")
   ```

4. **重启后端服务**

5. **重新上传 PDF 文件**

## 验证模型切换

查看日志确认：

```
INFO:services.vector_service:加载embedding模型: shibing624/text2vec-base-chinese
INFO:services.vector_service:本地embedding模型加载成功: shibing624/text2vec-base-chinese
INFO:services.vector_service:使用本地embedding模型生成向量成功，维度: 768
```

## 性能优化建议

1. **首次使用**：模型需要下载，可能需要一些时间
2. **内存占用**：768维模型比384维占用更多内存，但效果更好
3. **搜索速度**：维度增加会略微影响搜索速度，但影响不大
4. **准确性提升**：使用中文优化模型后，搜索准确性会明显提升

