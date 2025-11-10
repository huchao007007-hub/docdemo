#!/bin/bash

# Docker部署脚本
# 用于快速部署到Ubuntu服务器

set -e

echo "=========================================="
echo "PDF总结小程序 - Docker部署脚本"
echo "=========================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "Docker未安装，开始安装..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "Docker安装完成"
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose未安装，开始安装..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose安装完成"
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo "未找到.env文件，从模板创建..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "已创建.env文件，请编辑配置："
        echo "  nano .env"
        echo ""
        echo "重要：请修改数据库密码！"
        exit 1
    else
        echo "错误：未找到.env.example文件"
        exit 1
    fi
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p backend/uploads
mkdir -p mysql

# 构建镜像
echo "构建Docker镜像..."
docker-compose build

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "=========================================="
echo "服务状态："
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  前端: http://$(hostname -I | awk '{print $1}')"
echo "  API文档: http://$(hostname -I | awk '{print $1}'):8000/docs"
echo ""
echo "查看日志："
echo "  docker-compose logs -f"
echo ""
echo "停止服务："
echo "  docker-compose down"
echo ""

