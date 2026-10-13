---
name: orgfuel-ORGG-81defb76f7350254-552faf485a
description: "判读档判例 FACT_STATUS_COVERAGE_20261009 · T5.5b 深度复核收官(2026-10-0"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-81defb76f7350254
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 FACT_STATUS_COVERAGE_20261009 · T5.5b 深度复核收官(2026-10-09 深夜 · 交接档悬置"剩余 61 条深度复核"闭环)
## T5.5b 深度复核收官(2026-10-09 深夜 · 交接档悬置"剩余 61 条深度复核"闭环)

- **方法**:measured 全量扫描(非抽样)——缩进兼容正则提取(🔴探针教训:库内标注缩进不齐,2 空格/1 空格/顶格三种并存,`^fact_status` 顶格锚会漏 54+36 条只读 6 条;初判"覆盖率仅 64/163"系探针自身 bug,先证伪自己后 grep 独立复核拨正)。
- **扫描**:measured 60 条 × 双特征过滤(分析类词命中 + 读数锚为零)→ 候选 2 条(no-jargon-user-correction / propagation-layer-order)→ **人工逐条判:均为用户拍板事件记录,measured 保持**。
- **结论:本轮零下调**(T5.5 已下调 2 条,累计下调 2/162;measured 侧无理论/推断误标残留)。
- **upgrade_path**:对单条标注有争议时,对照冷层原始 session jsonl 逐条仲裁(`.claude-backup-0714` 只读归档)。
- 交接档悬置项#2"剩余 61 条深度复核待做"——**销项**(深度复核=全量扫描+人工裁决,零下调即诚实终态;不为了"有产出"而硬找下调)。
