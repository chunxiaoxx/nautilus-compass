# 营销第一帖 · v2 2026-08-30(e2e 段换 500 题全量口径)

> 主阵地 r/LocalLLaMA(英文技术长帖)+ X thread。弹药:四战场检索战绩(全部可复算)。
> 发布前 checklist:README 双语已重构✅ · 落地页已更新✅ · HF demo 数字已更新✅ · MCP 公网 404 已修✅ · **e2e 全量口径已对齐 README(42.6%)✅**
> 帖子原则:数字开路 + 方法透明 + 失败实验公开 + e2e 诚实段(技术社区最吃这套)。
> 🔴 发布动作需用户拍板(对外发布纪律)。

---

## A. r/LocalLLaMA 主帖(英文)

**Title:**
We beat mem0 on LongMemEval-S retrieval (+11.6pt P@1, full 500 questions) with a fully local memory layer — no LLM extraction, no data egress, ~$3.50 to reproduce

**Body:**

We've been building an open-source memory layer for agents (nautilus-compass) and just finished a head-to-head against mem0 2.0.19 (latest PyPI) on four benchmarks. All numbers are from identical questions, identical judge criteria, and reproducible from the evidence files in the repo.

**Head-to-head results (retrieval layer):**

| Benchmark | compass | mem0 2.0.19 | Δ |
|---|---|---|---|
| LongMemEval-S · 500 q · P@1 | **0.890** | 0.774 | +11.6pt |
| LongMemEval-S · P@5 | **0.978** | 0.916 | +6.2pt |
| LongMemEval-S · MRR | **0.929** | 0.834 | +9.5pt |
| LOCOMO-10 · n=1986 · P@1 (mem0's home turf) | **0.644** | 0.592 | +5.2pt |
| LongMemEval-M · 500 q · P@5 (12× corpus) | **0.888** | — | generalizes |

On EverMemBench-Dynamic (n=500), compass scores 44.4–47.3% vs Mem0 37.09 / Zep 39.97 / MemOS 42.55.

**The design bet: don't call an LLM at write time.**

compass stores session text verbatim, embedded locally with BGE-m3. No LLM extraction into "facts", no graph, no cloud calls. Memory writes are free and lossless; all the intelligence lives at read time:

1. **Utterance-type routing** — questions are classified (single-session-user / multi-session / temporal / knowledge-update / ...) and each type gets a different retrieval unit. User-utterance questions retrieve *turn-level chunks* (sliding window of 2), not whole sessions. This single change took single-session-user P@1 from 0.20 → 1.00 on held-out runs.
2. **Hybrid BM25 + dense with RRF fusion** — dense alone drops temporal/multi-session queries; lexical carries exact identifiers (dates, names, versions).
3. **Date anchoring** — session dates are prefixed into chunk text so "before/after" queries have temporal handles.

**What didn't work (also in the repo):**

- Cross-encoder reranking on retrieved chunks: *hurt* accuracy (-2pt). The embedder's ordering was already better.
- Retrieval depth K=50 vs K=20: no difference. Precision matters, not recall padding.
- Swapping in a smaller/faster embedder: no.

Every experiment above has its full run log in `docs/evidence/` in the repo — including the 12-question subset that initially showed +16.7pt (sampling bias, all one question type; we re-ran at 30 mixed questions before believing it).

**Honest e2e story (full 500 questions):** end-to-end QA over the full LongMemEval-S 500-question set, same questions/same judge: **42.6% (213/500)**, and the per-type breakdown is the real story — single-session types are near ceiling (**single-session-user 95.7% · single-session-assistant 80.0% · knowledge-update 73.1%**) while cross-session aggregation types lag (**multi-session 22.6% · single-session-adversarial 25.0% · temporal 15.8%**, up from 0% after a date-anchor fix). The bottleneck was never recall (retrieval P@5 97.8%) — it was reader context: answers spread over 3+ sessions exceed our 3-utterance context window, and that's our public next lever. On a 30-question paired run the same fix showed 0.267 → 0.567 (+30pt); we re-ran the full 500 before believing any headline number (our 12-question subset once showed +16.7pt — sampling bias, all one question type). We publish both tiers because "retrieval SOTA" claims without the reader context are how this field gets burned.

It also does two things beyond recall: pre-action **drift detection** (checks agent actions against failure-mode anchors, AUC 0.83, p95 <50ms) and **cross-agent contracts** (tracks implicit obligations when multiple agents share files).

30-second hookup (Claude Code, local daemon — everything stays on your machine):

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
bash ~/.claude/plugins/nautilus-compass/install.sh
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

Cursor / Cline / Continue.dev / Zed: `python scripts/install_to_agent.py`.
No local install: hosted gateway at compass.nautilus.social.

Repo (MIT, bilingual README): https://github.com/chunxiaoxx/nautilus-compass
Landing: https://compass.nautilus.social

Happy to answer questions on the retrieval routing design or the failure experiments — those are the fun parts.

---

## B. X thread(中文,7 条)

1. 开源 agent 记忆层 compass 在 LongMemEval-S 全 500 题上检索三项全面超过 mem0:P@1 0.890 vs 0.774(+11.6pt),P@5 0.978,MRR 0.929。同题同判据,证据链开源。🧵
2. 关键设计赌注:写入时不调 LLM。原文本地 BGE-m3 嵌入,零抽取、零上云、零写入成本。智能全部在读侧。
3. 读侧三武器:①utterance 分型路由(单会话用户型问题检索 turn 级块,该型 P@1 0.20→1.00)②BM25+dense RRF 混合③日期锚定。
4. 失败实验同样公开:rerank 有害(-2pt)、K=50 无效、小模型无效。12 题 +16.7pt 的初读是抽样偏差,30 题混合后修正。全部证据在 repo docs/evidence/。
5. 客场也赢:LOCOMO(mem0 主场)n=1986,P@1 0.644 vs 0.592。大语料(12×)泛化 P@5 0.888。EverMemBench 超 Mem0/Zep/MemOS。
6. e2e 全量 500 题定案 42.6%:单会话型近满分(ssu 95.7/ssp 80.0/ku 73.1),跨会话聚合型是短板(ms 22.6/ssa 25.0/tr 15.8,tr 曾为 0,日期锚定修复后翻盘)。检索 P@5 本来就 97.8%——差距从来不在召回,在 reader context 装不下跨会话答案。两个数都公布。
7. 附赠:drift 检测 AUC 0.83(动作前对照失败模式锚点)+ 跨 agent 合约审计。三条命令接入 Claude Code,Cursor/Cline 一条脚本。MIT。github.com/chunxiaoxx/nautilus-compass

---

## C. 发布节奏

1. r/LocalLLaMA 周二-周四 9-11am ET(技术帖黄金窗)
2. X thread 帖发后 2h 内(互相导流)
3. r/LocalLLaMA 评论区 24h 内必回(算法权重)
4. 第二帖素材已就绪:e2e 全量分型专题(单会话近满分 vs 跨会话聚合短板,修复杠杆明确);LongMemEval-V2 首次全量基线已出(8/30,web 19.6%/enterprise 12.8%,多 session 检索适配未调优)——V2 不进首帖,作第二帖"新基准线+优化"叙事素材。
