# 营销第一帖 · v3 2026-09-04(A 臂 PASS 刷新 e2e 段 + 开放自助上线刷新 hosted 段)

> v2→v3 变更:①e2e 段从"42.6% + 短板是公开下一步"→ 追加摘要层终判(70.0 保守/81.6 干净,预注册判据)②hosted 从裸 gateway → 开放自助 signup + scoped token + 四探针背书③X thread 条 6 同步。其余段落沿用 v2。
> 🔴 发布动作需用户拍板(对外发布纪律)。发布窗口 9/12 前。
> 发布前刷新清单:
> - [x] d14 刀4:未过门(2026-09-02 定案)→ 维持 d12 现役
> - [x] d12 干净口径定案:web 40.0% / ent 38.4%(主帖正文无 LME-V2 数字,在第二帖)
> - [x] e2e 段刷新:9/3 A 臂终判 PASS + 9/4 #40 断连重判补齐,定案 75.4%(377/500,每题有真判决)/81.6%(同口径剔除断连 71 题);42.6 为基线锚,正文双报
> - [x] cheap-tier 定案 36.3/36.5 双域未超现役组合关闭(9/4)→ 主帖不放,第二帖填(SCOREBOARD 已录)
> - [ ] paper2 arXiv 链接回填(提交后)
> - [x] 终检 9/6:帖子数字与 README/落地页逐项对照一致(0.890/0.978/0.929 · 0.774/0.916/0.834 · 0.644/0.592 · 42.6→75.4/81.6 · 三弱型双口径 ms 69.2/73.2 · ssa 83.9/85.4 · tr 62.4/83.3)

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

**The reader-context bottleneck — fixed, with preregistered gates.** Our first full-500 e2e run scored 42.6%: single-session types near ceiling (single-session-user 95.7% · single-session-preference 80.0% · knowledge-update 73.1%) while cross-session types lagged (multi-session 22.6% · single-session-assistant 25.0% · temporal 15.8%). Retrieval P@5 was already 97.8% — the gap was the reader's context window, not recall. So we shipped a summary layer (per-trajectory compressed summaries, routed by question type), with pass/fail gates **committed before the run**. Final full-500 verdict: overall **42.6% → 75.4%** — every question has a real judge verdict (the 71/500 = 14.2% originally lost to intermittent judge-gateway failures were re-judged with the same judge, retry-only); **81.6%** like-for-like excluding those 71. We disclose both because judge-side outages masquerading as wrong answers is exactly how this field inflates or deflates itself. All three weak types clear their preregistered gates under both accountings (final re-judged n=500: multi-session 22.6→69.2, single-session-assistant 25.0→83.9, temporal 15.8→62.4; clean accounting excluding the 71: 73.2/85.4/83.3). High-scoring types show zero regression under the final accounting — an earlier −5pt on one type turned out to be a judge-outage artifact, not model regression. e2e judging used our own harness with a glm-5.3-flash judge (the official harness judge is GPT-4o), which is one more reason we report dual accounting and publish the full protocol. Preregistration doc + full verdict live in the repo.

It also does two things beyond recall: pre-action **drift detection** (checks agent actions against failure-mode anchors, AUC 0.83, p95 <50ms) and **cross-agent contracts** (tracks implicit obligations when multiple agents share files).

**Sealed, not just claimed.** Every number above ships as a VerifyPack entry in the repo: `pack.json` + sha256 manifest + claims recomputable from payload bytes + an ed25519-signed receipt. `python -m tools.verifypack verify runtime/verifypack/arma_summary/pack` recomputes all eight claims (0.754 all-judged / 0.700 conservative / per-type) from bytes alone — no trusting us required (exact commands in the pinned comment). One thing we're oddly proud of: the 81.6% figure is deliberately **not** sealed, because it can't be recomputed from pack-internal bytes alone — unverifiable numbers don't get sealed, they get disclosed with the reason why. And the door swings both ways: re-run anything (~$3.50) and sign the receipt with *your own* key — contradicting results go on our Reproducibility Wall with the same prominence as confirming ones.

**Getting it (the sub filters links in post bodies — every URL lives in the pinned first comment):**
- Python users: `pip install nautilus-compass` (PyPI — ships the CLI, MCP server, A2A adapter and session tools).
- Claude Code / Desktop (local daemon, everything stays on your machine): clone the repo into `~/.claude/plugins/nautilus-compass`, then run its `install.sh` and `daemon_start.sh` — exact commands in the pinned first comment.
- Cursor / Cline / Continue.dev / Zed: `python scripts/install_to_agent.py` (one script).
- No local install: **hosted open beta, self-serve** — 6-digit email-code signup, mint a scoped token in the console, point any MCP client at the hosted endpoint. Tokens are server-bound to your own space (read+write scoped per project); cross-user read/write is denied and revocation takes effect immediately — verified by a four-probe suite that runs against the public endpoint (code in repo).

The pinned first comment carries the repo / landing / signup links, the answer to "why is your 75.4% lower than mem0's self-reported 94.4%", and the verify-it-yourself commands:

