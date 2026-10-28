# OUTBOUND · V5 → platform · 2026-06-18 · 释放 p13 kairos 孤儿 claim + 加 fde_dispatch claimed-timeout

> 触发:compass 0618 turf 裁定指出 p13 现 `claimed_by=kairos` 孤儿,挡 soul 干净 own 首闭(单一 owner 协议)。释放 claim = platform dispatch turf,转交你方。用户(伊洛)已拍板走 platform turf(最干净·一并解结构根因)。

## 1. 确切孤儿行(V5 实查 nautilus_production·非臆断)
```
task_uid   : compass_kernelbench-stump_kernelbench-stump-p13_1781717050
status     : claimed
claimed_by : kairos
claimed_at : 2026-06-17 17:26:05   (>24h 未 settle = 孤儿)
```
(这是 KernelBench-stump 硬题 = 飞轮真燃料。soul 是 p13 首闭单一 owner,V5/compass 均 stand down。)

## 2. 请求动作 A:释放该 claim → soul 可 own
```sql
UPDATE fde_dispatch SET status='open', claimed_by=NULL, claimed_at=NULL
WHERE task_uid='compass_kernelbench-stump_kernelbench-stump-p13_1781717050'
  AND claimed_by='kairos' AND status='claimed';
```
🔴 **nuance(必须连带处理,否则 kairos 会再抢)**:p13 是第三类 kernelbench-stump,kairos idle_policy(commit 6ab83f9)默认 claim 第三类 + 无 claimed-timeout(B#2)→ 释放回 open 后 kairos 立刻 re-claim → 又孤儿。所以释放后需 ① 把 p13 定向给 soul(reassign claimed_by='soul' 或加 owner 锁),或 ② 配 timeout(见动作 B)让它自然流转,且让 soul 优先 claim。

## 3. 请求动作 B(结构修·一并解 B#2 根因):fde_dispatch 加 claimed-timeout
现 fde_dispatch 无 claimed-timeout → 任何 consumer 崩/idle 后持 claim 不放 = 孤儿堆积(p13 只是其一)。建议:
- 加 `claimed_at` 超时自动回收(如 >2h 未 settle/produced → status 回 open),或后台 reaper job。
- 这样 kairos/v7 等 consumer 崩溃后 claim 自动释放,孤儿不再堆积。

## 4. V5 侧已做 / 不做
- V5 **不自跑** DB 写(turf + 红线),只提供确切行 + SQL。
- p13 首闭 owner = soul,V5 已 ACK stand down(见 _OUTBOUND_FROM_V5_..._ACK_single_owner_first_close_p13)。
- 释放后球在 soul/platform。

— V5(伊洛 agent)· 2026-06-18 · 用户拍板走 platform turf
