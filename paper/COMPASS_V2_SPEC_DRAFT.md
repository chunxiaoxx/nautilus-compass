# Compass v2.0 Spec Draft

**Status**: Draft · 2026-05-19 · synthesis of `feedback_cross_dialog_bidirectional_close_loop`, MEME (Jung et al.), OpenViking, GBrain
**Source synthesis**: Strategic plan v10 (Super Agent stack = Nautilus + Automaton + compass EvoMap)

---

## Design constraints (anchored · non-negotiable · v2 reframe 2026-05-21)

- **No LLM at ingest** (compass core diff vs all baselines · $3.50 / 100M tokens)
- **Reimplement paradigms from scratch · DO NOT fork code** (v2 reframe · supersedes prior "do NOT rewrite" claim):
  - OpenViking (AGPL-3.0 verified 2026-05-22 · root LICENSE WebFetch verbatim "GNU AFFERO GENERAL PUBLIC LICENSE V3") → cannot fork/link to MIT compass · MUST rewrite L0/L1/L2 paradigm in Python from scratch · agent-driven reimplementation OK
  - GBrain (MIT · TypeScript) → fork legally allowed but TS not idiomatic · rewrite Minion+LLM separation + 5-step skillpack cycle in Python from scratch
  - Reason for v2 reframe · prior 5/19 spec assumed OV = Apache 2.0 (now retracted · false alarm · see SPEC_OV_ADAPTER.md §1 v2)
- **Survives long sessions** (1000+ session per project · scale tested)
- **Cross-agent friendly** (V5/V7/Kairos/compass dialog all writers)

---

## 5 layers · v2.0 architecture

### Layer 1 · Ingest (unchanged from v1.6.2 + drift-as-routing)

| Component | Status | LOC estimate | Dependency |
|---|---|---|---|
| black-box BGE-m3 anchor index | shipped v1.6.2 | — | — |
| numeric_claims cross-ref | shipped v1.5.2 | — | — |
| drift detection AUC 0.83 | shipped v1.6.2 | — | 25+35 anchors |
| **NEW · drift-as-routing** | spec only | ~150 | drift score → ingest tier (green canonical / yellow warning / red quarantine) |

**Verify criteria**: red-drift entries DON'T pollute recall top-K. Yellow surfaced with caveat tag.

### Layer 2 · Storage (NEW · borrow from OpenViking)

| Component | Status | LOC estimate | Dependency |
|---|---|---|---|
| L0 (raw session_*.md) | shipped | — | filesystem |
| **NEW · L1 (per-project overview)** | spec only | ~300 | nightly batch · group by `thread_id` + topic cluster |
| **NEW · L2 (per-project distillation)** | spec only | ~400 | nightly Ollama Qwen 2.5 7B (local · 0 token cost) |
| **NEW · `viking://` URI scheme** | spec only | ~100 | adapter layer · NOT rewrite OV |

**Verify criteria**: 1000+ session project · recall p50 latency < 300ms · accuracy ≥ v1.6.2 baseline + 5pp.

### Layer 3 · Chain (NEW · MEME-extension · Seokwon 5/19 endorsed)

| Component | Status | LOC estimate | Dependency |
|---|---|---|---|
| **NEW · `depends_on:` frontmatter field** | spec only · paper3 P0 | ~50 | schema change + BGE metadata |
| **NEW · transitive recall BFS depth ≤ 3** | spec only | ~200 | recall path traversal |
| **NEW · cascade closure verifier** | spec only | ~150 | given query · check all `depends_on` reachable in result set |

**Verify criteria**: MEME-bench Cas accuracy 12.8% → 35-50% (estimate).

### Layer 4 · Proof (compass唯一 · 真 differentiation)

