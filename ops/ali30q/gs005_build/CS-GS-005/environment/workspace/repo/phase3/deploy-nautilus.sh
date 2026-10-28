#!/bin/bash
set -e

echo "🚀 Nautilus 自动部署开始..."
echo "时间: $(date)"
echo ""

# 1. 进入项目目录
cd /home/ubuntu/nautilus-mvp/phase3

# 2. 备份当前代码
echo "📦 备份当前代码..."
git diff > /tmp/pre-deploy-backup-$(date +%Y%m%d_%H%M%S).patch

# 3. Stash 本地修改
echo "💾 保存本地修改..."
git stash push -m "Auto stash before deploy $(date +%Y%m%d_%H%M%S)" || true

# 4. 拉取最新代码
echo "⬇️  拉取最新代码..."
git pull origin master

# 5. 安装依赖（如果需要）
if [ -f "backend/requirements.txt" ]; then
    echo "📚 更新 Python 依赖..."
    cd backend
    pip install -r requirements.txt --quiet
    cd ..
fi

# 6. 重启后端服务
echo "🔄 重启后端服务..."
sudo systemctl restart nautilus-backend

# 7. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 8. 健康检查
echo "🏥 健康检查..."
HEALTH=$(curl -s https://api.nautilus.social/health | jq -r '.status' 2>/dev/null || echo "error")

if [ "$HEALTH" = "healthy" ]; then
    echo "✅ 部署成功！服务健康运行"
    echo ""
    echo "📊 服务状态:"
    sudo systemctl status nautilus-backend --no-pager | head -10
else
    echo "❌ 部署失败！服务不健康"
    echo "🔙 回滚..."
    git stash pop || true
    sudo systemctl restart nautilus-backend
    exit 1
fi

echo ""
echo "🎉 部署完成！"
echo "时间: $(date)"
