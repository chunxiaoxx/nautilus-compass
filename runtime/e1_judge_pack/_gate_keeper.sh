#!/usr/bin/env bash
# E1 判读守门抢窗:显存 free>=4500MiB 即起 3B 判读(死线 13:16)
while true; do
  FREE=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
  if [ "$FREE" -ge 4500 ] && ! pgrep -f e1_j2_batch_judge_3b >/dev/null; then
    echo "[$(date +%H:%M:%S)] free=${FREE}MiB launching judge"
    cd /root && /root/openpi/.venv/bin/python tools/e1_j2_batch_judge_3b.py >> /root/e1_3b_chain.log 2>&1
    break
  fi
  echo "[$(date +%H:%M:%S)] free=${FREE}MiB waiting"
  sleep 120
done
