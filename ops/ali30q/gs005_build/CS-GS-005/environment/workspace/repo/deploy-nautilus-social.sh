#!/bin/bash
# Nautilus Social - 一键部署脚本
# Domain: nautilus.social
# Date: 2026-02-21

set -e  # Exit on error

echo "=========================================="
echo "Nautilus Social - 域名部署脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}错误: 请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 域名配置
DOMAIN="nautilus.social"
API_DOMAIN="api.nautilus.social"
WWW_DOMAIN="www.nautilus.social"

echo -e "${YELLOW}步骤 1/6: 检查DNS解析...${NC}"
echo "正在检查 $DOMAIN 的DNS解析..."
if host $DOMAIN > /dev/null 2>&1; then
    IP=$(host $DOMAIN | grep "has address" | awk '{print $4}' | head -1)
    echo -e "${GREEN}✓ DNS解析成功: $DOMAIN -> $IP${NC}"
else
    echo -e "${RED}✗ DNS解析失败${NC}"
    echo "请确保已配置以下DNS记录:"
    echo "  A    @      43.160.239.61"
    echo "  A    www    43.160.239.61"
    echo "  A    api    43.160.239.61"
    echo ""
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}步骤 2/6: 安装依赖...${NC}"
# 检查并安装 certbot
if ! command -v certbot &> /dev/null; then
    echo "安装 certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    echo -e "${GREEN}✓ certbot 安装完成${NC}"
else
    echo -e "${GREEN}✓ certbot 已安装${NC}"
fi

# 检查 nginx
if ! command -v nginx &> /dev/null; then
    echo "安装 nginx..."
    apt-get install -y nginx
    echo -e "${GREEN}✓ nginx 安装完成${NC}"
else
    echo -e "${GREEN}✓ nginx 已安装${NC}"
fi

echo ""
echo -e "${YELLOW}步骤 3/6: 创建 certbot 目录...${NC}"
mkdir -p /var/www/certbot
chown -R www-data:www-data /var/www/certbot
echo -e "${GREEN}✓ certbot 目录创建完成${NC}"

echo ""
echo -e "${YELLOW}步骤 4/6: 获取 SSL 证书...${NC}"
if [ -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo -e "${YELLOW}证书已存在，是否续期? (y/n)${NC}"
    read -p "" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        certbot renew --nginx
    fi
else
    echo "正在获取 SSL 证书..."
    certbot certonly --nginx \
        -d $DOMAIN \
        -d $WWW_DOMAIN \
        -d $API_DOMAIN \
        --non-interactive \
        --agree-tos \
        --email admin@$DOMAIN \
        --no-eff-email

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ SSL 证书获取成功${NC}"
    else
        echo -e "${RED}✗ SSL 证书获取失败${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}步骤 5/6: 配置 Nginx...${NC}"
# 复制配置文件
NGINX_CONF="/etc/nginx/sites-available/nautilus-social"
cp nginx-nautilus-social.conf $NGINX_CONF
echo -e "${GREEN}✓ 配置文件已复制${NC}"

# 创建软链接
if [ -L "/etc/nginx/sites-enabled/nautilus-social" ]; then
    rm /etc/nginx/sites-enabled/nautilus-social
fi
ln -s $NGINX_CONF /etc/nginx/sites-enabled/nautilus-social
echo -e "${GREEN}✓ 软链接已创建${NC}"

# 删除默认配置（如果存在）
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    rm /etc/nginx/sites-enabled/default
    echo -e "${GREEN}✓ 默认配置已删除${NC}"
fi

# 测试 Nginx 配置
echo "测试 Nginx 配置..."
if nginx -t; then
    echo -e "${GREEN}✓ Nginx 配置测试通过${NC}"
else
    echo -e "${RED}✗ Nginx 配置测试失败${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}步骤 6/6: 重启服务...${NC}"
# 重启 Nginx
systemctl reload nginx
echo -e "${GREEN}✓ Nginx 已重启${NC}"

# 检查服务状态
echo ""
echo "检查服务状态..."
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx 运行正常${NC}"
else
    echo -e "${RED}✗ Nginx 未运行${NC}"
    systemctl status nginx
    exit 1
fi

# 检查前端服务
if curl -s http://127.0.0.1:3000 > /dev/null; then
    echo -e "${GREEN}✓ 前端服务运行正常 (端口 3000)${NC}"
else
    echo -e "${YELLOW}⚠ 前端服务未运行，请手动启动:${NC}"
    echo "  cd /path/to/frontend && npm run dev"
fi

# 检查后端服务
if curl -s http://127.0.0.1:8000/docs > /dev/null; then
    echo -e "${GREEN}✓ 后端服务运行正常 (端口 8000)${NC}"
else
    echo -e "${YELLOW}⚠ 后端服务未运行，请手动启动:${NC}"
    echo "  cd /path/to/backend && uvicorn main:app --host 0.0.0.0 --port 8000"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  主站: https://$DOMAIN"
echo "  WWW:  https://$WWW_DOMAIN"
echo "  API:  https://$API_DOMAIN"
echo ""
echo "测试命令:"
echo "  curl -I https://$DOMAIN"
echo "  curl -I https://$API_DOMAIN"
echo ""
echo "日志位置:"
echo "  访问日志: /var/log/nginx/nautilus-social-access.log"
echo "  错误日志: /var/log/nginx/nautilus-social-error.log"
echo "  API访问:  /var/log/nginx/nautilus-social-api-access.log"
echo "  API错误:  /var/log/nginx/nautilus-social-api-error.log"
echo ""
echo -e "${GREEN}Nautilus Social · 智涌 - 智能如潮，螺旋向上！${NC}"
echo ""
