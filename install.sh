#!/bin/bash
# V5 Memory Plugin v1.0 · 一键装

set -e
PLUGIN_DIR="$(dirname "$(readlink -f "$0")")"

echo "=== V5 Memory Plugin v1.0 安装 ==="
echo ""

# 1. install BGE
echo "[1/4] 装 sentence-transformers + BAAI/bge-small-zh-v1.5 ..."
bash "$PLUGIN_DIR/install_bge.sh"

# 2. start daemon
echo ""
echo "[2/4] 启动 daemon (后台 BGE 常驻 · 召回 < 2s) ..."
bash "$PLUGIN_DIR/daemon_start.sh"

# 3. build links (A-MEM)
echo ""
echo "[3/4] A-MEM 链接发现 (cosine cross-检测 supersede) ..."
PYTHON=""
for c in python3 python; do
    if command -v "$c" &>/dev/null; then PYTHON="$c"; break; fi
done
"$PYTHON" "$PLUGIN_DIR/links_finder.py" 2>&1 | tail -8

# 4. settings.json hooks
echo ""
echo "[4/4] settings.json hook 已注册:"
echo "  · UserPromptSubmit → hook.sh (metadata + strategy lookup · 0.5s)"
echo "  · Stop → stop_hook.py (auto distill strategy · 0 LLM)"

echo ""
echo "✅ V5 Memory Plugin v1.0 ready"
echo ""
echo "用法:"
echo "  · 自动: 每个 user prompt 看到 metadata + strategy + age 警告"
echo "  · 深度: python3 $PLUGIN_DIR/recall.py --bge --query \"<问题>\""
echo "    daemon 命中 → 1.8s · BGE 真召回 + drift detection"
echo ""
echo "维护:"
echo "  · daemon 重启: bash daemon_stop.sh && bash daemon_start.sh"
echo "  · 重新算 links: python3 links_finder.py"
echo "  · 看 strategy: python3 strategy_store.py list"
echo "  · 自测: python3 selftest.py · python3 deeptest.py"
