# 快速部署指南

## 一键部署（推荐）

```bash
# 1. 上传项目到服务器
cd /opt
git clone <your-repo> docdemo
cd docdemo

# 2. 配置环境变量
cp .env.example .env
nano .env  # 编辑配置，设置数据库密码和API密钥

# 3. 运行部署脚本
chmod +x deploy.sh
./deploy.sh
```

## 手动部署

### 1. 安装Docker和Docker Compose

```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. 配置环境变量

```bash
cd /opt/docdemo
cp .env.example .env
nano .env
```

**必须修改**：
- `MYSQL_ROOT_PASSWORD` - MySQL root密码
- `MYSQL_PASSWORD` - 应用数据库密码
- `DEEPSEEK_API_KEY` - DeepSeek API密钥

### 3. 启动服务

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 测试后端
curl http://localhost:8000/health

# 测试前端
curl http://localhost
```

## 访问应用

- **前端**: `http://your-server-ip`
- **API文档**: `http://your-server-ip:8000/docs`

## 常用命令

```bash
# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新代码后重新部署
git pull
docker-compose build
docker-compose up -d
```

## 详细文档

查看 `DEPLOY.md` 获取完整的部署说明。

