#!/bin/bash
# LME-V2 收尾:repo 数据 + vLLM reader + compass 后端安装(STEP4 完成后跑)
exec > /tmp/finish.log 2>&1
set -x
cd /root/LongMemEval-V2
export HF_ENDPOINT=https://hf-mirror.com
echo "=== F1 validate data ==="
python3 data/validate_data.py --data-root "$(pwd)/data/longmemeval-v2" --tier small
echo "=== F2 install compass backend ==="
cp /root/compass_memory_stage.py memory_modules/compass_memory.py
grep -q compass_memory memory_modules/memory.py || echo "
from .compass_memory import CompassMemory  # noqa: E402,F401" >> memory_modules/memory.py
cat > /root/compass_cfg.json <<'CFG'
{
  "memory_type": "compass_chunk_hybrid",
  "memory_params": {
    "device": "cuda",
    "model_name": "/root/models/bge-m3",
    "top_k": 8,
    "max_state_chars": 1200,
    "max_screenshots": 4,
    "text_budget_chars": 12000
  }
}
CFG
echo "=== F3 start vllm reader ==="
export VLLM_LOGGING_LEVEL=WARNING
setsid nohup python3 -m vllm.entrypoints.openai.api_server \
  --model /root/models/qwen35-9b \
  --served-model-name Qwen/Qwen3.5-9B \
  --port 8023 --gpu-memory-utilization 0.85 \
  --max-model-len 32768 > /tmp/vllm.log 2>&1 < /dev/null &
echo "vllm launched, waiting for ready..."
for i in $(seq 1 60); do
  sleep 10
  if curl -s http://localhost:8023/v1/models 2>/dev/null | grep -q Qwen; then
    echo "VLLM_READY"; break
  fi
  if [ $i -eq 60 ]; then echo "VLLM_TIMEOUT"; tail -20 /tmp/vllm.log; fi
done
echo "FINISH_DONE"
