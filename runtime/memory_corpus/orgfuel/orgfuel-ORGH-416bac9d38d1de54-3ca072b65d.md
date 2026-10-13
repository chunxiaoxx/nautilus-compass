---
name: orgfuel-ORGH-416bac9d38d1de54-3ca072b65d
description: "commit 38b0a2b8646c 2026-07-16 docs(fde): BioMysteryBench 50"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-416bac9d38d1de54
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 38b0a2b8646c 2026-07-16
docs(fde): BioMysteryBench 500 题规模化生产设计(路 A)
甲方要 500 题·手工每题 20-30min 不可行。设计=反向推理模板 × 真数据集库 ×
自动化产-验管线(~10-12 模板 × ~40-50 实例=500)。钥匙:难度来自模型摸不出
工具链非算力→验证可自动化难度守住。铁律:优先小数据模板(避 721MB FASTA)、
跨 8 类型防单调、NCBI 限速、每模板抽样真解验难度。分 5 阶段 P1 证 1 模板起。
工厂将来招专家复用。

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
