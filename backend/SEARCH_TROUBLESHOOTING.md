# 搜索功能问题排查指南

## 问题：查询不到结果

### 可能原因和解决方案

#### 1. 模型未成功加载（最常见）

**症状**：
- 日志显示 "无法生成查询向量"
- 日志显示 "本地embedding模型加载失败"

**原因**：
- 网络无法访问 huggingface.co，模型下载失败

**解决方案**：

**方案A：使用镜像源（推荐）**

在 `backend/.env` 文件中添加：
```env
HF_ENDPOINT=https://hf-mirror.com
```

然后重启后端服务。

**方案B：使用代理/VPN**

确保网络可以访问 huggingface.co

**方案C：手动下载模型**

```bash
# 设置镜像源
export HF_ENDPOINT=https://hf-mirror.com

# 手动下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

#### 2. Qdrant集合为空

**症状**：
- 日志显示 "Qdrant集合为空，没有可搜索的数据"

**原因**：
- 没有上传PDF文件
- PDF文件上传时向量生成失败
- 向量没有成功存储到Qdrant

**解决方案**：

1. **检查是否有上传的PDF文件**：
   - 查看文件列表，确认有已上传的PDF

2. **重新上传PDF文件**：
   - 删除旧文件，重新上传
   - 查看日志确认向量生成成功

3. **检查向量生成日志**：
   - 查看上传时的日志，确认看到 "PDF向量生成成功"
   - 如果看到 "无法生成向量" 或 "插入文档向量失败"，说明向量生成/存储失败

#### 3. 相似度阈值太高

**症状**：
- 日志显示 "所有结果都被阈值过滤掉了"
- 日志显示 "最高相似度: 0.xx"（低于阈值）

**原因**：
- 相似度阈值设置为 0.5，但实际匹配度较低

**解决方案**：

1. **降低相似度阈值**：
   - 修改 `frontend/src/views/Home.vue` 第406行
   - 将 `0.5` 改为 `0.3` 或 `0.4`

2. **使用更相关的查询词**：
   - 使用文档中实际存在的关键词
   - 避免使用过于宽泛的查询

#### 4. 用户ID过滤问题

**症状**：
- Qdrant中有数据，但搜索不到结果

**原因**：
- 向量存储时使用的 user_id 与搜索时不一致

**解决方案**：

1. **检查用户登录状态**：
   - 确认已正确登录
   - 确认使用的是正确的用户账号

2. **检查向量存储**：
   - 查看上传时的日志，确认 user_id 正确

#### 5. 向量维度不匹配

**症状**：
- 日志显示向量生成成功，但搜索失败
- 错误信息包含 "dimension" 或 "vector size"

**原因**：
- Qdrant集合配置的维度与生成的向量维度不一致

**解决方案**：

1. **检查配置**：
   - 确认 `EMBEDDING_DIMENSION` 配置正确
   - sentence-transformers 默认是 384 维

2. **重建集合**：
   ```python
   # 删除旧集合，重新创建
   # 集合会在首次使用时自动创建
   ```

## 诊断步骤

### 步骤1：检查模型加载

查看日志，确认看到：
```
INFO:services.vector_service:本地embedding模型加载成功
```

如果没有，按照上面的方案1解决。

### 步骤2：检查向量生成

上传PDF时，查看日志确认：
```
INFO:services.vector_service:文档向量已添加: PDF ID=xx, 块数=xx
```

如果没有，检查：
- 模型是否加载成功
- 文本内容是否提取成功
- Qdrant连接是否正常

### 步骤3：检查Qdrant数据

搜索时，查看日志确认：
```
INFO:services.vector_service:Qdrant集合 'pdf_summary_vectors' 中共有 xx 个向量点
```

如果为0，说明没有数据，需要重新上传PDF。

### 步骤4：检查搜索过程

搜索时，查看日志：
```
INFO:services.vector_service:开始生成查询向量: '查询词'
INFO:services.vector_service:查询向量生成成功，维度: 384
INFO:services.vector_service:Qdrant返回 xx 个原始结果
INFO:services.vector_service:经过阈值 0.5 过滤后，剩余 xx 个结果
```

根据日志信息判断问题所在。

## 快速诊断命令

### 检查模型是否加载

```python
# 在Python中测试
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
embedding = model.encode("测试文本")
print(f"向量维度: {len(embedding)}")
```

### 检查Qdrant连接和数据

```python
from qdrant_client import QdrantClient
client = QdrantClient(host="118.89.121.9", port=6333)
collection = client.get_collection("pdf_summary_vectors")
print(f"向量点数量: {collection.points_count}")
```

## 常见错误信息

### "无法生成查询向量"
- **原因**：模型未加载
- **解决**：配置镜像源或使用代理

### "Qdrant集合为空"
- **原因**：没有向量数据
- **解决**：重新上传PDF文件

### "所有结果都被阈值过滤掉了"
- **原因**：相似度阈值太高
- **解决**：降低阈值或使用更相关的查询词

### "Qdrant搜索操作失败"
- **原因**：Qdrant服务问题
- **解决**：检查Qdrant服务是否运行

## 验证修复

修复后，搜索时应该看到：

1. **模型加载成功**：
   ```
   INFO:services.vector_service:本地embedding模型加载成功
   ```

2. **向量生成成功**：
   ```
   INFO:services.vector_service:查询向量生成成功，维度: 384
   ```

3. **有搜索结果**：
   ```
   INFO:services.vector_service:经过阈值 0.5 过滤后，剩余 X 个结果
   INFO:services.vector_service:搜索完成: 查询='xxx', 结果数=X
   ```

## 注意事项

1. **首次使用**：模型需要下载，可能需要一些时间
2. **网络问题**：如果无法访问 huggingface.co，必须使用镜像源
3. **已上传的文件**：如果模型加载失败，已上传的文件可能没有向量，需要重新上传
4. **相似度阈值**：可以根据实际情况调整，建议范围 0.3-0.6

