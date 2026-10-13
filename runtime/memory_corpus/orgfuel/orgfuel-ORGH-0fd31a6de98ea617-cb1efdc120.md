---
name: orgfuel-ORGH-0fd31a6de98ea617-cb1efdc120
description: "工具决策记录 e1_final_eval.py E1-TUNE 终局评测(R442): v2 干净工作集 × 三配置正式"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-0fd31a6de98ea617
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 e1_final_eval.py
E1-TUNE 终局评测(R442): v2 干净工作集 × 三配置正式定谳读数。

格1 基线:  原始语料 + bge-m3 alone
格2 H2:    原始语料 + bge-m3 + rerank
格3 组合:  合并语料(150) + bge-m3 + rerank
gold 含被并文件时 REMAP 到保留者(R438 同表)。输出 e1_final_verdict.json。
