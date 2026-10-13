---
name: orgfuel-ORGG-f43e35eddc047d7c-8107be31ad
description: "判读档判例 2026-07-08-flagship-closure-and-docs-design · ② drift "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f43e35eddc047d7c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-08-flagship-closure-and-docs-design · ② drift 拦截环 · 真实缺口 = 检测器 52% 误报(不是接线)
## ② drift 拦截环 · 真实缺口 = 检测器 52% 误报(不是接线)
- 已闭合:auto_ack 接线,act-on 可测 0.178。
- **缺口**:152 acks 里 **79 = fp**(52%)→ agent 理性 tune out → act-on 上不去。降 act-on↔降 fp 是同一件事。
- **设计(fresh session · 真工程)**:
  1. 分析 79 个 fp 的 embedding 模式(哪些正/负锚点误触)。
  2. 调 25 正/35 负锚点 或阈值(NEG_ANCHOR 0.538 / COSINE_MIN 0.35)。
  3. **held-out 复验**:`eval_drift_holdout.py` 跑,断言 AUC 不低于 0.83 baseline(防为降 fp 牺牲召回)。
  4. 目标:fp 率下降 + AUC 保持 → act-on 自然上行。**不承诺 0.70**(那取决于 agent 行为,非纯代码可保证)。
- 🔴 **R3**:此项在 marathon session 尾部不做,fresh session 带此设计执行。
