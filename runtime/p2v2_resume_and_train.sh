#!/bin/bash
# P2v2 LoRA 续跑:验证环境 → 下载(重试×5,断点续传)→ 训练
set -e
mkdir -p /root/runtime/judge_lora
cd /root

echo "=== [1/3] verify env ==="
python3 -c "from transformers import Qwen3ForCausalLM; import transformers; print('Qwen3 OK, transformers', transformers.__version__)"

echo "=== [2/3] download Qwen3-1.7B (retry x5, resume) ==="
python3 - <<'PYEOF'
import time
from huggingface_hub import snapshot_download
for attempt in range(1, 6):
    try:
        p = snapshot_download("Qwen/Qwen3-1.7B", max_workers=4)
        print("model at:", p)
        break
    except Exception as e:
        print(f"attempt {attempt} failed: {type(e).__name__}: {e}", flush=True)
        if attempt == 5:
            raise
        time.sleep(20 * attempt)
PYEOF

echo "=== [3/3] train ==="
python3 /root/tools/train_judge_lora.py
echo "=== DONE ==="
