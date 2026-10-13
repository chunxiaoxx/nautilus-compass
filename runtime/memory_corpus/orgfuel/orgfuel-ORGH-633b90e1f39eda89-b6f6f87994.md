---
name: orgfuel-ORGH-633b90e1f39eda89-b6f6f87994
description: "工具决策记录 e1_calib60_kappa.py calib60 汇总:人类标定 vs 判官读数一致率+Cohen'"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-633b90e1f39eda89
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_calib60_kappa.py
calib60 汇总:人类标定 vs 判官读数一致率+Cohen's κ+分歧归因清单。

输入:作答表填毕的 ANSWER_SHEET_filled.md(或 CSV)+ sample_manifest.json(判官读数区)。
门槛(预备档建议,组织方裁):一致率>=80%(κ>=0.6)→判官读数获人类标定背书;
<80%→分歧题逐题归因(判据二义/判官错/材料歧义三类)报告先出再议。
用法:python tools/e1_calib60_kappa.py <filled_sheet.csv>
