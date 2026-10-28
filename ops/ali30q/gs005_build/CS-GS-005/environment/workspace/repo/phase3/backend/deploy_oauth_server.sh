#!/bin/bash
# OAuth 服务部署脚本 - 在服务器上执行
set -e

echo "=========================================="
echo "Nautilus OAuth 服务部署"
echo "=========================================="

DEPLOY_DIR="$HOME/nautilus-oauth"
VENV_DIR="$DEPLOY_DIR/venv"
LOG_FILE="$DEPLOY_DIR/oauth.log"
PID_FILE="$DEPLOY_DIR/oauth.pid"

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }
log_error() { echo -e "\033[0;31m[ERROR]\033[0m $1"; }

# 停止现有服务
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log_info "停止现有服务 (PID: $PID)..."
        kill "$PID" && sleep 2
    fi
fi

# 创建目录并解压
log_info "创建部署目录..."
mkdir -p "$DEPLOY_DIR" && cd "$DEPLOY_DIR"
log_info "解压部署包..."
tar -xzf "$HOME/nautilus-oauth.tar.gz"

# 设置虚拟环境
log_info "设置虚拟环境..."
[ ! -d "$VENV_DIR" ] && python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# 安装依赖
log_info "安装依赖..."
pip install -q --upgrade pip
pip install -q fastapi uvicorn[standard] sqlalchemy psycopg2-binary python-jose[cryptography] passlib[bcrypt] python-multipart httpx slowapi fastapi-csrf-protect redis pydantic-settings python-dotenv

# 配置环境变量
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    log_info "创建环境配置..."
    cat > "$DEPLOY_DIR/.env" << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/venture_daily_report
JWT_SECRET=pRUq_aE--dXuv0iBRcLD4lLfX40c0TLGboH7CbkyJv8
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400
CSRF_SECRET_KEY=ni2HbX-pMcfF7XZpZSPCQVXKTY7fKsLEYwrsoGxAdnY
GITHUB_CLIENT_ID=Ov23liYOPQqFZRw5rGf9
GITHUB_CLIENT_SECRET=eefc9d8fed1c7507915b234c0a2385d006a77259
GITHUB_REDIRECT_URI=https://chunxiao.wang/api/auth/github/callback
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=https://chunxiao.wang/api/auth/google/callback
FRONTEND_URL=https://chunxiao.wang
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=https://chunxiao.wang,https://www.chunxiao.wang
ALLOWED_ORIGINS=https://chunxiao.wang,https://www.chunxiao.wang
RATE_LIMIT_ENABLED=true
TESTING=false
EOF
fi

# 数据库迁移
if [ -f "$DEPLOY_DIR/migrations/add_google_oauth.sql" ]; then
    log_info "运行数据库迁移..."
    PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d venture_daily_report -f "$DEPLOY_DIR/migrations/add_google_oauth.sql" 2>/dev/null || log_warn "迁移可能已执行"
fi

# 启动服务
log_info "启动 OAuth 服务..."
nohup "$VENV_DIR/bin/uvicorn" main:app --host 127.0.0.1 --port 8000 --workers 2 > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
sleep 3

# 验证服务
if curl -s http://127.0.0.1:8000/health > /dev/null; then
    log_info "✅ OAuth 服务运行正常 (PID: $(cat $PID_FILE))"
else
    log_error "❌ 服务启动失败"
    exit 1
fi

# 配置 Nginx
if ! grep -q "location /api/auth/" /etc/nginx/sites-available/vcreport 2>/dev/null; then
    log_info "配置 Nginx..."
    sudo cp /etc/nginx/sites-available/vcreport /etc/nginx/sites-available/vcreport.backup.$(date +%Y%m%d_%H%M%S)
    sudo sed -i '/location \/ {/i \    location /api/auth/ {\n        proxy_pass http://127.0.0.1:8000;\n        proxy_http_version 1.1;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n    }\n' /etc/nginx/sites-available/vcreport
    sudo nginx -t && sudo systemctl reload nginx
fi

# 更新 venture-daily-report
if [ -f "$HOME/venture-daily-report/.env" ]; then
    if ! grep -q "OAUTH_SERVER_URL" "$HOME/venture-daily-report/.env"; then
        log_info "更新 venture-daily-report 配置..."
        cp "$HOME/venture-daily-report/.env" "$HOME/venture-daily-report/.env.backup.oauth"
        echo -e "\nOAUTH_SERVER_URL=http://127.0.0.1:8000" >> "$HOME/venture-daily-report/.env"
        pm2 restart venture-daily-report
    fi
fi

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "OAuth 端点:"
echo "  - GitHub: https://chunxiao.wang/api/auth/github/login"
echo "  - Google: https://chunxiao.wang/api/auth/google/login"
echo ""
echo "管理命令:"
echo "  - 查看日志: tail -f $LOG_FILE"
echo "  - 停止服务: kill \$(cat $PID_FILE)"
