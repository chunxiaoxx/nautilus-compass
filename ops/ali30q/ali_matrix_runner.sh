#!/bin/zsh
# 阿里30题·B批判分矩阵跑批器(compass loop 专项 · 2026-10-24)
# 按 21220 排程错峰跑批;渠道探活先行;断点记日志;单题五模型齐即出矩阵
CS=~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense
LOG=~/Projects/nautilus-compass/ops/ali30q/matrix_run.log
PROBE() {
  curl -s -m 8 -o /dev/null -w "%{http_code}" https://api.chunxiao.wang/v1/models 2>/dev/null
}
relay=$(PROBE)
echo "[$(date '+%m-%d %H:%M')] 中转站探活: $relay (000/500=宕)" >> $LOG
# 渠道集:中转站通=5渠道;宕=qwen+opus先行
if [ "$relay" = "200" ]; then
  MODELS=(glm5.3 kimi-k3 gpt-6-astra qwen3.8max opus5.5)
else
  MODELS=(qwen3.8max opus5.5)
fi
ITEMS=(CS-010 CS-011 CS-012 CS-013 CS-014)
for item in $ITEMS; do
  # 题目就绪检查(笔记本线未交付的题跳过)
  [ -f "$CS/items/$item/task.toml" ] || { echo "[$item] 未就绪,跳过" >> $LOG; continue }
  for m in $MODELS; do
    for run in 0 1 2 3; do
      R="$CS/items/$item/_s5/${m}_run${run}_result.json"
      [ -f "$R" ] && continue  # 幂等:已有结果跳过
      echo "[$(date '+%H:%M')] $item × $m × run$run 开考" >> $LOG
      (cd $CS && python3 tools/model_solve.py $item --model $m --run $run >> $LOG 2>&1)
      sleep 20   # relay 12req/min 约束
    done
  done
  # 单题齐检查→矩阵
  n=$(ls $CS/items/$item/_s5/*_run[0-3]_result.json 2>/dev/null | wc -l | tr -d ' ')
  echo "[$item] 已完成读数: $n/20" >> $LOG
done
echo "[$(date '+%H:%M')] 本轮跑批结束" >> $LOG
