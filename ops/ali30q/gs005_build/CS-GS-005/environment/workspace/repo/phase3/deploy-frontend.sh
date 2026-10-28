#!/bin/bash
set -e

# Nautilus 前端自动化部署脚本
# 版本: 1.0
# 作者: Claude Sonnet 4.6
# 日期: 2026-03-03

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Nautilus 前端自动化部署"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 配置变量
FRONTEND_DIR="/home/ubuntu/nautilus-mvp/phase3/frontend"
DEPLOY_DIR="/var/www/nautilus/current"
BACKUP_DIR="/var/www/nautilus/backup"
API_URL="https://api.nautilus.social"
WS_URL="wss://api.nautilus.social"

# 1. 进入前端目录
echo "📁 进入前端目录..."
cd "$FRONTEND_DIR" || exit 1

# 2. 验证环境变量配置
echo "🔍 验证环境变量配置..."
cat > .env.production << EOF
VITE_API_URL=$API_URL
VITE_WS_URL=$WS_URL
EOF

echo "✅ 环境变量配置完成"
echo "   VITE_API_URL=$API_URL"
echo "   VITE_WS_URL=$WS_URL"
echo ""

# 3. 清理旧构建
echo "🧹 清理旧构建..."
rm -rf dist/
echo "✅ 清理完成"
echo ""

# 4. 构建前端
echo "🔨 构建前端..."
BUILD_START=$(date +%s)
npm run build
BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))
echo "✅ 构建完成（耗时: ${BUILD_TIME}秒）"
echo ""

# 5. 验证构建结果
echo "🔍 验证构建结果..."
if [ ! -d "dist" ]; then
    echo "❌ 错误: dist 目录不存在"
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    echo "❌ 错误: index.html 不存在"
    exit 1
fi

FILE_COUNT=$(find dist -type f | wc -l)
echo "✅ 构建验证通过（文件数: $FILE_COUNT）"
echo ""

# 6. 备份当前部署
echo "💾 备份当前部署..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
sudo mkdir -p "$BACKUP_PATH"

if [ -d "$DEPLOY_DIR" ] && [ "$(ls -A $DEPLOY_DIR)" ]; then
    sudo cp -r "$DEPLOY_DIR"/* "$BACKUP_PATH/" 2>/dev/null || true
    echo "✅ 备份完成: $BACKUP_PATH"
else
    echo "⚠️  没有需要备份的文件"
fi
echo ""

# 7. 部署新版本
echo "🚀 部署新版本..."
sudo rm -rf "$DEPLOY_DIR"/*
sudo cp -r dist/* "$DEPLOY_DIR"/
sudo chown -R www-data:www-data "$DEPLOY_DIR"
echo "✅ 部署完成"
echo ""

# 8. 验证文件权限
echo "🔍 验证文件权限..."
OWNER=$(stat -c '%U:%G' "$DEPLOY_DIR/index.html")
if [ "$OWNER" = "www-data:www-data" ]; then
    echo "✅ 文件权限正确"
else
    echo "⚠️  文件权限: $OWNER（应该是 www-data:www-data）"
fi
echo ""

# 9. 测试 Nginx 配置
echo "🔍 测试 Nginx 配置..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Nginx 配置正确"
else
    echo "❌ Nginx 配置错误"
    exit 1
fi
echo ""

# 10. 重载 Nginx
echo "🔄 重载 Nginx..."
sudo systemctl reload nginx
echo "✅ Nginx 重载完成"
echo ""

# 11. 验证部署
echo "🔍 验证部署..."
sleep 2

# 测试前端
if curl -s https://nautilus.social | grep -q "Nautilus"; then
    echo "✅ 前端访问正常"
else
    echo "❌ 前端访问失败，开始回滚..."
    sudo rm -rf "$DEPLOY_DIR"/*
    sudo cp -r "$BACKUP_PATH"/* "$DEPLOY_DIR"/
    sudo systemctl reload nginx
    echo "❌ 已回滚到上一个版本"
    exit 1
fi

# 测试 API
if curl -s https://api.nautilus.social/health | grep -q "healthy"; then
    echo "✅ API 连接正常"
else
    echo "⚠️  API 连接异常"
fi
echo ""

# 12. 清理旧备份（保留最近5个）
echo "🧹 清理旧备份..."
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR" | wc -l)
if [ "$BACKUP_COUNT" -gt 5 ]; then
    cd "$BACKUP_DIR"
    ls -1t | tail -n +6 | xargs -I {} sudo rm -rf {}
    echo "✅ 清理完成（保留最近5个备份）"
else
    echo "✅ 备份数量正常（$BACKUP_COUNT 个）"
fi
echo ""

# 13. 部署总结
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 部署成功！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 部署信息:"
echo "   • 构建时间: ${BUILD_TIME}秒"
echo "   • 文件数量: $FILE_COUNT"
echo "   • 备份位置: $BACKUP_PATH"
echo "   • 部署时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "🌐 访问地址:"
echo "   • 前端: https://nautilus.social"
echo "   • API: https://api.nautilus.social"
echo ""
echo "💡 提示:"
echo "   • 如需回滚: sudo cp -r $BACKUP_PATH/* $DEPLOY_DIR/"
echo "   • 清除缓存: Ctrl+Shift+Delete"
echo "   • 硬刷新: Ctrl+F5"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
