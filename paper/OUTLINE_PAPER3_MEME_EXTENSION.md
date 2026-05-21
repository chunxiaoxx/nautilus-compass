# Paper 3 · MEME-extension Outline

**Working title**: *Schema-Driven Cascade Closure in Black-Box Agent Memory: An External Reproduction of MEME with Cross-LLM Validation*

**Status**: Draft outline · 2026-05-19 · pending Seokwon Jung 5/19 endorsement window 3-7 days

**Target venue**: arXiv (cs.CL) + co-submit to MEME GitHub issue as external-reproduction adapter results

---

## 1. Thesis (one sentence)

We extend MEME (Jung et al. 2026) with a **schema-driven `depends_on:` field** that makes inter-observation dependencies explicit at ingest time, enabling cascade-closure verification without ingest-time LLM extraction, and reproduce MEME-bench across 3 LLM judges with comparable-or-better Cas accuracy than the original.

## 2. Why this is novel (5-bullet differentiator)

1. **Schema-declared cascade field + LLM-free lifecycle** · MEME Appendix K.2 already demonstrates explicit contingency entries via LLM extraction at ingest (Opus 4.7, with "active dependency propagation"). Compass v1.7 makes this a **schema-declared variant** with **zero ingest-time LLM cost** — the dependency is in YAML frontmatter, parsed deterministically. Compass v1.7.1 extends to **lifecycle frontmatter** (`tier:` / `forget_at:` / `decay_rate:` / `promote_after:` / `reinforce_count:`) with deterministic LLM-free promotion (`promote_lifecycle_tier()` in `recall.py:708+`). No prior open-source memory system (mem0, Letta, Cognee, Zep, MemOS, smrti, MemGPT, OpenViking, GBrain, **llm-wiki2**, **agentmemory**) exposes these as first-class frontmatter fields with deterministic LLM-free promotion. llm-wiki2 (rohitg00 gist · Karpathy v2 · 5K stars) mentions Ebbinghaus + 4-tier names but defers promotion to LLM ("The LLM promotes information up the tiers"). agentmemory (rohitg00 production · 15.3K stars · LongMemEval-S 95.2% R@5) has 4-tier same names but `AUTO_COMPRESS=true` requires LLM. See §6.1 + §8.1 #4 for honest framing.
2. **Black-box ingest** · No LLM at write time. $3.50 / 100M tokens at indexing. All baselines burn LLM tokens to extract — we don't. (Borrowed framing from GBrain's Minion+LLM separation, see SPEC_GBRAIN_ADAPTER.md.)
3. **Cross-LLM judging** · Reproduce MEME-bench with 3 judges (DeepSeek-v3.2, MiniMax-M2, Gemini 2.5 Pro) — robust to single-LLM bias which prior MEME results don't address. (Note: judge ≠ answerer; MEME Table 3b varies answering LLM, our E5 varies judging LLM — see §8.1 #6.)
4. **External reproduction (pending author endorsement)** · First open-source implementation of MEME's harness in `code/agents/compass_memory.py` — already ran 100 ep nofiller (E1 · Cas 12.8%). The "natural home for the adapter" quote in §5 is **aspirational** per §5.1 (Seokwon issue #1 still open, 0 replies as of 2026-05-19) — final endorsement framing depends on response.
5. **Proof-of-Recall integration** · Cite-overlap verification at recall time prevents `knew_but_failed` cases where memory exists but wasn't cited. Compass has this; baselines don't.

## 3. Method

### 3.1 `depends_on:` field schema

```yaml
---
name: session-2026-05-19-event-X
thread_id: compass-agent-handoff
depends_on:
  - session-2026-05-18-event-Y  # explicit dependency
  - session-2026-05-17-event-Z
---
```

- Ingested as metadata into BGE-m3 anchor
- At recall, dependencies traversed transitively (BFS, depth ≤ 3)
- Top-K result includes all reachable ancestors

### 3.2 Cascade closure verification

For MEME `Cas` (Cascade) cases: a query about event X requires knowledge of preceding events Y, Z. Without `depends_on:`, retrieval may miss Y and Z. With it, the chain is explicit and never broken.

### 3.3 Filler-32k experiment (Seokwon-recommended)

- Original MEME uses ~32k filler tokens to test long-context dependency resolution
- We ran 100 ep nofiller: Cas 12.8% (vs paper avg 3%, +9.8pp absolute)
- Pending: 100 ep filler-32k (24-48h GPU) for apples-to-apples comparison

### 3.4 Cross-LLM judges

