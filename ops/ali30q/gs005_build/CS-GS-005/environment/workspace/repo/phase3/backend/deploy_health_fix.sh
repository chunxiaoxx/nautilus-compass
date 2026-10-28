#!/bin/bash
# 数据库健康检查修复 - 快速部署脚本

set -e  # 遇到错误立即退出

SERVER="ubuntu@115.159.62.192"
REMOTE_PATH="/home/ubuntu/nautilus-mvp/phase3/backend"
LOCAL_FILE="monitoring_config.py"

echo "=========================================="
echo "Nautilus 数据库健康检查修复部署"
echo "=========================================="
echo ""

# 步骤 1: 备份远程文件
echo "📦 步骤 1/4: 备份远程文件..."
ssh $SERVER "cd $REMOTE_PATH && cp monitoring_config.py monitoring_config.py.backup.$(date +%Y%m%d_%H%M%S)"
echo "✅ 备份完成"
echo ""

# 步骤 2: 上传修复文件
echo "📤 步骤 2/4: 上传修复文件..."
scp "$LOCAL_FILE" "$SERVER:$REMOTE_PATH/"
echo "✅ 上传完成"
echo ""

# 步骤 3: 重启服务
echo "🔄 步骤 3/4: 重启后端服务..."
ssh $SERVER "cd $REMOTE_PATH && sudo systemctl restart nautilus-backend"
echo "⏳ 等待服务启动 (10秒)..."
sleep 10
echo "✅ 服务重启完成"
echo ""

# 步骤 4: 验证修复
echo "🔍 步骤 4/4: 验证健康检查..."
HEALTH_CHECK=$(curl -s http://115.159.62.192:8000/health)
echo "$HEALTH_CHECK" | python3 -m json.tool

# 检查状态
STATUS=$(echo "$HEALTH_CHECK" | python3 -c "import sys, json; print(json.load(sys.stdin).get('checks', {}).get('database', {}).get('status', 'unknown'))")

echo ""
if [ "$STATUS" = "healthy" ]; then
    echo "✅ 修复成功！数据库健康检查正常"
    echo "=========================================="
    exit 0
else
    echo "❌ 修复失败！数据库状态: $STATUS"
    echo "=========================================="
    echo ""
    echo "回滚命令:"
    echo "ssh $SERVER 'cd $REMOTE_PATH && cp monitoring_config.py.backup.* monitoring_config.py && sudo systemctl restart nautilus-backend'"
    exit 1
fi
