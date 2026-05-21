# SPEC · Layer 2 · L1 Per-Project Overview · OpenViking Paradigm Rewrite

> **Status**: Design only · 2026-05-21 · code ship deferred to next fresh session (~1 week effort)
> **Strategy**: Agent-driven clean-room rewrite of OV L1 paradigm in Python · NO fork of AGPL-3.0 source
> **Target**: v2.0 Layer 2 storage tier · `paper/COMPASS_V2_SPEC_DRAFT.md` line 30-39
> **Total LOC estimate**: ~300 (group/cluster/render/cron)

---

## 1. Context · why L1 layer

compass v1.7.1 currently has only **L0 storage** (raw `session_*.md` + BGE-m3 anchor index). For projects with **1000+ sessions**, raw L0 retrieval has 2 problems:

1. **Latency**: BGE-m3 cosine over 1000 embeddings is fast (<300ms) but the LLM downstream then has to read top-K raw sessions (~600 chars each) → context bloat
2. **Coherence loss**: top-K from cosine alone can return 5 sessions from 5 different threads · no narrative coherence

**OV's bet**: introduce a middle tier — per-project **L1 overview** that pre-summarizes related sessions into compact paragraphs. Recall hits L0 first; if returned set has L1 overview, surface the L1 summary instead of 5 raw sessions.

**Trade-off**:
- ✅ Fewer tokens to downstream LLM (1 L1 paragraph vs 5 raw L0 sessions)
- ✅ Better narrative coherence (grouped by `thread_id` + topic cluster)
- ❌ L1 generation is offline batch work (nightly) · adds infrastructure
- ❌ L1 freshness lag (1 day stale at worst case)

---

## 2. OV paradigm audit (verbatim · what we borrow vs reject)

### Borrowed (paradigm-only · no code)
- **3-tier on-demand loading**: L0 raw / L1 overview / L2 deep dive · client requests by tier
- **Filesystem-paradigm storage**: each tier is a file (not a DB row) · diffable, git-trackable
- **`viking://` URI scheme**: tier-agnostic addressing · `viking://project/agent/session_X` resolves to L0 by default, L1/L2 on suffix

### Rejected (anchor #5 anti-reinvention)
- **OV ingest-time LLM extraction**: kills compass core diff (no LLM at ingest). compass L1 generation runs **nightly offline** (not at write time)
- **OV's specific TypeScript/Rust/Python stack**: rewriting in idiomatic Python only · drop multi-language complexity
- **OV's `viking://` URI scheme implementation**: design borrowed, code from scratch

### License rationale (2026-05-22 WebFetch verified)
- OV root LICENSE = AGPL-3.0
- Fork/link to compass MIT = copyleft contamination
- Clean-room paradigm rewrite = legally OK (only design borrowed · zero code copy)
- Document upstream design references in `THIRD_PARTY_DESIGN_REFERENCES.md` (TODO Layer 5 ship)

---

## 3. L1 architecture (Python · clean-room)

### 3.1 Storage layout

```
~/.claude/projects/<encoded>/memory/
├── session_*.md                    # L0 raw (existing · unchanged)
└── _l1/                            # NEW · L1 overview tier
    ├── thread_<id>.md              # one file per thread_id with ≥3 sessions
    ├── topic_<cluster_id>.md       # one file per detected topic cluster
    └── _l1_index.json              # lookup table · session_id → l1_file
```

### 3.2 Generation pipeline (nightly batch)

```
Trigger: cron 03:00 daily (or manual `compass-mcp l1-build`)

Step 1 · Scan recent sessions
  - All session_*.md modified in last 7 days
  - Skip sessions already in _l1_index.json

Step 2 · Group by thread_id
  - For sessions with non-empty thread_id frontmatter:
    - Group all sessions sharing thread_id
    - If group size >= 3, generate L1 overview

Step 3 · Detect topic clusters (for thread-less sessions)
  - BGE-m3 embed each session description (already indexed at L0)
  - Cluster with cosine threshold 0.55 (heuristic · tuneable)
  - For clusters size >= 4, generate L1 overview

Step 4 · Generate L1 overview (LLM-free · deterministic)
  - Concatenate session descriptions + extract numeric_claims
  - Render markdown overview file with:
    - YAML frontmatter (tier: episodic · auto-detected from member tiers)
    - List of constituent session paths
    - First-sentence excerpts from each member
    - Aggregated numeric_claims across members
  - NO LLM summarization at this step (anchor: no LLM at ingest)

Step 5 · Update _l1_index.json
  - Map each member session_id to L1 file path

Step 6 · Re-index BGE-m3
  - Re-embed _l1/*.md files as separate index pool
  - Recall now searches L0 + L1 concurrently (RRF k=60 fusion · existing)
```

### 3.3 Recall integration (online · no new latency)

```python
# Pseudocode · recall.py extension
def render_v02_vector_mode_with_l1(entries, query, cache):
    # Existing: L0 cosine ranking
    l0_top = bge_cosine_top_k(query, entries_l0, k=10)

    # NEW · L1 overlay
    l1_entries = load_l1_index()
    l1_top = bge_cosine_top_k(query, l1_entries, k=5)

    # RRF fusion (reuse v1.7.1 rrf_fusion · Phase 2.C ship 2ed77b4)
    fused = rrf_fusion(l0_top, l1_top, k=60, top_k=10, session_diversify=True)

    # Surface L1 when present · collapse member sessions to summary
    return collapse_to_l1_if_available(fused)
```

