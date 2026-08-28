#!/bin/bash
# LME-V2 GPU 机一键部署 · 日志 /tmp/deploy.log
exec > /tmp/deploy.log 2>&1
set -x
echo "=== STEP1 vllm(brings torch2.6.0) ==="
pip install -q vllm==0.8.5 || pip install vllm==0.8.5 | tail -5
python3 -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda)"
echo "=== STEP2 st+bm25+agents ==="
pip install -q sentence-transformers rank_bm25 openai-agents || pip install sentence-transformers rank_bm25 openai-agents 2>&1 | tail -3
echo "=== STEP3 modelscope ==="
pip install -q modelscope 2>&1 | tail -1
echo "=== STEP4 models ==="
python3 - <<'PYEOF'
from modelscope import snapshot_download
snapshot_download('BAAI/bge-m3', local_dir='/root/models/bge-m3')
print('BGE_DONE')
try:
    snapshot_download('Qwen/Qwen3.5-9B', local_dir='/root/models/qwen35-9b')
    print('QWEN_DONE')
except Exception as e:
    print('QWEN_MODELSCOPE_FAIL', e)
PYEOF
echo "=== STEP5 repo+data ==="
cd /root && rm -rf LongMemEval-V2
git clone --depth 1 https://github.com/xiaowu0162/LongMemEval-V2.git
cd LongMemEval-V2
export HF_ENDPOINT=https://hf-mirror.com
pip install -q huggingface_hub 2>&1 | tail -1
python3 data/download_data.py --data-root data/longmemeval-v2
python3 data/prepare_data.py --data-root "$(pwd)/data/longmemeval-v2" --mode symlink
python3 data/validate_data.py --data-root "$(pwd)/data/longmemeval-v2" --tier small
echo "DEPLOY_ALL_DONE"
