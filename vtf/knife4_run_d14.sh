#!/bin/bash
# d14 = 刀3(knife3 merged embedder,/root/compass_cfg.json 已切)+ 刀4(abstention gate)一键执行
# 前置: d13 双域必须已结束(run_compass 进程数=0),否则退出(防污染 d13)
# 冒烟策略: 点火后由 compass 巡检前 10 题把关(含 dynamic ≥3 道),异常 kill 重挂(harness 幂等,已产出题不重跑)
# 判据: vtf/_compass_lmev2_out/d14_PREREGISTERED_CRITERIA.md(commit 9ff3a0d)
set -e
echo "[d14] pre-check: run_compass must be absent"
if pgrep -f run_compass.py > /dev/null; then echo "ABORT: run_compass still running (d13 not finished)"; exit 1; fi

echo "[d14] step1: apply knife4 abstention-gate patch"
python3 /root/knife4/lmev2_harness_prompt_patch_d4.py
N=$(grep -c "MUST give the concrete answer from it" /root/LongMemEval-V2/evaluation/harness.py)
[ "$N" -ge 1 ] || { echo "ABORT: gate keyword missing after patch"; exit 1; }
echo "[d14] patch verified (gate keyword x$N)"

echo "[d14] step2: launch web -> enterprise (serial)"
cd /root/LongMemEval-V2
export $(cat /root/e2e/judge.env | xargs)
PLAN=https://ark.cn-beijing.volces.com/api/coding/v3
MODEL=doubao-seed-2-0-pro-260215
setsid nohup bash -c "python3 run_compass.py --domain web --tier small --model $MODEL --base-url $PLAN --prompt-workers 1 --reader-concurrency 4 --evaluator-model $MODEL --evaluator-base-url $PLAN --output-root /root/lmev2_runs_d14 > /tmp/full_d14_web.log 2>&1; python3 run_compass.py --domain enterprise --tier small --model $MODEL --base-url $PLAN --prompt-workers 1 --reader-concurrency 4 --evaluator-model $MODEL --evaluator-base-url $PLAN --output-root /root/lmev2_runs_d14 > /tmp/full_d14_ent.log 2>&1" < /dev/null > /dev/null 2>&1 &
echo "[d14] LAUNCHED web(d14) -> ent(d14), logs /tmp/full_d14_{web,ent}.log"
