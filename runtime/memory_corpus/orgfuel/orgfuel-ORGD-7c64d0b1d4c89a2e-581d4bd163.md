---
name: orgfuel-ORGD-7c64d0b1d4c89a2e-581d4bd163
description: "[## 切片 A · verdict 数据订正 + 口径解耦(齿轮③·先做·关键路径)] - 判据=分两类:① 难倒门 "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-7c64d0b1d4c89a2e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 切片 A · verdict 数据订正 + 口径解耦(齿轮③·先做·关键路径)] - 判据=分两类:① 难倒门 pass(buyer stump 验收·pass@5≤0.6=合格)≠ ② 解对 pass(solver correctness)。这两套语义当前混用同一 overall_pass。
- `levenshtein/regex/golf`:note 明写难倒门→若作买方难倒题,overall_pass=t 合理,**保留**(标注 verdict_kind='stump_gate')。
- `aes128_ctr/hash_join/fft_rust`:threshold_met=false 却 pass·note 仅 batch1·**来源不明 → 与 bvh 同批订正**(SELECT 确认后,若非难倒门语义则 overall_pass=f)。
- 产物:不改代码(无写入器),而是**在 verdict 上加 `verdict_kind` 标注口径**(若 schema 允许)或写一份口径备忘 `docs/verdict_semantics_stump_vs_correctness.md`,供未来 ingest 分流。