---

## 4. Implementation plan · ~300 LOC

| Module | Path | LOC | Description |
|---|---|---|---|
| `l1_grouper.py` | `nautilus_compass/storage/l1_grouper.py` | 80 | Step 2-3 · thread_id + topic cluster grouping |
| `l1_renderer.py` | `nautilus_compass/storage/l1_renderer.py` | 90 | Step 4 · LLM-free markdown overview generation |
| `l1_index.py` | `nautilus_compass/storage/l1_index.py` | 60 | Step 5-6 · index management + BGE re-embed |
| `l1_recall_overlay.py` | `nautilus_compass/storage/l1_recall_overlay.py` | 50 | Step 6 (online) · RRF fusion with L0 |
| `cli_l1_build.py` | `bin/cli_l1_build.py` | 20 | Manual trigger · `compass-mcp l1-build` |
| **Total** | | **~300** | |

---

## 5. Verification criteria

### 5.1 Smoke test (10 cases · LLM-free deterministic)
1. Empty session set → no L1 files generated
2. 2 sessions same thread_id → no L1 (below threshold 3)
3. 3 sessions same thread_id → 1 thread_<id>.md created
4. 5 thread-less sessions cosine-similar → 1 topic_<id>.md created
5. Mixed: 3 in thread_A + 4 in topic cluster → 2 L1 files
6. L1 frontmatter has tier=episodic + accurate member list
7. _l1_index.json maps every member session_id → L1 file
8. Recall query that matches L1 returns L1 summary (not 3 raw)
9. RRF fusion deterministic across 2 runs
10. Idempotent · re-running L1 build doesn't duplicate

### 5.2 Production verification (post-ship)
- 1000+ session project · recall p50 latency < 300ms (no regression)
- Accuracy ≥ v1.7.1 baseline + 5pp on LongMemEval-S
- L1 generation walltime < 5min for 100 sessions on local CPU
- Disk overhead < 10% of L0 (compression check)

---

## 6. Open questions (defer to ship session)

- [ ] **Topic cluster threshold** · cosine 0.55 is a heuristic. Validate against actual project distributions before fixing.
- [ ] **L1 staleness policy** · do we mark L1 entries stale when a member session is updated? Or rebuild only on cron?
- [ ] **Privacy filtering** · L1 inherits union of member sessions' privacy tags · need explicit policy doc.
- [ ] **L0 vs L1 ranking precedence** · when both match query, surface which? (current proposal: L1 if score ratio > 0.85)

---

## 7. Sequence (ship order in 1-week sprint)

| Day | Module | Notes |
|---|---|---|
| 1 | `l1_grouper.py` | Pure logic · easy smoke |
| 2 | `l1_renderer.py` | Markdown output · diff-check against golden |
| 3 | `l1_index.py` | Includes BGE re-embed · slowest step |
| 4 | `l1_recall_overlay.py` + integration with recall.py | Touches existing hot path · careful |
| 5 | `cli_l1_build.py` + cron wiring | UX polish |
| 6 | Smoke test 10 cases + benchmark p50 latency | Verification |
| 7 | LongMemEval-S sample 50 acceptance run | Pre-ship sanity check (NOT full 500) |

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Topic cluster threshold mis-tuned · poor groupings | Manual tuning per-project · expose env var `COMPASS_L1_TOPIC_THRESHOLD` |
| L1 generation breaks at scale (10K+ sessions) | Incremental mode · only re-compute affected groups |
| L1 staleness · users surprised by old summaries | Frontmatter shows `generated_at` · stale > 7d marked |
| Anchor #5 reinvention · OV TypeScript already does L1 | Read OV docs, **not code** · clean-room verified |
| `viking://` URI premature · over-engineering | Defer URI to Layer 5 sprint · L1 uses raw paths first |

---

## 9. Anchor contributions

| Anchor | Contribution |
|---|---|
| #1 agent first | L1 surfaces narrative coherence for super-agent long sessions |
| #3 anti-D-maintenance | Clean 7-day sprint plan · NOT bundled with L2 (separate sprint S6) |
| #5 anti-reinvention | OV paradigm rewrite is the strategy · paradigm-only borrow |
| #7 anti-overclaim | Pre-registered verification criteria · 10 smoke cases + p50 latency |
| #9 verbatim direction | OV LICENSE verbatim AGPL-3.0 (5/22) → rewrite-from-scratch path |

---

## 10. Related ship trail

- v2 spec source · `paper/COMPASS_V2_SPEC_DRAFT.md` Layer 2
- License audit · `paper/SPEC_OV_ADAPTER.md` §1 v2 (5/22 verbatim)
- 3-doc realignment · commit `97fbc2c` (5/21 user-clarified rewrite strategy)
- RRF reuse · commit `2ed77b4` Phase 2.C (`recall.py rrf_fusion`)
- Plan reference · `~/.claude/plans/scalable-drifting-seahorse.md` Phase 4 (future)
- Next sprint S4 spec · `paper/SPEC_PROOF_OF_IMPACT.md` (write next)
