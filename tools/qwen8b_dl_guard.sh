#!/bin/bash
# Qwen3-8B 下载守护(R466): hf-mirror 对 16GB 大文件不稳(实测两断),
# loop 自动续传(hf-cli 断点续传), 完成自停。
TARGET=/root/vdf/models/Qwen3-8B
while true; do
    # 完成判定: config.json + 全部 safetensors 分片在位且无 .incomplete 残留
    N_SHARDS=$(ls "$TARGET"/model-*.safetensors 2>/dev/null | wc -l)
    INCOMPLETE=$(find "$TARGET" -name "*.incomplete" 2>/dev/null | wc -l)
    if [ "$N_SHARDS" -ge 4 ] && [ "$INCOMPLETE" -eq 0 ] && [ -f "$TARGET/config.json" ]; then
        echo "[$(date +%H:%M)] download complete, guard exiting" >> /root/vdf/dl8b_guard.log
        break
    fi
    if ! pgrep -f "huggingface-cli downloa[d]" > /dev/null; then
        echo "[$(date +%H:%M)] resume download" >> /root/vdf/dl8b_guard.log
        cd /root/vdf
        HF_ENDPOINT=https://hf-mirror.com setsid nohup huggingface-cli download Qwen/Qwen3-8B \
            --local-dir "$TARGET" < /dev/null > dl_qwen8b_guard.log 2>&1 &
        disown
    fi
    sleep 120
done
