# 快速部署命令（腾讯云Ubuntu 24.04）

## 一、服务器准备（首次部署）

```bash
# 1. 更新系统
sudo apt-get update && sudo apt-get upgrade -y

# 2. 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl start docker
sudo systemctl enable docker

# 3. 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 验证安装
docker --version
docker-compose --version
```

## 二、上传项目

```bash
# 方法1：使用Git（推荐）
cd /opt
sudo git clone <your-repo-url> docdemo
cd docdemo

# 方法2：使用SCP（在本地执行）
# scp -r docdemo root@your-server-ip:/opt/
```

## 三、配置环境变量

```bash
cd /opt/docdemo

# 创建.env文件
cat > .env << 'EOF'
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-e79c5ddba7324e58bbffa901ea368756
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 数据库配置（重要：修改密码！）
MYSQL_ROOT_PASSWORD=YourStrongRootPassword123!
MYSQL_DATABASE=pdf_summary
MYSQL_USER=pdfuser
MYSQL_PASSWORD=YourStrongPassword123!

# 文件存储配置
MAX_FILE_SIZE=10485760
EOF

# 编辑.env文件（修改密码）
nano .env
```

## 四、部署

```bash
# 创建必要目录
mkdir -p backend/uploads mysql

# 构建并启动（首次运行）
docker-compose build
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 五、验证

```bash
# 查看服务状态
docker-compose ps

# 测试后端
curl http://localhost:8000/health

# 测试前端
curl http://localhost
```

## 六、访问应用

- **前端**: `http://your-server-ip`
- **API文档**: `http://your-server-ip:8000/docs`

## 常用命令

```bash
# 查看日志
docker-compose logs -f [service_name]

# 重启服务
docker-compose restart [service_name]

# 停止服务
docker-compose stop

# 停止并删除容器
docker-compose down

# 更新代码后重新部署
git pull
docker-compose build
docker-compose up -d
```

## 一键部署脚本

```bash
chmod +x deploy.sh
./deploy.sh
```

## 注意事项

1. **修改数据库密码**：`.env`文件中的密码必须修改为强密码
2. **开放端口**：确保服务器防火墙开放80和8000端口
3. **首次访问**：需要注册用户账号
4. **数据备份**：定期备份数据库和上传的文件

