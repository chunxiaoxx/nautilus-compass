# SPEC · OpenViking Storage Backend Adapter for nautilus-compass v2.0

**Status**: Spec design only (no implementation code) · 2026-05-19
**Target**: compass v2.0 Layer 2 (Storage) per `COMPASS_V2_SPEC_DRAFT.md` lines 30-39
**Scope**: Adapter layer ONLY · do NOT rewrite OpenViking
**Total LOC estimate**: ~800 (L1 ~300 + L2 ~400 + `viking://` ~100)

---

## 1. License Compatibility (v2 · 2026-05-21 reframe)

> ⚠️ **License audit timeline · 真 verbatim multi-source reconciliation**:
>
> | Date | Source | Verbatim claim | Status |
> |---|---|---|---|
> | 2026-05-19 | This spec author | "LICENSE file = Apache License 2.0" | retracted by v2 |
> | 2026-05-22 | WebFetch root `LICENSE` file | "GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007" | **current truth** |
> | 2026-05-22 | WebFetch repo README | "Main Project: AGPLv3 · crates/ov_cli: Apache 2.0 · examples: Apache 2.0" | confirms mixed |
>
> Possible cause · (a) OV upstream changed license between 5/19 and 5/22 OR (b) 5/19 author claim of "verbatim" was unverified summary. Either way · v2 truth = AGPL-3.0 main · Apache 2.0 subdirs (`crates/ov_cli` + `examples`).

**Source-of-truth (5/22 verified)**: `https://github.com/volcengine/OpenViking/blob/main/LICENSE` · verbatim:
```
GNU AFFERO GENERAL PUBLIC LICENSE
Version 3, 19 November 2007
```

**Subdirectory licenses** (per upstream README):
- Main project · **AGPL-3.0**
- `crates/ov_cli` · Apache 2.0
- `examples/` · Apache 2.0

**Compatibility with compass (MIT)**:
- ❌ AGPL-3.0 main code · **NOT MIT-compatible** for vendoring (copyleft contagion · any code linking to AGPL becomes AGPL)
- ✅ Apache 2.0 subdirs (`crates/ov_cli` only) · compass MIT can consume freely
- ✅ Paradigm-only reference (read README/docs · cite design pattern without code fork) · OK

**Adapter strategy (v2 · revised)**:
- ❌ Do NOT vendor OV main source (would contaminate compass MIT)
- ❌ Do NOT `pip install openviking` and link main · same contamination
- ✅ Reference OV `crates/ov_cli` (Apache 2.0) only · re-implement L0/L1/L2 tier paradigm from scratch in compass · cite OV as design reference
- ✅ Cite OV LoCoMo10 benchmark (+43% task / -91% token) as third-party result · paradigm validation without code dependency

**Required attribution actions** (P0 before paper3 ship):
1. Cite OV verbatim with **license correction** in all paper/docs: "OpenViking (volcengine · AGPL-3.0 main + Apache 2.0 subdirs · 24.3k stars)"
2. Update `paper/COMPASS_V2_SPEC_DRAFT.md` line 116 (original AGPLv3 claim was correct · 5/19 retraction was wrong)
3. Module header (if any compass storage module borrows OV paradigm): `# Inspired by OpenViking L0/L1/L2 paradigm (volcengine · AGPL-3.0 · paradigm only · no code linkage)`
4. Do NOT vendor OV source at any level · do NOT pip-install · paradigm-only reference

---

## 2. L0 / L1 / L2 Tier Mapping to Compass

OpenViking's core innovation: **filesystem-paradigm tiered context loading** (NOT vector store) with self-evolving distillation.

| Tier | Compass current | Compass v2.0 (this spec) | Source |
|---|---|---|---|
| **L0** | `session_*.md` raw + BGE-m3 anchor index (v1.6.2) | unchanged | shipped |
| **L1** | _none_ | per-project overview · nightly batch · group by `thread_id` + topic cluster | **NEW · ~300 LOC** |
| **L2** | _none_ | per-project distillation · nightly Ollama Qwen 2.5 7B local LLM (0-token cost) | **NEW · ~400 LOC** |

**Why local LLM for L2**: GBrain "deterministic + LLM separation" path. Compass core constraint (`COMPASS_V2_SPEC_DRAFT.md` line 10) = **no LLM at ingest**. L2 distillation runs **offline nightly** (not ingest path), so single local LLM is permissible. Ollama Qwen 2.5 7B = $0 marginal cost · ~30s per project per night.

**Verbatim OpenViking benchmark** (upstream README, OpenClaw + OpenViking combo): task completion 35.65% → 52.08% · token cost −80%. Compass adopts the storage paradigm only · benchmark deltas are upstream's, not promised here.

---

## 3. `viking://` URI Scheme

**Goal**: compass code references memory artifacts by stable URI, decoupled from filesystem layout.

**Scheme**:
```
viking://project/<project>/L0/<session_id>
viking://project/<project>/L1/<overview_id>
viking://project/<project>/L2/<distillation_id>
```

**Resolution order** in `recall.py`:
1. If URI starts with `viking://` → adapter layer dispatch (~100 LOC).
2. Adapter: try local filesystem first (`~/.compass/projects/<project>/<tier>/...`).
3. Fallback: HTTP REST to OpenViking runtime if deployed (`OV_ENDPOINT` env var; optional).
4. If neither resolves → return 404 (do not fabricate).

