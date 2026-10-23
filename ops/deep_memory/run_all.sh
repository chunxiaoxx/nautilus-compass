#!/bin/zsh
set -e
cd "$(dirname "$0")/../.."
PY=.venv/bin/python
for d in "-Users-chunxiao-wang-Projects-nautilusflywheel" \
         "-Users-chunxiao-wang-Projects-nautilus-core" \
         "-Users-chunxiao-wang-Projects-nautilus-v5" \
         "-Users-chunxiao-wang" \
         "-Users-chunxiao-wang-Projects-venture-daily-report" \
         "-Users-chunxiao-wang-Projects-arm-worker-prime" \
         "-Users-chunxiao-wang-Projects-arm-worker-v7" \
         "C--Users-chunx" \
         "-Users-chunxiao-wang-Projects-quantum-buddha-project" \
         "-Users-chunxiao-wang-Projects-caishen-ai"; do
  echo "════ $d ════"
  $PY ops/deep_memory/deep_memory_pipeline.py --dir="$d" || echo "⚠️ $d 失败,继续"
done
echo "════ 全框完成 ════"
ls -la ops/deep_memory/*.db | awk '{print $5, $NF}'
