---
name: orgfuel-ORGH-4767239741a294b0-beae7b814e
description: "commit 2fb66cc96350 2026-07-17 fix(bmb): 提交前对照买方文档全面审查 + 修正 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-4767239741a294b0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2fb66cc96350 2026-07-17
fix(bmb): 提交前对照买方文档全面审查 + 修正 5 处(正式交付就绪)
对照《BioMysteryBench 数据要求【外部】》+ qes1 样例逐条审查,修:
- F1 问题去具体工具产品名(VEP/ClinVar/BLAST)→ 用工具类别措辞,保'模型自主选工具链'难度,合买方风格
- F2 VCF 变异 18→30 消'难度过低'退回风险(远程盲解 60 次交互/唯一=1 确认)
- F3 allowed_domains 补全 14 白名单(对齐 qes1)
- F4 答案格式统一 GENE|Condition
- F5 data zip 改纯数据(去 README,对齐 qes1)
- 全部复验:合并 3 题 0 REJECT/0 WARN;#1/#2 本地 QC 致病唯一=1;#1 远程盲解 60 交互
- DELIVERY_NOTES 加逐条对照审查表;dead code 清理
