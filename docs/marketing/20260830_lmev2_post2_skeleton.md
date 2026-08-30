# 营销第二帖骨架 · LME-V2 三刀逆袭 · 2026-08-30(数字占位版)

> 定位:第一帖(r/LocalLLaMA 检索战绩)的续篇。素材=LME-V2 451 题从崩盘到翻盘的全过程。
> 🔴 全部 `⟦d13⟧`/`⟦d14⟧`/`⟦LME-S⟧` 占位符等定案报告填终值;发布动作需用户拍板。
> 原则同第一帖:数字开路 + 方法透明 + 失败实验公开 + 诚实成本段。

---

## 故事线(技术社区最吃的"我们搞砸了然后修好了"叙事)

**开头钩子**:First post we showed retrieval wins. This one is about what happened when we ran a harder benchmark and scored **19.6%** — and the three fixes that took it to ⟦d12: 36.7%⟧ (web) and **12.8% → ⟦d12: 40.3%⟧** (enterprise), with ⟦d13/d14 终值⟧ after domain-adapting the embedder.

### Act 1 · 崩盘(不藏丑)
- LongMemEval-V2: 451 questions, real agent-trajectory haystacks (web browsing / ServiceNow), open benchmark with published baselines
- First full run: web 19.6% / ent 12.8% — far below published numbers
- 逐题对齐 evidence(不是猜):252 answers were bare `UNKNOWN` scored 0;enterprise had an inversion — gold WAS in the retrieved window, reader scored 0.115 when it was present

### Act 2 · 三刀(每刀一个根因,每刀一个可复算数字)
1. **Knife 1 — scoring alignment**: 30% of the benchmark is abstention-type; judge rubric rewards "explain the contradiction" or "state you can't verify live state", not bare UNKNOWN. Rewrote the system prompt. Abstention score rate: web 2.8%→45.8%, ent 0%→83.9%. Bare UNKNOWN: 252 → 0.
2. **Knife 2 — retrieval unit upgrade**: prune empty a11y structural lines + per-trajectory dense reranking + budget 12000→24000 chars. Gold-present scoring rate: ent 0.115→0.652 (the inversion was an ordering/vision problem, not a recall problem).
3. **Knife 3 — embedder domain adaptation**: mined 88 contrastive pairs from 568 rejected trajectories + LoRA on q/k/v (0.41% params, ~2h on one GPU). Guard recall@5 0.533→0.733. Full-benchmark: ⟦d13/d14 终值⟧.

### Act 3 · 诚实段(第一帖同款)
- **Cost is real**: tokens +63~72% (budget doubling) — we publish the token counts, not just accuracy
- **Judge dependence**: abstention scoring relies on judge rubric; cross-system comparison must lock the same judge & criteria
- **What broke**: our knife-1 fix over-generalized — the model started refusing on questions the snapshots COULD answer (3 dynamic questions flipped 1.0→0.0). Fixed with an explicit gate ("if any snapshot shows the state, you MUST answer"). ⟦d14 验证终值⟧
- **Disaster-forgetting check**: LoRA on trajectory domain did NOT hurt dialogue-domain retrieval (recall@8 0.950→0.950, overlap 0.958); full e2e regression ⟦LME-S 终值 vs 基线 0.567⟧
- 1 question scored 0 due to endpoint timeouts (network, not model) — disclosed

### 预注册文化段
- Every knife had pre-registered criteria written BEFORE the run (commit 9ff3a0d is public); we didn't move the goalposts after seeing numbers
- 12-question-subset lesson from post #1 applied: no belief until full-set rerun

## X thread 第 1 条(短钩子)

> We scored 19.6% on LongMemEval-V2. Published baselines said we should be near 30+.
> Instead of tweaking the demo, we aligned every wrong answer against the evidence and found 3 root causes.
> Three knives later: ⟦终值⟧. Full breakdown 🧵

## 发布前 checklist
- [ ] d13/d14 定案数字填入(占位符全部替换)
- [ ] LME-S 回归终值填入(判据 4)
- [ ] evidence 路径与 repo 对齐(README 链接终审)
- [ ] 跨系统对比口径声明(judge 锁定声明)
- [ ] 用户拍板(对外发布纪律)
