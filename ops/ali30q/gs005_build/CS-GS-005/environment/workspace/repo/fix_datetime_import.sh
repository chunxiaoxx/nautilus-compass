#!/bin/bash
# 修复auth.py缺少datetime导入的问题

AUTH_FILE=~/nautilus-mvp/phase3/backend/api/auth.py

# 检查是否已经有datetime导入
if ! grep -q "^from datetime import datetime" "$AUTH_FILE"; then
    echo "Adding datetime import..."
    sed -i '1i from datetime import datetime' "$AUTH_FILE"
    echo "✅ datetime import added"
else
    echo "✅ datetime import already exists"
fi

# 验证修复
echo ""
echo "Checking imports:"
head -5 "$AUTH_FILE"