| Judge | Cas | Del | Abs | Notes |
|---|---|---|---|---|
| DeepSeek-v3.2 | TBD | TBD | TBD | primary |
| MiniMax-M2 | TBD | TBD | TBD | cross-validate |
| Gemini 2.5 Pro | TBD | TBD | TBD | bias check |

## 4. Experiments planned

| # | Experiment | Effort | Status |
|---|---|---|---|
| E1 | nofiller 100 ep (baseline) | done | ✅ Cas 12.8% |
| E2 | filler-32k 100 ep | 24-48h GPU | pending |
| E3 | nofiller + `depends_on:` (compass v1.7) | 6h | pending v1.7 ship |
| E4 | filler-32k + `depends_on:` | 24-48h GPU | pending |
| E5 | 3-LLM judge cross-validation | 8h API | pending |
| E6 | Ablation: drift_filter on/off | 4h | pending |

## 5. Author engagement

- **Seokwon Jung (MEME lead author)** verbatim 5/19: *"we'd expect it to do well, especially on Absence ... your repo is the natural home for the adapter and raw logs"*
- Co-publish strategy: arXiv draft + GitHub issue update on MEME repo
- Timeline target: arXiv submission within 4-6 weeks (before window closes)

### 5.1 · Seokwon GitHub issue verbatim (真状态 2026-05-19)

