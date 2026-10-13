---
name: orgfuel-ORGM-lmev2-first-full-baselin-45b8550fb2
description: "--- name: lmev2-first-full-baseline-20260830 description: LM"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-lmev2-first-full-baselin
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: lmev2-first-full-baseline-20260830
description: LME-V2 small tier 451 题首次全量基线——web 19.6%/ent 12.8%(doubao 口径一致 e2e500);短板=static/dynamic unknown 55-67% 检索适配未调优;evidence 在 vtf/_compass_lmev2_out
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-08-29T23:20:04.195Z
---

# LME-V2 首次全量基线(2026-08-30 · GPU 651799)

**数字(N5② evidence · commit 已入库)**:451 题 = web 240(**19.6%** overall / 26.8% 实答)+ enterprise 211(12.8% / 17.4%)。拒答率 ~28%。分类型(web 实答):procedure 52.4% > gotchas 46.7% >> dynamic 17.6% > static 11.7%;static/dynamic 的 **unknown 率 55-67% = 检索未召回**(多 session haystack 的 chunk/路由适配未调优),非 reader 拒答癖。

**口径**:reader+judge = doubao-seed-2-0-pro-260215 @ ARK(与 e2e 500 同款 subject,营销一个故事);compass_chunk_hybrid bge-m3 cuda