```
git clone https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
python -m tools.verifypack verify runtime/verifypack/arma_summary/pack --out /tmp/r.json
python -m tools.verifypack check runtime/verifypack/arma_summary/pack \
  --receipt runtime/verifypack/arma_summary/pack/receipts/receipt.json \
  --pubkey f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be
```
(recomputes all 8 claims from bytes; full protocol: docs/REPRODUCIBILITY_WALL.md)

Happy to answer questions on the retrieval routing design or the failure experiments — those are the fun parts.

> 🔴 2026-09-08 发布夜变更:r/LocalLLaMA AutoMod 拦新账号正文 URL。正文全部链接(git clone 块/signup/repo/landing)移入首评;首评正本=launch_plan §13(已加链接块头)。

---

## B. X thread(中文,7 条)

1. 开源 agent 记忆层 compass 在 LongMemEval-S 全 500 题上检索三项全面超过 mem0:P@1 0.890 vs 0.774(+11.6pt),P@5 0.978,MRR 0.929。同题同判据,证据链开源。🧵
2. 关键设计赌注:写入时不调 LLM。原文本地 BGE-m3 嵌入,零抽取、零上云、零写入成本。智能全部在读侧。
3. 读侧三武器:①utterance 分型路由(单会话用户型问题检索 turn 级块,该型 P@1 0.20→1.00)②BM25+dense RRF 混合③日期锚定。
4. 失败实验同样公开:rerank 有害(-2pt)、K=50 无效、小模型无效。12 题 +16.7pt 的初读是抽样偏差,30 题混合后修正。全部证据在 repo docs/evidence/。
5. 客场也赢:LOCOMO(mem0 主场)n=1986,P@1 0.644 vs 0.592。大语料(12×)泛化 P@5 0.888。EverMemBench 超 Mem0/Zep/MemOS。
6. e2e 短板已修:摘要层上线(判据先于跑数预注册),全量 500 题 42.6%→75.4%(71 题 judge 断连全部重判补齐,每题有真判决)/81.6%(同口径剔除断连 71 题)。三弱型双口径全过门,定案重判口径:ms 22.6→69.2·ssa 25.0→83.9·tr 15.8→62.4(剔除断连干净口径 73.2/85.4/83.3);高分型零回退。
7. 附赠:drift 检测 AUC 0.83(动作前对照失败模式锚点)+ 跨 agent 合约审计。所有对外数字已 seal+ed25519 签名,两条命令从字节复算,无需信任我们。本地三条命令接入;托管版开放自助注册(signup→控制台发 scoped token→任意 MCP 客户端直连),跨用户读写被拒+撤销即时,四探针公网验证。Modified MIT。github.com/chunxiaoxx/nautilus-compass

## B2. X thread(英文,7 条 · 9/8 发布夜新增,英文侧零覆盖补位)

> 发法同 §B:条 1 附 `table_headtohead_en.png`;每条 <280 字符;LinkedIn 可整条复用。

1. We built an open-source memory layer for agents (nautilus-compass) and ran a head-to-head vs mem0 2.0.19 on LongMemEval-S — full 500 questions. Retrieval P@1: 0.890 vs 0.774 (+11.6pt). Same questions, same criteria, evidence open. 🧵
2. The design bet: zero LLM calls at write time. Verbatim text, local BGE-m3 embedding — no extraction, no cloud, no write cost. All the intelligence lives at read time.
3. Read-side weapons: ① utterance-type routing (turn-level chunks for user-utterance questions — that type went P@1 0.20→1.00) ② BM25+dense with RRF fusion ③ date anchoring.
4. What didn't work is published too: cross-encoder reranking hurt (-2pt), K=50 didn't help, smaller embedders didn't either. A 12-question subset once read +16.7pt — sampling bias; we re-ran 30 mixed before believing it.
5. Away games: LOCOMO (mem0's home turf), n=1986: 0.644 vs 0.592. A 12× larger corpus: P@5 0.888. EverMemBench: above Mem0/Zep/MemOS.
6. e2e, fixed with preregistered gates: 42.6% → 75.4% on the full 500 (71 judge-outage questions re-judged — every question has a real verdict); 81.6% like-for-like excluding them. Weak types cleared gates under both accountings.
7. Every number here ships sealed & ed25519-signed (VerifyPack) — two commands recompute our claims from bytes, no trust required. Plus a Reproducibility Wall: run it yourself (~$3.50), or re-run & sign with your own key. github.com/chunxiaoxx/nautilus-compass

---

## C. 发布节奏

1. r/LocalLLaMA 周二-周四 9-11am ET(技术帖黄金窗)
2. X thread 帖发后 2h 内(互相导流)
3. r/LocalLLaMA 评论区 24h 内必回(算法权重)
4. 第二帖素材:骨架已就绪(docs/marketing/20260830_lmev2_post2_skeleton.md,占位符待填 d13/d14 终值已定案:LoRA 双域未过门关闭、abstention gate 预注册拒收);V2 现役干净口径 web 40.0%/ent 38.4%;cheap-tier 已定案 36.3/36.5 未超现役组合关闭,一并填入。
