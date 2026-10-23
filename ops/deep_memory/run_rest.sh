#!/bin/zsh
cd "$(dirname "$0")/../.."
PY=.venv/bin/python
for d in "-Users-chunxiao-wang-Projects-nautilus-core" \
         "-Users-chunxiao-wang-Projects-nautilus-v5" \
         "-Users-chunxiao-wang" \
         "-Users-chunxiao-wang-Projects-venture-daily-report" \
         "-Users-chunxiao-wang-Projects-arm-worker-prime" \
         "C--Users-chunx" \
         "-Users-chunxiao-wang-Projects-quantum-buddha-project" \
         "-Users-chunxiao-wang-Projects-caishen-ai" \
         "-Users-chunxiao-wang-Projects-venture_daily_report"; do
  echo "════ $d ════"
  $PY ops/deep_memory/deep_memory_pipeline.py --dir="$d" 2>&1 | tail -3
done
echo "════ REST-DONE ════"
