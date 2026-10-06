#!/usr/bin/env bash
# NACRE champion (Qwen3-1.7B + best_lora) vLLM 服务 · PRECOR B/C 实验共用
set -euo pipefail
BASE=/root/vdd4/modelscope/models/Qwen--Qwen3-1.7B
ADAPTER=/root/vdd4/adapters/best_lora          # compass 提供,sha16=dbcbab6fd1ff5821 校验后用
PORT=${PORT:-8300}

pip show vllm >/dev/null 2>&1 || pip install vllm -q

nohup python -m vllm.entrypoints.openai.api_server \
  --model "$BASE" \
  --enable-lora --lora-modules champion="$ADAPTER" \
  --served-model-name nacre-champion \
  --max-model-len 8192 --port "$PORT" \
  > /root/vdd4/nacre_serve.log 2>&1 &

echo "vLLM starting on :$PORT (model=nacre-champion)"
sleep 20
curl -s "http://127.0.0.1:$PORT/v1/models" | head -c 300
echo
echo "自检: curl http://127.0.0.1:$PORT/v1/chat/completions -d '{\"model\":\"nacre-champion\",\"messages\":[{\"role\":\"user\",\"content\":\"PONG?\"}]}'"
