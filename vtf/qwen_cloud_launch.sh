#!/bin/bash
# cloud 中转下载 Qwen3.5-9B(18G, hf-mirror)
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
cd /home/ubuntu
setsid nohup python3 /tmp/qwen_dl_cloud.py > /tmp/qwen_cloud.log 2>&1 < /dev/null &
echo LAUNCHED
