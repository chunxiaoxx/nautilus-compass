---
name: orgfuel-ORGM-0a3948b4204db448-be9b4325a8
description: "记忆条目 session_20260718-1201_drift护城河实测0-92-不需ARK.md # drift护城"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-0a3948b4204db448
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 session_20260718-1201_drift护城河实测0-92-不需ARK.md
# drift护城河实测0.92·不需ARK

## 上下文
compass 唯一真护城河 drift 当前 live 实测 AUC 0.9232(anchor集,本地BGE,零LLM);冻结held-out本机缺失需LLM-judge重造(ARK唯一正当用途)

## 内容
7/18 实测 compass 护城河(接"lifecycle 层用 MRR 是错尺子"之后,验唯一真差异化 drift 现在硬不硬):
- tests/eval_drift.py(自包含·50 aligned+50 deviation·anchor集·本地 bge-m3·零 LLM):**ROC AUC=0.9232**,default thr -0.032 precision 0.851/recall 0.800/acc 0.830,best Youden acc 0.840。→ drift 护城河当前强。
- 诚实界:0.92 是 anchor 集(in-distribution,偏乐观);uncontaminated 冻结 held-out(历史 0.83)= eval/holdout_v1.json 本机**缺失**,--generate 需 LLM-as-judge(原 Vertex Gemini)。

ARK 判断(用户给 b8ed1f14 key + doubao2.0pro/Seed-Evolving/GLM5.2):
- compass 核心零-LLM=护城河,不接 ARK。
- 撤回上轮"poi 下游 ARK 对比"提议:grounded 查本地 cumulative_impact 全 0 → poi rerank==flat → A==B 空实验(反D 剧场)。
- ARK 对
