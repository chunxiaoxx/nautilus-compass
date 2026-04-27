#!/bin/bash
# V5 Memory Plugin · 一键装 BGE 启用真语义召回
# 装完后 v0.2 自动启用 · 不装就走 v0.1 metadata 模式

set -e

echo "=== V5 Memory Plugin · BGE 安装 ==="
echo ""
echo "将装: sentence-transformers + BAAI/bge-small-zh-v1.5 (~400MB total)"
echo ""

# 找 python · 优先 V5 cleanup venv 然后系统
PIP=""
PYTHON=""
for candidate in \
    "/c/Users/chunx/Projects/nautilus-v5-cleanup/.venv/Scripts/python.exe" \
    "/c/Users/chunx/Projects/nautilus-v5/.venv/Scripts/python.exe" \
    "$(which python3)" \
    "$(which python)"; do
    if [ -x "$candidate" ] || command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "❌ 找不到 python · 请先装 python 3.9+"
    exit 1
fi

echo "用 python: $PYTHON"
echo ""

# 装
"$PYTHON" -m pip install --user sentence-transformers || {
    echo "❌ pip install 失败"
    exit 1
}

# 预热下载模型 (避免第一次 hook 调用时下载阻塞)
"$PYTHON" -c "
from sentence_transformers import SentenceTransformer
print('Pre-downloading BAAI/bge-small-zh-v1.5...')
m = SentenceTransformer('BAAI/bge-small-zh-v1.5')
emb = m.encode('test')
print(f'OK · embedding dim={len(emb)}')
" || {
    echo "❌ BGE 模型下载失败 · 检查网络"
    exit 1
}

echo ""
echo "✅ BGE 装好 · zenmind-mem 自动启用真语义召回"
echo "   下个 Claude Code prompt 会看到 🎯 BGE 召回 top 5 相关 memory"
