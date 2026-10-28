#!/bin/bash
# 部署 API 文档到服务器

set -e

echo "🚀 部署 Nautilus API 文档..."

# 服务器配置
SERVER="ubuntu@115.159.62.192"
BACKEND_DIR="/home/ubuntu/nautilus-mvp/phase3/backend"
DOCS_DIR="/home/ubuntu/nautilus-mvp/phase3/docs"

# 1. 上传文档文件
echo "📤 上传文档文件..."
scp -r docs/* $SERVER:$DOCS_DIR/

# 2. 上传更新的 API 文件
echo "📤 上传 API 文件..."
scp backend/main.py $SERVER:$BACKEND_DIR/
scp backend/api/tasks.py $SERVER:$BACKEND_DIR/api/
scp backend/api/agents.py $SERVER:$BACKEND_DIR/api/
scp backend/api/auth.py $SERVER:$BACKEND_DIR/api/

# 3. 上传 OpenAPI 生成脚本
echo "📤 上传 OpenAPI 生成脚本..."
ssh $SERVER "mkdir -p $BACKEND_DIR/scripts"
scp backend/scripts/generate_openapi.py $SERVER:$BACKEND_DIR/scripts/

# 4. 在服务器上生成 OpenAPI schema
echo "🔧 生成 OpenAPI schema..."
ssh $SERVER << 'EOF'
cd /home/ubuntu/nautilus-mvp/phase3/backend

# 激活虚拟环境
source venv/bin/activate

# 生成 OpenAPI schema
python scripts/generate_openapi.py

# 确保文档目录权限正确
chmod -R 755 ../docs

echo "✅ OpenAPI schema 生成完成"
EOF

# 5. 配置 Nginx 提供文档访问
echo "🔧 配置 Nginx..."
ssh $SERVER << 'EOF'
# 创建 Nginx 配置
sudo tee /etc/nginx/sites-available/nautilus-docs > /dev/null << 'NGINX_CONFIG'
server {
    listen 80;
    server_name docs.nautilus.social;

    root /home/ubuntu/nautilus-mvp/phase3/docs;
    index api-playground.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location /openapi.json {
        alias /home/ubuntu/nautilus-mvp/phase3/docs/openapi.json;
        add_header Content-Type application/json;
        add_header Access-Control-Allow-Origin *;
    }

    # 代理 API 请求到后端
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_CONFIG

# 启用站点
sudo ln -sf /etc/nginx/sites-available/nautilus-docs /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx

echo "✅ Nginx 配置完成"
EOF

# 6. 重启后端服务
echo "🔄 重启后端服务..."
ssh $SERVER << 'EOF'
cd /home/ubuntu/nautilus-mvp/phase3/backend
sudo systemctl restart nautilus-backend
echo "✅ 后端服务已重启"
EOF

# 7. 验证部署
echo "🔍 验证部署..."
sleep 3

# 检查 API 文档是否可访问
if curl -s http://115.159.62.192/docs | grep -q "Nautilus"; then
    echo "✅ API 文档部署成功: http://115.159.62.192/docs"
else
    echo "⚠️  API 文档可能未正确部署，请检查"
fi

# 检查 OpenAPI schema
if curl -s http://115.159.62.192/openapi.json | grep -q "openapi"; then
    echo "✅ OpenAPI schema 可访问: http://115.159.62.192/openapi.json"
else
    echo "⚠️  OpenAPI schema 可能未正确生成，请检查"
fi

echo ""
echo "🎉 API 文档部署完成！"
echo ""
echo "📚 访问地址:"
echo "  - 交互式文档: http://115.159.62.192/docs"
echo "  - ReDoc 文档: http://115.159.62.192/redoc"
echo "  - OpenAPI Schema: http://115.159.62.192/openapi.json"
echo "  - API Playground: http://115.159.62.192/api-playground.html"
echo ""
