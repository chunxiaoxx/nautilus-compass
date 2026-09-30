#!/bin/bash
# ModelScope 通道:下载 Qwen3-1.7B → 改训练脚本 MODEL_ID → 训练
set -e
mkdir -p /root/runtime/judge_lora

echo "=== [1/3] modelscope download ==="
MODEL_PATH=$(python3 -c "
from modelscope import snapshot_download
p = snapshot_download('Qwen/Qwen3-1.7B')
print(p)
" | tail -1)
echo "MODEL_PATH=$MODEL_PATH"

echo "=== [2/3] verify size + patch MODEL_ID ==="
du -sh "$MODEL_PATH"
TOTAL=$(du -sb "$MODEL_PATH" | cut -f1)
[ "$TOTAL" -lt 3000000000 ] && echo "FAIL: too small" && exit 3
sed -i "s|MODEL_ID = \"Qwen/Qwen3-1.7B\"|MODEL_ID = \"$MODEL_PATH\"|" /root/tools/train_judge_lora.py
grep '^MODEL_ID' /root/tools/train_judge_lora.py

echo "=== [3/3] train ==="
python3 /root/tools/train_judge_lora.py
echo "=== DONE ==="