**Backward compatibility**: existing v1.6.2 code paths (raw `session_*.md` filesystem reads) untouched. The `viking://` scheme is **additive**. Recall callers may opt-in by prefixing URIs; legacy callers continue passing bare paths.

---

## 4. Ingest Hook Changes

**Current (v1.6.2)**:
- compass `stop_hook.py` writes `session_*.md` (L0 raw).

**v2.0 additions** (no changes to L0 hot path · keeps ingest-LLM-free constraint intact):

| Hook | When | What | LLM? |
|---|---|---|---|
| `stop_hook.py` | per-session end (existing) | write L0 `session_*.md` | NO (unchanged) |
| `cron_l1_nightly.py` | nightly 03:00 local | batch: group L0 by `thread_id` + topic-cluster (BGE-m3 cosine k-means · k=8) → write L1 overview | NO (clustering only) |
| `cron_l2_nightly.py` | nightly 04:00 local | for each project · feed L1 + sampled L0 to Ollama Qwen 2.5 7B → write L2 distillation | YES (local · offline) |

**Crash semantics**: nightly batches are idempotent. If L1/L2 fails, L0 still serves recall. No data loss.

---

## 5. Recall Hook Changes (Hierarchical)

**Current (v1.6.2)**: cosine top-K over L0 anchor index.

**v2.0 hierarchical recall**:

1. **Pre-filter via L2** (if exists): query → top-3 L2 distillations → identify candidate projects/threads.
2. **Narrow via L1**: within candidate threads → top-K L1 overviews.
3. **Verify via L0**: pull cited L0 sessions referenced in selected L1 → run existing v1.6.2 anchor-cosine recall on this narrowed set.
4. Return L0 snippets with full provenance chain `L2 → L1 → L0`.

**Drift gate placement** (per v2.0 spec Layer 4):
- **L2 level · pre-filter**: drop drifted L2 distillations from candidate set (prevents whole-project pollution).
- **L0 level · verify**: existing v1.6.2 drift check on final returned snippets (unchanged).
- Rationale: L2 drift = systemic; L0 drift = local. Catching both stages.

**Fallback**: if L2/L1 missing (cold start · new project) → recall degrades gracefully to v1.6.2 L0-only behavior. No hard dependency.

---

## 6. Verification Criteria

| Metric | Target | Method |
|---|---|---|
| Recall p50 latency | < 300ms on 1000+ session project | `bench_recall_p50.py` (new) on synthetic 1k-session corpus |
| Recall accuracy | ≥ v1.6.2 baseline + 5pp | EverMemBench v2 rerun (compare to 44.4% baseline from `evermembench_compass_44pct.md`) |
| Ablation | 3-way: L0-only · L0+L1 · L0+L1+L2 | same harness · isolate contribution per tier |
| L2 token cost | $0 | assert Ollama local · no remote API calls in nightly batch |
| L0 hot path | unchanged latency | regression test: v1.6.2 ingest path runs identical wall-clock |
| Drift gate (L2) | ≥ 90% of drifted L2 quarantined | seeded drift corpus · measure quarantine rate |

**Stop conditions** (any failure → spec re-design, no ship):
- L0 latency regresses > 10%.
- L2 batch fails to converge in < 60s per project at 1k sessions.
- Ablation shows L1/L2 contribute < 2pp (then not worth ~800 LOC).

---

## 7. Cross-Reference & Scope Boundary

**Relation to other v2.0 specs**:
- **`COMPASS_V2_SPEC_DRAFT.md` Layer 2** (lines 30-39): this file IS that layer's full design.
- **GBrain adapter spec** (separate file · TBD): handles Minion+LLM separation framing. Independent contribution. Does NOT overlap with storage tiering here.
- **paper3 MEME-extension** (`OUTLINE_PAPER3_MEME_EXTENSION.md`): paper3 is the **chain layer** (`depends_on:` cascade · Layer 3). This spec is the **storage layer** (Layer 2). Paper3 does NOT need to cite this work. Independent contribution streams · paper3 stays scoped to chain semantics.

**Not in scope** (anti-D-maintenance · `COMPASS_V2_SPEC_DRAFT.md` line 11 "no reinventing OS components"):
- ❌ Rewriting OpenViking internals.
- ❌ Replacing BGE-m3 anchor index.
- ❌ Ingest-time LLM extraction (kills compass core diff · `COMPASS_V2_SPEC_DRAFT.md` line 96).
- ❌ Distributed L2 (single-machine Ollama only · multi-node deferred to v2.1+).
- ❌ Real-time L1/L2 updates (nightly batch only · simpler · proven).

---

## LOC Summary

| Component | LOC | Notes |
|---|---|---|
| L1 overview batch (`cron_l1_nightly.py` + clustering helpers) | ~300 | deterministic · no LLM |
| L2 distillation batch (`cron_l2_nightly.py` + Ollama client) | ~400 | local LLM call · offline |
| `viking://` URI scheme adapter (`viking_adapter/`) | ~100 | resolver + fallback dispatch |
| **Total NEW code** | **~800** | adapter only · zero OV-internals modification |

---

**Author**: compass-dialog · 2026-05-19
**License of this spec**: same as repo (MIT) · adapter implementation will be Apache 2.0 per upstream
**Next step**: defer ship to v2.0 sprint S3 (week 3-4 per `COMPASS_V2_SPEC_DRAFT.md` line 81). Code lives in fresh session.
