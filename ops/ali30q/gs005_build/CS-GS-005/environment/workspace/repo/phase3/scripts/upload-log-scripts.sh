#!/bin/bash

# 将本地脚本上传到服务器并设置权限

echo "=== Uploading Log Management Scripts to Server ==="
echo ""

# 定义服务器别名
SERVER="cloud"
REMOTE_DIR="/home/ubuntu"

# 上传分析脚本
echo "1. Uploading analyze-logs.sh..."
scp scripts/analyze-logs.sh $SERVER:$REMOTE_DIR/
ssh $SERVER "chmod +x $REMOTE_DIR/analyze-logs.sh"
echo "✅ analyze-logs.sh uploaded"
echo ""

# 上传查询脚本
echo "2. Uploading loki-queries.sh..."
scp scripts/loki-queries.sh $SERVER:$REMOTE_DIR/
ssh $SERVER "chmod +x $REMOTE_DIR/loki-queries.sh"
echo "✅ loki-queries.sh uploaded"
echo ""

# 上传测试脚本
echo "3. Uploading test-log-system.sh..."
scp scripts/test-log-system.sh $SERVER:$REMOTE_DIR/
ssh $SERVER "chmod +x $REMOTE_DIR/test-log-system.sh"
echo "✅ test-log-system.sh uploaded"
echo ""

# 上传告警规则
echo "4. Uploading alert rules..."
scp config/loki-alert-rules.yaml $SERVER:$REMOTE_DIR/loki-config/rules.yaml
echo "✅ Alert rules uploaded"
echo ""

# 验证上传
echo "5. Verifying uploaded files..."
ssh $SERVER "ls -lh $REMOTE_DIR/*.sh $REMOTE_DIR/loki-config/rules.yaml"
echo ""

echo "=== Upload Complete ==="
echo ""
echo "You can now run:"
echo "  ssh $SERVER 'bash $REMOTE_DIR/test-log-system.sh'"
echo "  ssh $SERVER 'bash $REMOTE_DIR/analyze-logs.sh'"
echo "  ssh $SERVER 'bash $REMOTE_DIR/loki-queries.sh'"
