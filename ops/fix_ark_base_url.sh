#!/bin/bash
# 治 ARK 真接入路径(/api/plan/v3 → /api/v3)
# 用户拍执行 · 默认 dry-run

set -e

ENV_FILE="$HOME/.claude/.cache/.fde_api_secrets.env"

echo "=== ARK 真接入路径治根脚本 ==="
echo ""
echo "真根因: ARK_BASE_URL=/api/plan/v3 走老 plan 订阅路径 · 新 key 没 plan 订阅 = 401"
echo "真治法: 改 /api/plan/v3 → /api/v3(OpenAI 兼容 · 标准按量)"
echo ""
echo "当前 ARK_BASE_URL:"
grep "ARK_BASE_URL" "$ENV_FILE" || echo "  (not found)"
echo ""
echo "治法:"
echo "  sed -i 's|api/plan/v3|api/v3|g' $ENV_FILE"
echo ""
echo "⚠️  真执行前请确认:用户已 7/4 04:13 拍 ark 仍可用 = 真改后即用"
echo ""
read -p "执行治根? (y/N): " confirm
if [ "$confirm" = "y" ]; then
    sed -i 's|api/plan/v3|api/v3|g' "$ENV_FILE"
    echo "✓ ARK_BASE_URL 改后:"
    grep "ARK_BASE_URL" "$ENV_FILE"
    echo ""
    echo "✓ 真测试:"
    ARK_BASE_URL_NEW=$(grep "ARK_BASE_URL" "$ENV_FILE" | cut -d= -f2)
    ARK_API_KEY=$(grep "ARK_API_KEY" "$ENV_FILE" | cut -d= -f2)
    ARK_MODEL=$(grep "ARK_MODEL_DOUBAO" "$ENV_FILE" | cut -d= -f2)
    curl -sS -m 30 -X POST "$ARK_BASE_URL_NEW/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $ARK_API_KEY" \
        -d "{\"model\":\"$ARK_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"echo ok\"}],\"max_tokens\":5}" \
        2>&1 | head -3
else
    echo "✗ 用户未拍,不改"
fi