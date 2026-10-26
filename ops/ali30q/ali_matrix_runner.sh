#!/bin/zsh
# 阿里30题·B批判分矩阵跑批器(compass loop 专项 · 2026-10-24)
# 按 21220 排程错峰跑批;渠道探活先行;断点记日志;单题五模型齐即出矩阵
CS=~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense
LOG=~/Projects/nautilus-compass/ops/ali30q/matrix_run.log
PROBE() {
  curl -s -m 8 -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $RELAY" https://api.chunxiao.wang/v1/models 2>/dev/null
}
RELAY=$(grep ^RELAY_API_KEY ~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/.env | cut -d= -f2)
# 防堆叠:launchd 900s 一拉,单轮跑批>15min 会多实例互踩(10/25 实证同 run 开考两次);锁内 pid 死亡自动清锁
LOCK=/tmp/ali30q_runner.lock
if ! mkdir "$LOCK" 2>/dev/null; then
  _pid=$(cat "$LOCK/pid" 2>/dev/null)
  if [ -n "$_pid" ] && ! kill -0 "$_pid" 2>/dev/null; then rm -rf "$LOCK"; mkdir "$LOCK"; else exit 0; fi
fi
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT
# 恢复判定放宽:200=OpenAI端可用扩原生glm/k3/gpt;401/5xx=仅Anthropic应急通道+qwen+opus

relay=$(PROBE)
echo "[$(date '+%m-%d %H:%M')] 中转站探活: $relay (000/500=宕)" >> $LOG
# 渠道集:中转站通=5渠道;宕=qwen+opus先行
if [ "$relay" = "200" ]; then   # OpenAI 端全恢复才扩原生渠道
  # qwen3.8max 两分支同摘(10/25 补 if 分支):渠道表仍指 bl.cmd(Windows 名),Mac 无 bl CLI,
  # relay 恢复走 if 分支后连崩 96 次;v5 渠道表修好前不回
  # kimi 走 ark 直连(10/25 R17 实核:relay k3 池 429 累计 95,v5 渠道表无 kimi-k3-256k key
  # ——559b0e1f 改名落空 KeyError 连崩;渠道表 verified 替代线=kimi-k3-ark,key 已入 env)
  # kimi-k3-ark 暂停(平台 #21909):CS-005 四槽空 body,候 ARK key/端点/配额归因后定槽补跑。
  # qwen3.8max 仍因 Mac 无 bl CLI 暂停；不可把三通道恢复表述为四通道全恢复。
  MODELS=(glm5.3 gpt-6-astra opus5.5)
else
  # qwen3.8max 摘除(10/24):bailian 协议需 bl CLI,Windows arm 线退役后 Mac 未装
  # (shutil.which("bl") 落空→FileNotFoundError 崩循环);bl 装好后加回
  # glm5.3-anthropic 暂停(R69 2026-10-26):中转 000 时走应急通道,但 04:08-11:16
  # 连续 Errno 8 nodename nor servname(DNS) raw_len=0/score=null,同因远超三连红线;
  # 候 v5 查 Anthropic 端点主机名。中转 200 时仍走 if 分支 glm5.3/gpt/opus。
  MODELS=(opus5.5)
fi
ITEMS=(CS-010 CS-011 CS-012 CS-013 CS-014 CS-001 CS-002 CS-003 CS-004 CS-005 CS-006 CS-007 CS-301)
for item in $ITEMS; do
  # 题目就绪检查(笔记本线未交付的题跳过)
  [ -f "$CS/items/$item/task.toml" ] || { echo "[$item] 未就绪,跳过" >> $LOG; continue }
  # 考试副本物化(model_solve 只读不建;原件=repo_bak,10/24 修连续 workspace/repo 缺失断点)
  [ -d "$CS/items/$item/environment/workspace/repo" ] || \
    cp -R "$CS/items/$item/environment/workspace/repo_bak" "$CS/items/$item/environment/workspace/repo"
  for m in $MODELS; do
    for run in 0 1 2 3; do
      R="$CS/items/$item/_s5/${m}_run${run}_result.json"
      # 幂等:有 score(成功读数)才跳过;error 结果重跑
      if [ -f "$R" ]; then
        S=$(python3 -c "import json;d=json.load(open('$R'));print(d.get('score'))" 2>/dev/null)
        [ "$S" != "None" ] && continue
        rm -f "$R"
      fi
      echo "[$(date '+%H:%M')] $item × $m × run$run 开考" >> $LOG
      (cd $CS && .venv-judge/bin/python tools/model_solve.py $item --model $m --run $run >> $LOG 2>&1)
      sleep 20   # relay 12req/min 约束
    done
  done
  # 单题齐检查→矩阵
  n=$(ls $CS/items/$item/_s5/*_run[0-3]_result.json 2>/dev/null | wc -l | tr -d ' ')
  echo "[$item] 已完成读数: $n/20" >> $LOG
done
echo "[$(date '+%H:%M')] 本轮跑批结束" >> $LOG
