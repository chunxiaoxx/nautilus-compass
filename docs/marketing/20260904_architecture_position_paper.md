# Position Paper · Architecture Long-Read(第①层 · 英文业界)

> 状态:v1 草稿(2026-09-04)。真源=[ARCHITECTURE.md](../nautilusmem/ARCHITECTURE.md)。
> 投放:Hacker News / dev.to / 个人博客。发布前终检:数字与 SCOREBOARD/README 一致;
> 口径脚注(e2e 判官 glm-5.3-flash 自建 harness、数据 2024-10 原版)必须保留。

---

# Don't Summarize the Past for a Future You Can't Predict

### The case for lossless memory and read-time intelligence

*Position paper · nautilus-compass · September 2026*

## The hidden bet in every memory system

Ask how your favorite AI memory system works and you'll find the same move everywhere: when a conversation happens, an LLM is called to decide what's worth keeping. ChatGPT's memory extracts "facts" about you. Mem0 distills conversations into memorable facts. Zep builds a temporal knowledge graph. MemoryBank compresses sessions into summaries. The details differ; the structure is identical — **an irreversible, lossy decision about the future, made at write time, by a model that knows nothing about what the future will ask.**

We think this bet is structurally unwinnable. So we built an open-source memory layer — [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) — that doesn't make it, and then we tested the two approaches head-to-head across four benchmarks. This post is the argument, the architecture, and the receipts.

## Three invariants the write-time bet can't survive

**1. The future query distribution is unknowable at write time.**
Importance is not a property of a memory; it is co-created by the question that retrieves it. You cannot know at write time what granularity or what slice of a conversation will matter, because that depends on what gets asked later. Our own data makes this concrete: the same memory store, retrieved with a fixed strategy, scores **P@1 0.20** on single-session-user questions; routed by question type to turn-level chunks, the same store scores **P@1 1.00**. Nothing about the memories changed. The questions did. A write-time extractor never sees the question.

**2. The original text is the only representation you can re-index.**
Every LLM extraction freezes your memory at the cognition level of the model that did the extracting. A better embedder ships next year? Your summaries can't benefit — the loss already happened. Verbatim text can. A lossless store is the only representation that improves for free as the rest of the field improves, and the only one that can later become training fuel. Write-time compression doesn't just lose information; it burns your data at the moment of its creation.

**3. The cost curves point the wrong way.**
Storage asymptotes to free; LLM calls don't. Replacing the cheap thing (text) with the expensive thing (extractions) walks against the cost curve. This is why a write-free architecture isn't a sacrifice play: our writes cost zero LLM calls, and our reads run at **p95 0.34–0.80s**, versus **26.9s** for a mainstream LLM-controller memory agent measured on the same benchmark family. The ~80× isn't an optimization miracle. It's what happens when you put intelligence at the right moment instead of at every moment.

**The benchmark authors agree.** The ICLR 2025 LongMemEval paper documented the cost of this bet in human terms: ChatGPT's memory "tended to overwrite crucial information as the chat continues"; Coze "often failed to record indirectly provided user information." Their controlled experiments found that replacing stored sessions with LLM-extracted summaries or facts *hurt* question-answering accuracy due to information loss. And long-context models reading the full history directly? A 30–60% performance drop. The field's three default strategies — compress, extract, or brute-force-read — fail for the same underlying reason: they decide what matters at the wrong time.

## The counter-architecture: six layers

nautilus-compass (MIT, one repo, ~$3.50 of GPU time reproduces every number below) is a memory system built around one discipline: **the write path does nothing smart; the read path does everything smart.**

```
Evolution    cross-agent learning capsules: validated write-back → inherit on claim
Governance   drift detection (AUC 0.83, p95<50ms) · contract audit · scoped multi-tenancy · judge hygiene
Assembly     per-question-type summary cards · date-ordered timelines · utterance windows
Retrieval    6-type routing → BM25 + dense (RRF) · date anchoring · type-specific granularity
Storage      verbatim text (md+frontmatter) · local BGE-m3 embeddings · timestamps · zero LLM, zero egress
Format       OKF-compatible by construction — any OKF tool can read our memory bundles
```

**The write path** stores original text verbatim, embeds it locally with BGE-m3, and attaches timestamps. No fact extraction, no graph construction, no cloud calls. Writes are free and lossless, forever.

**The read path** carries all the intelligence:

1. **Question-type routing.** Questions are classified into six types, each routed to a different retrieval unit. User-statement questions retrieve turn-level chunks; cross-session questions route to per-session summary cards. This routing alone took single-session-user retrieval from P@1 0.20 → 1.00.
2. **Hybrid retrieval.** BM25 + dense embeddings fused with RRF. Dense alone drops temporal and multi-session queries; lexical carries exact identifiers — dates, names, versions.
3. **Date anchoring.** Session dates are prefixed into chunk text so "before/after" questions have temporal handles.
4. **Summary-card assembly.** Cross-session questions are answered from date-ordered per-session summary cards instead of raw chunks. End-to-end, this took our full 500-question run from **42.6% → 75.4%** with pass/fail gates committed before the run.

**What didn't work — also published.** Cross-encoder reranking on retrieved chunks *hurt* accuracy (−2pt). Retrieval depth K=50 added nothing over K=20. A smaller, faster embedder was strictly worse. We publish failures with the same rigor as wins; every experiment has its run log in the repo.

