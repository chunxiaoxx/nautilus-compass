---
name: orgfuel-ORGM-69e1062545ca92cb-75b7a0bd8a
description: "记忆条目 memgate-m5-deploy-lessons-20261008.md # M5 部署三课(2026-10"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-69e1062545ca92cb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 memgate-m5-deploy-lessons-20261008.md
# M5 部署三课(2026-10-08 · R369)

**交付**:记忆门三件套(fact_status/dedup_check/沿链一跳)+v2.5.1 coverage 披露进生产 9876;J4 gate GREEN;首卡 nautilus-l1-0002 同窗口 delivered。

**Why:** 三类陷阱都在"验证"环节误导,不在实现——探针环境与生产环境的行为差异是主旋律。

**How to apply:**
1. **inotify 环境差**:装有 inotify_simple 的 python 进程里 get_memory_entries 走 fast path(缓存 list 直接 return,不进 embed 段)——测试进程与 daemon 进程(无此包)同代码双行为。判定法:patch daemon.log 后调用,logs 全空=走了 fast path。冒烟/复算须在与生产同 env 下跑,或先确认 _INOTIFY_USE 值。
2. **EMBED_BUDGET 假 RED**:默认 COMPASS_EMBED_BUDGET=24 渐进消化(v3.0.9)——daemon 重启后冷文件 embedding=None 不可打分,J4 gate 老文件案必假 RED(排名整体存在但目标文件缺席,分数带 0.49-0.53 是缺席信号)。根修=`COMPASS_EMBED_BUDGET=200` 重启,首轮 dedup_check 触发全量嵌(155 条 490s),coverage 字段=进度表。暖机循环脚本轮询两小时不递进即停,别硬等。
3. **MSYS kill 假动作**:git-bash `kill <pid>` 对 nohup 起的
