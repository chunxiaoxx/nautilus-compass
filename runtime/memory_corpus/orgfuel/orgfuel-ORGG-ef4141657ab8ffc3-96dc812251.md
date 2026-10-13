---
name: orgfuel-ORGG-ef4141657ab8ffc3-96dc812251
description: "判读档判例 2026-05-29-compass-comprehensive-uplift-design · 0. Co"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ef4141657ab8ffc3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-05-29-compass-comprehensive-uplift-design · 0. Context · 本次 design 的触发
## 0. Context · 本次 design 的触发

今天一个 session 内:

1. Sprint 0 baseline 2/5 placeholder → measured · v2.0.1 跑分:
   - **MEME Cas/Del/Abs n=500 · acc=45.6% · recall@30=97.4%** · paper Table 4 reported baselines 第一 (+3.05pp vs MemOS)
   - **LongMemEval-S n=500 · retrieval P@5=0.932 / MRR=0.8585** · vs v0.8 +7.2pp/+17.4pp · 大幅超原 plan "near-zero delta" 预测
   - LongMemEval-S overall acc=0.364 (Gemini-2.5-pro judge · NOT 直接对比历史 56.6% GPT-4o-mini)

2. 实测 dormant differentiation:
   - PoI emit events: **0** (`.cache/poi_emit.jsonl` 不存在)
   - impact_event_count > 0 sessions: **2/1424 = 0.14%**
   - cross-agent contracts consumed: **0** (2 expired in alerts file)
   - drift detection: 25k+ events / act-on rate ≈ 0% (5/27 s
