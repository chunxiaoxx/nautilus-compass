#!/bin/bash
# Git Push Retry Script
# 用于在网络不稳定时重试推送到GitHub

MAX_RETRIES=5
RETRY_DELAY=10

echo "开始推送到GitHub..."
echo "最大重试次数: $MAX_RETRIES"
echo ""

for i in $(seq 1 $MAX_RETRIES); do
    echo "尝试 $i/$MAX_RETRIES..."

    if git push origin master; then
        echo ""
        echo "✅ 推送成功！"
        exit 0
    else
        if [ $i -lt $MAX_RETRIES ]; then
            echo "❌ 推送失败，${RETRY_DELAY}秒后重试..."
            sleep $RETRY_DELAY
        fi
    fi
done

echo ""
echo "❌ 推送失败，已达到最大重试次数"
echo "请稍后手动执行: git push origin master"
exit 1
