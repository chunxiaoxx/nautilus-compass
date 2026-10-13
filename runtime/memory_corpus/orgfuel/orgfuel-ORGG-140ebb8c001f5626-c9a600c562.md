---
name: orgfuel-ORGG-140ebb8c001f5626-c9a600c562
description: "判读档判例 DEADLINE_RUNBOOK_20261009 · 夜班终态补记(2026-10-08 深夜 · R37"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-140ebb8c001f5626
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 DEADLINE_RUNBOOK_20261009 · 夜班终态补记(2026-10-08 深夜 · R376 实测)
## 夜班终态补记(2026-10-08 深夜 · R376 实测)

- pull_batches **21/30 OK 后 GUARD 自停**(avail=23G<25G,#22 精确触发)——护栏语义验证通过;
- 磁盘 148G/178G(余 23G);剩余 9 镜像待扩容后重跑脚本补拉(均值 1.9G,~17G,280G 盘零压力);
- 晨检命令不变(tail log+images 计数+df);扩容 a/b 拍板后按 01 节切换。
