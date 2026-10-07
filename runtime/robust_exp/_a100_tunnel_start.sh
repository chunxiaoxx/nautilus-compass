#!/usr/bin/env bash
# A100→cloud 反向隧道守护:cloud 127.0.0.1:19986 → A100:8400(embed 服务)
# 由 /root/vdd4/tunnel_daemon.sh 调用;断线自动重连(30s 间隔)
while true; do
  ssh -NR 19986:127.0.0.1:8400 \
      -p 24860 -i /root/.ssh/id_ed25519 \
      -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
      -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes \
      ubuntu@43.160.239.61
  sleep 30
done
