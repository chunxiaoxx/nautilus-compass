# 营销第一帖 · 2026-08-27

> 主阵地 r/LocalLLaMA(英文技术长帖)+ X thread。弹药:四战场检索战绩(全部可复算)。
> 发布前 checklist:README 双语已重构✅ · 落地页已更新✅ · HF demo 数字已更新✅ · MCP 公网 404 已修✅
> 帖子原则:数字开路 + 方法透明 + 失败实验公开 + e2e 诚实段(技术社区最吃这套)。

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

**Honest e2e story (with the fix):** end-to-end QA pairs, same questions/same judge: baseline 0.267 → **0.567 (+30pt, 2.13x)** after we found the real bottleneck — a 600-char context truncation that cut off the answer turn. The fix (question-type-routed utterance context + anchoring all turns for assistant-type questions) took single-session-user from 0.00 → 1.00 and single-session-assistant from 0.00 → 0.80. Retrieval P@5 was already 97.8% — the gap was never recall. Remaining: temporal-reasoning e2e still 0 (diagnosis queued). We publish both numbers because "retrieval SOTA" claims without the reader context are how this field gets burned.

It also does two things beyond recall: pre-action **drift detection** (checks agent actions against failure-mode anchors, AUC 0.83, p95 <50ms) and **cross-agent contracts** (tracks implicit obligations when multiple agents share files).

30-second hookup for Claude Code / Cline / Cursor / Continue.dev / Zed via MCP:

```
bash ~/.claude/plugins/nautilus-compass/ops/agent_quickstart.sh my-agent
```

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
6. e2e 翻倍故事:同题同判据配对 0.267→0.567(+30pt)。根因是 600 字符 context 截断把答案 turn 切掉,分型 utterance context 修复后单会话用户型 0→满分。检索 P@5 本来就 97.8%——差距从来不在召回。
7. 附赠:drift 检测 AUC 0.83(动作前对照失败模式锚点)+ 跨 agent 合约审计。MCP 30 秒接入 Claude Code/Cursor/Cline。MIT。github.com/chunxiaoxx/nautilus-compass

---

## C. 发布节奏

1. r/LocalLLaMA 周二-周四 9-11am ET(技术帖黄金窗)
2. X thread 帖发后 2h 内(互相导流)
3. r/LocalLLaMA 评论区 24h 内必回(算法权重)
4. 第二帖(e2e 修复专题/LongMemEval-V2 上榜)素材已就绪:e2e +30pt 配对定案已可并入首帖;V2 数字等 GPU 跑完
