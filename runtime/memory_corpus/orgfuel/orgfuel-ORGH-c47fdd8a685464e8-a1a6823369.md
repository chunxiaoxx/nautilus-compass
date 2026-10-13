---
name: orgfuel-ORGH-c47fdd8a685464e8-a1a6823369
description: "commit 2fb06363f554 2026-06-21 feat(gear5): memory_bridge — "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c47fdd8a685464e8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2fb06363f554 2026-06-21
feat(gear5): memory_bridge — 飞轮 sqlite learning 沉淀成胶囊并入文件语义库(治split-brain第一刀)
split-brain根因:Store A(sqlite飞轮/v1/recall)↔Store B(文件语义库/v1/v14/recall)无桥接。
本模块=单向桥:飞轮obs(过W1晋升门reward≥1.0)→v14_ingest_obs body→写文件语义库为胶囊。
复用现有(anchor#5):W1晋升门+revoke tombstone+ingest_obs契约·不重造store。
纯逻辑+注入ingest_fn·14 TDD绿。服务conductor(质量pulse→可语义召回)。
live(读真sqlite ob_fw+POST ingest_obs+consolidation runner)gated on ssh.
