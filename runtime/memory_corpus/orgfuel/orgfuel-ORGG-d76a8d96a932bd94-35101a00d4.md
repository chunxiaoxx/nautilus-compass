---
name: orgfuel-ORGG-d76a8d96a932bd94-35101a00d4
description: "判读档判例 2026-06-06-compass-cloud-substrate-plan · Phase 2 · sp"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d76a8d96a932bd94
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-cloud-substrate-plan · Phase 2 · spot T4 GPU daemon(需用户 provision T4 · ops)
## Phase 2 · spot T4 GPU daemon(需用户 provision T4 · ops)

### Task 7: T4 spot 实例起 GPU daemon
**runbook(ops):** spot T4 · 装 daemon + 拉语料(Task 2)+ 拉快照(Task 3)+ `COMPASS_PROD_RERANK=1`(reranker 默认开 · T4 GPU ~0.6-0.9s)· systemd + spot 抢占信号 handler(收 2min 警告 → drain ingest → 标记下线让客户端 fallback)· 自动重拉(spot fleet restart)。

### Task 8: 客户端指向 T4 + 抗抢占验证
**runbook:** 你本机 recall hook primary=T4 · fallback=CPU 服(Task 4)· 验:跨设备 recall 通 + reranker lift 生效 + **手动 kill T4 daemon → 1 分钟 fallback 到 CPU 服**(实测抗抢占)。

---