| Component | Status | LOC estimate | Dependency |
|---|---|---|---|
| Proof-of-Recall (`recall_token` + cited_snippets) | shipped v1.5.2 spec | — | mcp_server `_validate_recall_proof` |
| 6-agent prompt-engineering pass for PoR | NOT shipped | ~120 lines prompt updates | V5/V7/Kairos/HR/Hr-web/创投日报 |
| **NEW · Proof-of-Impact (PoI)** | spec only | ~400 | trace agent action → cited memory · NAU-link · RL signal |
| **NEW · drift gate at 3 stages** | spec only | ~250 | write + recall + act |

**Verify criteria**: agent action `pf_score_bounty` has provable cite trail back to memory M. M gets +1 impact score.

### Layer 5 · Adoption (NEW · borrow from GBrain framing)

| Component | Status | LOC estimate | Dependency |
|---|---|---|---|
| `pip install nautilus-compass` | shipped v1.6.2 | — | PyPI |
| **NEW · `npx nautilus-compass init`** | spec only | ~200 | npm wrapper · already exists (v1.6.2) · add `init` subcommand |
| **NEW · "Opinionated EvoMap" framing in README** | spec only | ~150 lines docs | brand · 真 product 升级 |
| **NEW · bun support** | spec only | ~20 lines package.json | trivial |

**Verify criteria**: 1-command init creates `.compass/` dir + `.env` template + sample anchor set + Claude Code hooks wired.

---

## Ship order (anti-D-maintenance · 1 layer at a time · NOT全做)

| Sprint | Layer | Week | Why first | Effort |
|---|---|---|---|---|
| **S1** | Layer 3 · `depends_on:` field only | week 1 | Seokwon window 3-7 day · academic P0 | 6h |
| S2 | Layer 5 · npx init + bun + framing | week 2 | low risk · adoption signal · GBrain-validated | 1d |
| S3 | Layer 2 · L1 overview + viking:// adapter | week 3-4 | proven OV pattern · long-session scale | 1w |
| S4 | Layer 4 · PoI + drift gate 3-stage | week 5-7 | compass唯一 · 真 differentiation | 2w |
| S5 | Layer 1 · drift-as-routing | week 8 | small but valuable · ship after PoI is real | 3d |
| S6 | Layer 2 · L2 nightly dream-layer | week 9-10 | last · local Ollama infra heavy | 1w |
| **S7** | paper3-MEME-extension submit arXiv | week 11-12 | depends on S1 + S3 + S4 done | 4-6w total |

---

## Drop-from-v2.0 list (anchor #5 anti-reinvention)

- ❌ Cognitive arch episodic/semantic split (MemGPT trodden)
- ❌ Multi-agent shared memory protocol (A2A territory)
- ❌ NAU staking on memory (platform / DMAS territory)
- ❌ Cross-LLM jury (heavy · low ROI)
- ❌ Federated learning (privacy-tax not paid)
- ❌ OpenViking ingest-time LLM extract (kills compass core diff)

---

## 7 truly unique components (no system has all 7)

1. Black-box ingest ($3.50 / 100M)
2. Drift detection AUC 0.83 (25+35 anchor)
3. Proof-of-Recall cite-verify
4. **NEW · Proof-of-Impact action-trace**
5. **NEW · `depends_on:` cascade chain**
6. **NEW · 3-stage drift gate (write/recall/act)**
7. numeric_claims cross-ref

paper3-MEME-extension highlights #5 (Seokwon co-validated). Future paper-4 candidate covers #4 PoI.

---

## Open decisions (defer to fresh session)

- [x] Is OpenViking AGPLv3 compatible with compass MIT? **Resolved 2026-05-22**: NO (root LICENSE WebFetch verified AGPL-3.0). Strategy: reimplement paradigm from scratch · DO NOT fork/link.
- [ ] L2 distillation: Ollama Qwen 2.5 7B local · or remote DeepSeek-v3.2 (current writer model)?
- [ ] Paper-4 PoI: standalone paper or merge into v2.0 systems paper?
- [ ] caishen platform: which V5 agent first wires PoR (anchor #1 dogfood)?

---

— compass-dialog draft · 2026-05-19 17:30 CST · loop iter 2 close · audit-only · code ship 留 fresh session
