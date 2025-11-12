# Qdrant 连接问题排查指南

## 常见错误：timed out

### 问题现象
- 上传PDF时：`ERROR:services.vector_service:添加文档向量失败: timed out`
- 搜索时：`ERROR:services.vector_service:搜索失败: timed out`

### 可能原因

1. **Qdrant服务未运行**
2. **Qdrant地址配置错误**
3. **网络连接问题**
4. **Qdrant服务响应慢**

## 排查步骤

### 1. 检查Qdrant服务是否运行

```bash
# 在服务器上检查
docker ps | grep qdrant

# 或者
curl http://localhost:6333/health
```

**应该返回**：
```json
{"title":"qdrant - vector search engine","version":"x.x.x"}
```

### 2. 检查Qdrant配置

查看 `.env` 文件中的配置：

```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

**如果Qdrant在其他服务器**：
```env
QDRANT_HOST=your-qdrant-server-ip
QDRANT_PORT=6333
```

### 3. 测试连接

在Python中测试：

```python
from qdrant_client import QdrantClient

try:
    client = QdrantClient(host="localhost", port=6333, timeout=10)
    collections = client.get_collections()
    print("连接成功！")
    print(f"集合列表: {collections}")
except Exception as e:
    print(f"连接失败: {str(e)}")
```

### 4. 检查网络

```bash
# 测试端口是否开放
telnet localhost 6333

# 或使用nc
nc -zv localhost 6333
```

### 5. 查看Qdrant日志

```bash
# 如果Qdrant在Docker中
docker logs qdrant

# 或查看容器名称
docker logs panda-wiki-qdrant
```

## 解决方案

### 方案1：确保Qdrant服务运行

```bash
# 检查Qdrant容器
docker ps -a | grep qdrant

# 如果容器停止了，启动它
docker start panda-wiki-qdrant

# 查看日志
docker logs -f panda-wiki-qdrant
```

### 方案2：检查防火墙

```bash
# Ubuntu防火墙
sudo ufw status
sudo ufw allow 6333/tcp

# 或检查iptables
sudo iptables -L -n | grep 6333
```

### 方案3：增加超时时间

在 `.env` 文件中：

```env
QDRANT_TIMEOUT=60  # 增加到60秒
```

### 方案4：使用正确的Qdrant地址

如果Qdrant在Docker网络中，可能需要使用容器名：

```env
# 如果后端也在Docker中
QDRANT_HOST=panda-wiki-qdrant  # 使用容器名

# 如果在同一服务器但不同容器
QDRANT_HOST=localhost  # 或服务器IP
```

### 方案5：临时禁用向量搜索

如果暂时不需要搜索功能，可以：

1. 注释掉向量服务初始化（在 `main.py` 中）
2. 或设置环境变量禁用

## 验证修复

修复后，查看日志应该看到：

```
INFO:services.vector_service:Qdrant客户端连接成功: localhost:6333
INFO:services.vector_service:Qdrant集合已存在: pdf_summary_vectors
```

而不是：
```
ERROR:services.vector_service:添加文档向量失败: timed out
```

## 快速诊断命令

```bash
# 1. 检查Qdrant是否运行
docker ps | grep qdrant

# 2. 测试HTTP连接
curl http://localhost:6333/health

# 3. 测试Python连接
python -c "from qdrant_client import QdrantClient; c=QdrantClient('localhost', 6333); print(c.get_collections())"

# 4. 查看后端日志
# 应该看到 "Qdrant客户端连接成功"
```

## 注意事项

- Qdrant服务必须运行才能使用语义搜索
- 如果Qdrant不可用，其他功能（上传、总结）仍然正常
- 向量生成和存储是异步的，不会阻塞文件上传

