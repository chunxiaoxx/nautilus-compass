#!/bin/bash
# LME-V2 GPU 机部署 v2 · 全国内源(pypi.org 被墙已证)· 日志 /tmp/deploy.log
exec > /tmp/deploy.log 2>&1
set -x
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
echo "=== NET PROBE ==="
timeout 15 python3 - <<'PYEOF'
import urllib.request
for u in ['https://github.com', 'https://hf-mirror.com', 'https://modelscope.cn']:
    try:
        r = urllib.request.urlopen(u, timeout=6)
        print(u, '->', r.status)
    except Exception as e:
        print(u, '-> FAIL', str(e)[:40])
PYEOF
echo "=== STEP1 vllm(brings torch2.6.0) ==="
pip install vllm==0.8.5 2>&1 | tail -3
python3 -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda)"
echo "=== STEP2 st+bm25+agents ==="
pip install sentence-transformers rank_bm25 openai-agents 2>&1 | tail -3
echo "=== STEP3 modelscope ==="
pip install modelscope 2>&1 | tail -1
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
git clone --depth 1 https://github.com/xiaowu0162/LongMemEval-V2.git 2>&1 | tail -1
if [ ! -d LongMemEval-V2 ]; then
  echo "GITHUB_FAIL_USE_FALLBACK"
  exit 42
fi
cd LongMemEval-V2
export HF_ENDPOINT=https://hf-mirror.com
pip install huggingface_hub 2>&1 | tail -1
python3 data/download_data.py --data-root data/longmemeval-v2
python3 data/prepare_data.py --data-root "$(pwd)/data/longmemeval-v2" --mode symlink
python3 data/validate_data.py --data-root "$(pwd)/data/longmemeval-v2" --tier small
echo "DEPLOY_ALL_DONE"
