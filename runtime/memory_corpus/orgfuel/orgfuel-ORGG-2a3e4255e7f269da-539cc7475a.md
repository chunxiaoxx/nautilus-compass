---
name: orgfuel-ORGG-2a3e4255e7f269da-539cc7475a
description: "判读档判例 2026-06-03-poi-central-ledger-design · 5. 横切 P0(三方审查命中"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-2a3e4255e7f269da
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-poi-central-ledger-design · 5. 横切 P0(三方审查命中,无论方案都纳入)
## 5. 横切 P0(三方审查命中,无论方案都纳入)

1. **`derive_memory_key(project, filename)` 单一函数** — 当前 candidate 只带纯文件名,project 不在数据里(reconciler 环境变量隐式注入)。三处(本地 emit / 云端 inline 副本 / boost 查表)调同一函数 + 契约测试钉死「本地与云端副本同输入同输出」。candidate JSONL 加 `project` 字段,`pull_cloud_candidates.py` 透传。
2. **NaN/inf 兜底** — `float("nan")` 不抛异常,`clamp(nan)` 污染,`sort` 用 NaN 比较打乱整个 top-K。`_parse_cumulative_impact` 后 `if not math.isfinite(v): return 0.0`;boost 后 `if not math.isfinite(boosted): boosted = cosine`。clamp `[-0.5, +1.0]` floor/cap 随快照迁移并单测钉死。
3. **快照原子写** — 见 4.3。
4. **M1 guard 语义迁移** — 现「本地文件存在才 settle」会让只存在于云端的 memory 永远 `exists()==False` → 复活 settled=0。settle 真相落点从 frontmatter 改为 DB UPSERT;幂等护栏从文件系统移到 settled_keys(Phase 1)/ 云端键表(Phase 2)。文件存在与否不再是 se