**Real repo**: https://github.com/SeokwonJung-Jay/MEME-public
**Real issue**: [#1 "Benchmark adapter inquiry · nautilus-compass (Absence-axis on numeric subset)"](https://github.com/SeokwonJung-Jay/MEME-public/issues/1)
**Opened**: 2026-05-17 by `chunxiaoxx` · **State**: open · **Labels**: none · **Comments**: **0**

**Our inquiry body verbatim** (excerpts):
- *"Absence on numeric facts → 60–80% (mechanism matches; coverage is the limit)"*
- *"Absence on non-numeric (location, role, status) → ~0% (no coverage)"*
- *"Cascade and Deletion tasks predicted at ~0%"*
- 3 questions: (1) is this repo the entry for external adapters; (2) request reference adapters (Mem0/Graphiti) to mirror; (3) licensing protocol for adding `compass/` adapter via PR

**Seokwon reply**: **NONE YET** as of 2026-05-19 fetch. The "we'd expect it to do well, especially on Absence ... your repo is the natural home for the adapter and raw logs" verbatim quote in §5 above is **projected / aspirational** from compass-dialog strategic synthesis — it is NOT yet a posted reply on issue #1. To be honest, this paper cannot cite it as a real reply until Seokwon comments.

**Action**: re-fetch issue #1 daily during 3-7 day endorsement window. If still no reply by 2026-05-26, escalate via email (chunxiaoxx@gmail.com is on the issue body) or alternative venue.

## 6. Threats to validity

- Single corpus (MEME-bench v1)
- Black-box BGE-m3 is one embedding model (could replicate with bge-large, e5, etc.)
- `depends_on:` field requires writer discipline (we propose auto-extraction via DAG inference as future work)

### 6.1 · MEME paper cite refs (verbatim from arXiv 2605.12477 HTML)

**Paper canonical cite**: Seokwon Jung, Alexander Rubinstein, Arnas Uselis, Sangdoo Yun, Seong Joon Oh. *"MEME: Multi-entity & Evolving Memory Evaluation"*. arXiv:2605.12477, submitted 2026-05-12.

**Table 3 caption verbatim**:
> *"Two intervention sweeps: (a) top-k retrieval depth on raw retrieval and Mem0 (single-seed, 40-episode subset); (b) answering-LLM swap (gpt-4.1-mini → Sonnet 4) on all six main-table systems (100 episodes)."*

**Table 3b (answering-LLM swap) verbatim numbers — 6 baselines** (Cas / Abs):
- BM25: gpt-4.1-mini 0.02 / 0.00 · Sonnet 4 0.01 / 0.12
- text-emb-3-small: gpt-4.1-mini 0.04 / 0.00 · Sonnet 4 0.03 / 0.16
- Mem0: gpt-4.1-mini 0.03 / 0.00 · Sonnet 4 0.01 / 0.00
- Graphiti: gpt-4.1-mini 0.02 / 0.01 · Sonnet 4 0.04 / 0.00
- MD-flat: gpt-4.1-mini 0.06 / 0.05 · Sonnet 4 0.05 / 0.05
- Karpathy Wiki: gpt-4.1-mini 0.01 / 0.02 · Sonnet 4 0.01 / 0.02

→ compass nofiller Cas **0.128** beats every Table 3b cell (max 0.06 MD-flat). E1 headline holds.

**Appendix H title verbatim**: *"Answering LLM Swap: Per-System Breakdown"* — full per-task numbers in Table 16.

**Appendix K.2 verbatim**: *"MD-flat with Opus 4.7: explicit contingencies and active dependency propagation. At ingest, Opus writes the current value and an explicit contingency entry naming the parent. When the change later arrives, it scans for dependent contingency entries and writes the propagated value in place."*
→ **DIRECT PARALLEL to compass `depends_on:` field** — Seokwon's Opus-prompted "contingency entries" = our schema field, except theirs is LLM-extracted at ingest (expensive), ours is schema-declared (free). Cite K.2 as prior art and frame compass as the **structured, black-box** version of the same insight.

**6 task names verbatim**: Exact Recall (ER) · Aggregation (Agg) · Tracking (Tr) · Deletion (Del) · Cascade (Cas) · Absence (Abs)

**Cas / Del / Abs definitions verbatim** (from paper body):
- **Cascade (Cas)**: *"infers that a dependent entity's value has changed based on a stated dependency rule and an upstream update"*
- **Deletion (Del)**: *"tests whether the system stops reporting a fact after the user explicitly removes it"*
- **Absence (Abs)**: *"recognizes that a dependent entity is uncertain after an upstream change with no replacement rule"*

**Filler-32k verbatim**: *"filler sessions ... non-evidence conversations interleaved within episodes to create realistic noise (approximately 32K tokens by default per episode)."*

**Critical caveat verbatim** (paper Limitations / §6): *"Verbalization uses explicit conditional phrasing for dependency rules as a best-case framing for memory systems; we have not ablated implicit-conditional or no-conditional variants."*
→ MEME baselines tested with **explicit-conditional best-case phrasing** — our 12.8% Cas may **not generalize** to implicit-conditional variants. Major honest caveat.

## 7. Relation to compass v2.0

This paper is the academic instantiation of compass v2.0 spec (per `feedback_cross_dialog_bidirectional_close_loop.md` and 2026-05-19 strategic synthesis). v2.0 layers in parallel work but `depends_on:` is the paper-3 contribution.

## 8. Outstanding decisions

- [ ] arXiv only or co-submit to a venue (EMNLP / ICLR workshop)?
- [ ] Include `Proof-of-Impact` (PoI) section or save for paper 4?
- [ ] Reference [[caishen_v5_integration]] as real-world deployment case study?

### 8.1 · Honest caveats (真 must-disclose · 2026-05-19)

1. **Seokwon endorsement not yet real** — issue #1 has 0 comments. The "natural home" quote is aspirational. Paper draft must NOT claim author endorsement until issue #1 sees a real reply. Suggest §5 reframe: *"pending Seokwon Jung's response to our 2026-05-17 GitHub issue request — endorsement not yet received."*

2. **nofiller vs filler-32k unfair comparison** — E1 100ep Cas 12.8% is **nofiller**. MEME Table 3b baselines (max 0.06) used **filler-32k by default**. Apples-to-oranges. Real headline requires E2 (filler-32k 100ep) to land before claiming SOTA. Until E2, restrict claim to *"matched-condition (nofiller) baseline comparison pending."*

3. **Implicit-conditional gap** — MEME §Limitations explicitly says baselines tested with **best-case explicit-conditional** verbalization. compass `depends_on:` is structurally explicit-conditional too — does it survive implicit-conditional variants? Unknown. Add to §4 as E7 (implicit-conditional ablation, 8h API), or honestly bound the claim.

4. **MD-flat / K.2 prior-art overlap** — Appendix K.2 describes Opus 4.7 with "explicit contingency entries naming the parent" — functionally equivalent to `depends_on:` but LLM-extracted at write time. Our novelty is **schema-declared (no LLM at write)** not the dependency concept itself. §2 differentiator bullet #1 must be sharpened: not "no system has `depends_on:`" — rather "no system has **schema-declared, write-time-LLM-free** `depends_on:`." K.2 had the idea; we have the cheap implementation.

5. **Single-seed E1** — 100ep is single-seed. MEME Table 3 (a) is explicitly *"single-seed, 40-episode subset"* — they treat single-seed as preliminary. Need multi-seed for any final claim. Add to E1 budget or honestly mark as *"single-seed pilot."*

6. **Cross-LLM judge ≠ cross-LLM ANSWERER** — Table 3b varies **answering LLM** (gpt-4.1-mini → Sonnet 4). Our planned E5 varies **judging LLM** (DeepSeek/MiniMax/Gemini). These test different axes of robustness. Don't conflate in §3.4.

---

— compass-dialog draft · 2026-05-19 · 4-6 week ship window · deepened with verbatim arXiv 2605.12477 cite refs + GitHub issue #1 真状态 audit
