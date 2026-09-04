# 营销第二帖骨架 · LME-V2 三刀逆袭 · 2026-08-30(终值已填 9/4)

> 定位:第一帖(r/LocalLLaMA 检索战绩)的续篇。素材=LME-V2 451 题从崩盘到翻盘的全过程。
> 9/4 填数:d13/d14 终值已从定案报告落位(`vtf/_compass_lmev2_out/d13/D13_FIXATION_20260831.md` + `d14_verdict_20260902.md`);剩 cheap-tier 数字可选回填。发布动作需用户拍板。
> 原则同第一帖:数字开路 + 方法透明 + 失败实验公开 + 诚实成本段。

---

## 故事线(技术社区最吃的"我们搞砸了然后修好了"叙事)

**开头钩子**:First post we showed retrieval wins. This one is about what happened when we ran a harder benchmark and scored **19.6%** — and the fixes that took it to **40.0%** (web) and **12.8% → 38.4%** (enterprise). Honest epilogue: a third of the lift came from finding our own judge was broken (4096-token budget silently eaten by reasoning, systematically zeroing answers — full re-judge moved web 36.7→40.0, ent 40.3→38.4); the LoRA embedder adaptation closed at parity and was NOT adopted; an abstention-gate patch was rejected by preregistered criteria. Tuned-v2 stack is the one that ships.

### Act 1 · 崩盘(不藏丑)
- LongMemEval-V2: 451 questions, real agent-trajectory haystacks (web browsing / ServiceNow), open benchmark with published baselines
- First full run: web 19.6% / ent 12.8% — far below published numbers
- 逐题对齐 evidence(不是猜):252 answers were bare `UNKNOWN` scored 0;enterprise had an inversion — gold WAS in the retrieved window, reader scored 0.115 when it was present

### Act 2 · 三刀(每刀一个根因,每刀一个可复算数字)
1. **Knife 1 — scoring alignment**: 30% of the benchmark is abstention-type; judge rubric rewards "explain the contradiction" or "state you can't verify live state", not bare UNKNOWN. Rewrote the system prompt. Abstention score rate: web 2.8%→45.8%, ent 0%→83.9%. Bare UNKNOWN: 252 → 0.
2. **Knife 2 — retrieval unit upgrade**: prune empty a11y structural lines + per-trajectory dense reranking + budget 12000→24000 chars. Gold-present scoring rate: ent 0.115→0.652 (the inversion was an ordering/vision problem, not a recall problem).
3. **Knife 3 — embedder domain adaptation**: mined 88 contrastive pairs from 568 rejected trajectories + LoRA on q/k/v (0.41% params, ~2h on one GPU). Guard recall@5 0.533→0.733 held — but full-benchmark transfer closed at **parity**: ent +0.46pt / web −0.03pt vs d12, both far below the preregistered +5pt gate → **NOT adopted**. (Retrieval-metric gains that don't move end-to-end QA are not gains; that's the whole reason we gate on the benchmark, not the proxy.)

### Act 3 · 诚实段(第一帖同款)
- **Cost is real**: tokens +63~72% (budget doubling) — we publish the token counts, not just accuracy
- **Judge dependence**: abstention scoring relies on judge rubric; cross-system comparison must lock the same judge & criteria
- **What broke**: our knife-1 fix over-generalized — the model started refusing on questions the snapshots COULD answer (3 dynamic questions flipped 1.0→0.0). Fixed with an explicit gate ("if any snapshot shows the state, you MUST answer"). The next gate candidate (d14, a preregistered abstention patch) was **rejected by its own criteria**: false refusals hit 92 (web) / 89 (ent) questions against a ≤1/≤2 gate, and non-abst web lost 5 questions — 95% of the newly-refused questions were ones d12 already got wrong, i.e. wrong answers collapsed into refusals instead of being fixed. d12 + the prompt-level gate is what ships.
- **Disaster-forgetting check**: moot for the shipped stack — the LoRA was never adopted, so there is no dialogue-domain regression surface in production; trial evidence kept for the record (dialogue-domain recall@8 0.950→0.950, overlap 0.958)
- 1 question scored 0 due to endpoint timeouts (network, not model) — disclosed

### 预注册文化段
- Every knife had pre-registered criteria written BEFORE the run (commit 9ff3a0d is public); we didn't move the goalposts after seeing numbers
- 12-question-subset lesson from post #1 applied: no belief until full-set rerun

## X thread 第 1 条(短钩子)

> We scored 19.6% on LongMemEval-V2. Published baselines said we should be near 30+.
> Instead of tweaking the demo, we aligned every wrong answer against the evidence and found 3 root causes.
> Three knives later: **40.0% (web) / 38.4% (ent)** — and two knives we killed ourselves (LoRA at parity, abstention gate over-refusing). Full breakdown 🧵

## 发布前 checklist
- [x] d13/d14 定案数字填入(9/4,占位符全部替换,来源两份定案报告)
- [x] LME-S 回归终值填入(判据 4)→ 改判 moot(LoRA 未采纳,无回归面)
- [x] 跨系统对比口径声明(judge 锁定:doubao-seed-2-0-pro-260215 · low/16384 · ARK coding 端点,重判修正后)
- [ ] evidence 路径与 repo 对齐(README 链接终审)
- [ ] cheap-tier raw-state 数字可选回填(跑分中,落地后决定进不进本帖)
- [ ] 用户拍板(对外发布纪律)
