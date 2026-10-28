#!/bin/bash

echo "=== Nautilus 代码同步检查 ==="
echo ""

echo "本地提交:"
cd /home/ubuntu/nautilus-mvp/phase3
git log -1 --oneline

echo ""
echo "GitHub 提交:"
git fetch origin --quiet
git log origin/master -1 --oneline

echo ""
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/master)" ]; then
    echo "✅ 代码已同步"
else
    echo "⚠️  代码不同步，需要 pull"
fi
