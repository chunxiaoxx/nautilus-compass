#!/bin/bash
# P2v2 LoRA 一条龙:升 transformers → 验证 Qwen3 → 预下载模型 → 训练
# 日志: /root/runtime/judge_lora/run.log;任一验证失败即停(红灯不硬跑)
set -e
mkdir -p /root/runtime/judge_lora
cd /root

echo "=== [1/4] pip upgrade transformers (tsinghua mirror) ==="
python3 -m pip install -q -U 'transformers>=4.51,<5' -i https://pypi.tuna.tsinghua.edu.cn/simple --break-system-packages 2>&1 | tail -3

echo "=== [2/4] verify Qwen3 import ==="
python3 -c "from transformers import Qwen3ForCausalLM, AutoTokenizer; import transformers; print('Qwen3 OK, transformers', transformers.__version__)"

echo "=== [3/4] predownload Qwen3-1.7B ==="
python3 - <<'PYEOF'
from huggingface_hub import snapshot_download
p = snapshot_download("Qwen/Qwen3-1.7B")
print("model at:", p)
PYEOF

echo "=== [4/4] train ==="
python3 /root/tools/train_judge_lora.py
echo "=== DONE ==="
