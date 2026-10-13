---
name: orgfuel-ORGG-bfe817a6cf9ac68b-cf2f566fef
description: "判读档判例 2026-06-06-compass-cloud-substrate-plan · Phase 1 · CP"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-bfe817a6cf9ac68b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-cloud-substrate-plan · Phase 1 · CPU 服冷备 + ingest 写路径(需 CPU 服 sudo · 用户 ops)
## Phase 1 · CPU 服冷备 + ingest 写路径(需 CPU 服 sudo · 用户 ops)

### Task 5: CPU 服冷备 daemon systemd(冷备 · 抢占触发)
**runbook(非 TDD · ops):** CPU 服装 compass daemon(CPU 模式 · `ZMM_DEVICE=cpu`)· systemd unit `compass-daemon-fallback.service`(`WantedBy` 手动/触发 · 非 always · 守内存:实测箱子已 swap → 平时不启)· 健康端点。验:手动 `systemctl start` → 1 分钟内 recall 可服(载 bge-m3 ~1.7G · 那时 available 8.7G 够)。

### Task 6: ingest 统一写云(单写权威)
**Files:** Modify stop-hook ingest + agent ingest → 都打云 daemon ingest API(非本地写)· Test。
- TDD:mock ingest API → 断言写转发 + 本地不再独立写语料(消灭多写)。
- Commit。

---
