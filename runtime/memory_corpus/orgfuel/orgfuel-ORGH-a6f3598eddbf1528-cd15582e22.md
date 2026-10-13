---
name: orgfuel-ORGH-a6f3598eddbf1528-cd15582e22
description: "commit 736b5ad69094 2026-05-06 Tier 1 · paper 2 投稿级 polish ·"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a6f3598eddbf1528
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 736b5ad69094 2026-05-06
Tier 1 · paper 2 投稿级 polish · 4 项
#2 bibtex · 加 hu2026evermembench · 修 wang→wu typo
#15 abstract · 280 → 189 词 · 顶会 ≤200 合规
#9  cost · 完整公式 · LLM API $1.40 + GPU $2.30 = $3.70
#8  figure 1 · pipeline_v08.pdf · TikZ 编译产物 · 替换 placeholder

附 · 修复 LaTeX 编译:
  · paper2_main.tex bibstyle plain → plainnat (natbib 兼容)
  · sections/*.tex 注释里的中文 unicode 替换为 [Chinese comment]
  · paper2_appendix_drift.tex 锚点示例译为英文 (typesetting)

最终 PDF · paper2_main.pdf 414K · 24+ 页 · 0 undefined citation/reference
