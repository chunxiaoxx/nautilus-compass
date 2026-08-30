#!/bin/bash
# LME-S s250 补跑(前次与 d13 争抢 plan 端点,subject read timeout 污染 2 题,作废重跑)
# 挂载时机: d13 双域(run_compass)全结束后;s0 分片活着的也可以共存(此时无 d13 争抢,2 分片 = 原基线并发模式)
# 判据: 对照 8/29 基线 e2e 0.567(judge 口径差异注明:本次 judge=doubao plan 端点,基线=glm-5.3-flash)
if pgrep -f run_compass.py > /dev/null; then echo "ABORT: run_compass still running (d13/d14 not finished)"; exit 1; fi
setsid nohup /root/e2e/run_shard_knife3_v2.sh 250 500 < /dev/null > /dev/null 2>&1 &
echo "s250 relaunched, log /tmp/e2e_knife3_s250.log(旧 log 已被覆盖属预期)"
