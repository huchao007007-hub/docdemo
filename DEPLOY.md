# Docker部署指南 - 腾讯云Ubuntu 24.04

## 前置要求

- Ubuntu 24.04 LTS 服务器
- 已安装 Docker 和 Docker Compose
- 服务器开放端口：80（前端）、8000（后端API，可选）、3306（MySQL，可选）

## 一、服务器准备

### 1. 安装Docker和Docker Compose

```bash
# 更新系统
sudo apt-get update
sudo apt-get upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 配置防火墙（如果需要）

```bash
# 开放端口
sudo ufw allow 80/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

## 二、上传项目文件

### 方法1：使用Git（推荐）

```bash
# 在服务器上克隆项目
cd /opt
sudo git clone <your-repo-url> docdemo
cd docdemo
```

### 方法2：使用SCP上传

```bash
# 在本地机器执行
scp -r docdemo root@your-server-ip:/opt/
```

## 三、配置环境变量

```bash
cd /opt/docdemo

# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

编辑 `.env` 文件，设置以下内容：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-e79c5ddba7324e58bbffa901ea368756
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 数据库配置（重要：修改密码！）
MYSQL_ROOT_PASSWORD=your_strong_root_password
MYSQL_DATABASE=pdf_summary
MYSQL_USER=pdfuser
MYSQL_PASSWORD=your_strong_password

# 文件存储配置
MAX_FILE_SIZE=10485760
```

**重要**：请修改数据库密码为强密码！

## 四、构建和启动服务

```bash
cd /opt/docdemo

# 构建镜像（首次运行）
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 五、验证部署

### 1. 检查服务状态

```bash
# 查看所有容器
docker-compose ps

# 应该看到三个服务都在运行：
# - pdf_summary_mysql
# - pdf_summary_backend
# - pdf_summary_frontend
```

### 2. 检查服务健康

```bash
# 检查后端健康
curl http://localhost:8000/health

# 检查前端
curl http://localhost

# 检查MySQL
docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"
```

### 3. 访问应用

- 前端：`http://your-server-ip`
- 后端API文档：`http://your-server-ip:8000/docs`

## 六、常用管理命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
```

### 停止服务

```bash
# 停止所有服务
docker-compose stop

# 停止并删除容器（数据会保留）
docker-compose down

# 停止并删除容器和卷（会删除数据库数据！）
docker-compose down -v
```

### 更新代码

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build

# 3. 重启服务
docker-compose up -d
```

### 备份数据库

```bash
# 创建备份
docker-compose exec mysql mysqldump -u root -p pdf_summary > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复备份
docker-compose exec -T mysql mysql -u root -p pdf_summary < backup_file.sql
```

## 七、生产环境优化

### 1. 使用Nginx反向代理（推荐）

创建 `nginx/docker-compose.yml`：

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
    networks:
      - pdf_network
```

### 2. 配置HTTPS（使用Let's Encrypt）

```bash
# 安装Certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com
```

### 3. 设置自动备份

创建 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
docker-compose exec -T mysql mysqldump -u root -p${MYSQL_ROOT_PASSWORD} pdf_summary > $BACKUP_DIR/db_$DATE.sql

# 备份上传的文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/docdemo/backend/uploads

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

添加到crontab：

```bash
# 每天凌晨2点备份
0 2 * * * /opt/docdemo/backup.sh
```

## 八、故障排查

### 查看容器日志

```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mysql
```

### 进入容器调试

```bash
# 进入后端容器
docker-compose exec backend bash

# 进入MySQL容器
docker-compose exec mysql bash

# 进入前端容器
docker-compose exec frontend sh
```

### 检查网络连接

```bash
# 测试后端连接
docker-compose exec backend curl http://mysql:3306

# 测试前端连接
docker-compose exec frontend wget http://backend:8000/health
```

### 重置数据库

```bash
# 停止服务
docker-compose down

# 删除数据库卷
docker volume rm docdemo_mysql_data

# 重新启动
docker-compose up -d
```

## 九、性能优化

### 1. 限制资源使用

在 `docker-compose.yml` 中添加：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### 2. 使用Redis缓存（可选）

添加Redis服务到 `docker-compose.yml`：

```yaml
  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data
    networks:
      - pdf_network
```

## 十、安全建议

1. **修改默认密码**：确保数据库密码足够强
2. **使用HTTPS**：配置SSL证书
3. **限制端口访问**：只开放必要的端口
4. **定期更新**：保持Docker镜像和系统更新
5. **备份数据**：设置自动备份
6. **监控日志**：定期检查日志文件

## 快速部署命令总结

```bash
# 1. 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 2. 上传项目（使用Git或SCP）
cd /opt && git clone <your-repo> docdemo

# 3. 配置环境变量
cd docdemo
cp .env.example .env
nano .env  # 编辑配置

# 4. 启动服务
docker-compose up -d

# 5. 查看状态
docker-compose ps
docker-compose logs -f
```

## 访问应用

部署成功后：
- 前端：`http://your-server-ip`
- API文档：`http://your-server-ip:8000/docs`

首次访问需要注册用户账号。