**Beyond recall**, the same substrate carries what an *organizational* memory needs: pre-action drift detection (checks agent actions against failure-mode anchors, AUC 0.83 at p95 <50ms), cross-agent contract auditing, three-layer scoped-token multi-tenancy verified by a public probe suite, and cross-agent learning capsules with a validation gate — an agent may only write experience back after a verified reward of 1.0, so wrong lessons can't compound into poison.

## The receipts

| Benchmark | compass | mem0 2.0.19 | Δ |
|---|---|---|---|
| LongMemEval-S · 500 q · P@1 | **0.890** | 0.774 | +11.6pt |
| LongMemEval-S · P@5 | **0.978** | 0.916 | +6.2pt |
| LongMemEval-S · MRR | **0.929** | 0.834 | +9.5pt |
| LOCOMO-10 · n=1986 · P@1 (mem0's home turf) | **0.644** | 0.592 | +5.2pt |
| LongMemEval-M · 500 q · P@5 (12× corpus) | **0.888** | — | generalizes |

On EverMemBench-Dynamic (n=500): **compass 44.4–47.3%** vs Mem0 37.09 / Zep 39.97 / MemOS 42.55.

On the official LongMemEval-V2 (451 questions, two domains): our untuned configuration scored 19.6%/12.8%; after tuning, **40.0%/38.4%** — with every negative result (LoRA retrieval augmentation, abstention gating, a cheap-tier variant) pre-registered, measured, and published.

And end-to-end on full LongMemEval-S — 500 questions against ~115k-token, ~50-session histories, retrieval through answering through judging — we score **75.4%** (or **81.6%** excluding 71 questions lost to a judge-side outage; both accountings disclosed). For scale: in the benchmark's own pilot study, the strongest commercial memory assistant — ChatGPT with GPT-4o-mini — scored **71.1%, on a version ten times easier** (3–6 sessions instead of ~50, 97 questions instead of 500).

Harder exam. Higher score.

*Caliber notes, in full: our end-to-end judging uses a self-built harness with a glm-5.3-flash judge over the original October-2024 benchmark release; the official judge is GPT-4o. Cross-paper score comparisons always carry judge caliber differences — which is exactly why we disclose ours and why we report dual accounting. The retrieval head-to-heads use identical questions and identical criteria on both sides, and the 71.1% comparison needs no judge of ours at all — it's the benchmark authors' own measurement.*

## What lossless unlocks

The standard memory pitch ends at recall. Ours doesn't, because a lossless store has a property no extraction pipeline can offer: **it appreciates.** Today it feeds retrieval. Tomorrow — with user consent — the same bytes feed fine-tuning and continual learning, the problem the largest labs are now betting their next act on. A memory system that compresses at write time is systematically destroying its own training corpus. We store the corpus instead.

There is a sentence from another project of ours that captures the design, and we'll leave it here without mysticism: *memory systems assume causes come first. In memory, the effect — the question — is what makes the cause real.* Keep every cause. Let the effect do the choosing.

## Why did everyone build it backwards?

1. **Path dependence.** Memory systems evolved from dialogue summarization, where a write-time summary feels as natural as a human taking notes. Nobody framed memory as a *storage* problem instead of an *understanding* problem.
2. **Misaligned incentives.** A pay-per-token write pipeline is a business model; "we store your text and index it locally" has no cloud story and no deck. The industry didn't fail to think of this. It can't afford it.
3. **The evaluation gap.** Without a hard benchmark, information loss at write time is invisible — lost facts don't error, they just quietly never come back. The LongMemEval authors built the ruler in 2024. We are among the first to use it and find the dominant design measuring short.
4. **The intuition error.** In the LLM era, the reflex is "a smart model should touch everything." The counter-intuition: a smart model should appear exactly once, at the moment information is complete *and* intent is known.
5. **The constraint advantage.** This system began as our own dogfood — an agent organization that needed private, local, fast memory and had no budget to pay an LLM for every remembered sentence. The constraints forced the first-principles answer. One developer, 130 days, 771 commits — most of them written by the agent fleet that this memory layer serves. The tool and its proof co-authored each other.

## Judge hygiene, briefly

One methodological note, because we think it's the field's meta-problem: we caught our own evaluation judge failing five times during this work — auth misconfiguration, gateway outages, reasoning-token budgets silently eating the response. One outage recorded 14.2% of questions as wrong answers (5.4 points of phantom error); without re-judging, our score corrections went in *different directions* across domains (+3.3/−1.9/+5.7). Every score above comes from a protocol with pre-registered anchors, judge smoke tests, mandatory dual accounting, and Wilson intervals. If your judge can silently fail, your leaderboard is fiction. (Full protocol in the repo; this is the subject of a separate paper in progress.)

## Reproduce it

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
bash install.sh && bash daemon_start.sh
```

Cursor / Cline / Continue.dev / Zed: `python scripts/install_to_agent.py`. No local install? Hosted open beta, self-serve: [compass.nautilus.social/signup](https://compass.nautilus.social/signup) — mint a scoped token, point any MCP client at the endpoint. Everything above — every benchmark number, failure log, and pre-registration doc — is in `docs/evidence/` and `docs/nautilusmem/`. Total reproduction cost: about $3.50 of GPU time.

One developer. 130 days. No cloud required. Your agents' memory shouldn't rent your past back to you.

*MIT · github.com/chunxiaoxx/nautilus-compass · compass.nautilus.social*
