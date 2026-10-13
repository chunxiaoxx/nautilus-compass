---
name: orgfuel-ORGH-bf1f9d63293c2a24-037a7f4705
description: "commit c82663c85333 2026-07-17 fix(bmb): 收买方反馈,题干改 qes1 自然简洁"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-bf1f9d63293c2a24
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit c82663c85333 2026-07-17
fix(bmb): 收买方反馈,题干改 qes1 自然简洁风格(去 AI 感/模板化)
买方反馈:题目描述有 AI 感+模板化,要像原 BioMysteryBench(qes1)自然简单语言、无背景介绍。
- 三题题干重写为一句直问(qes1 风格),去掉全部背景铺垫/工具说明/GENE|Condition 格式模板
  · #1 'One variant in this VCF is pathogenic for a Mendelian disorder — which gene is it in, and what is the disorder?'
  · #2 'This sample has a single variant that is pathogenic for an inherited disorder. Name the affected gene and the disorder it causes.'
  · #3 'One of these protein sequences is a lysosomal enzyme — which gene encodes it, and what disorder does its deficiency cause?'
- VCF 题干池跨题轮换措辞治'模板化';rubric 也精简为 qes1 风格(值+别名+全对全错)
- bmb_validator 按买方偏好校准:不再对自然题干误报 no_tool/no_answer_format(工具靠真解坐实/格式靠 rubric)
- 复验:0 REJECT/0 WARN;唯一性=1;数据未变(仅题面)解题性不受影响
