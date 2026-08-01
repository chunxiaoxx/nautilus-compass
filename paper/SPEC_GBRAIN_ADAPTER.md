# SPEC · GBrain Adapter for nautilus-compass v2.0

**Status**: Spec design only · no implementation · 2026-05-19
**Scope**: framing + attribution + borrowed-pattern matrix · NOT code
**Companion specs**: `SPEC_OV_ADAPTER.md` (L0/L1/L2 hierarchical storage) · `SPEC_DECLARATION_FIELD.md` (MEME-extension `depends_on:` field)
**Parent**: `COMPASS_V2_SPEC_DRAFT.md` Layer 5 (adoption)

---

## 1. Design philosophy (真借)

compass v1.6.2 ships **no LLM at ingest** ($3.50 / 100M tokens · BGE-m3 anchor index only). All measured baselines (mem0, Letta, Cognee, Zep, MemOS) burn LLM tokens at write time to extract entities/relations.

GBrain (github.com/garrytan/gbrain · MIT · Garry Tan / Y Combinator CEO · 2026-04-05 · 14k stars) ships the same core split under explicit framing:

> *"most knowledge management operations are deterministic and don't need an LLM. GBrain wipes that cost to zero."* — GBrain README (verbatim)

**Conclusion**: compass's "no LLM at ingest" is an independent same-family implementation of GBrain's **Minion (deterministic) + LLM (non-deterministic) split**. We adopt GBrain's framing as prior art and cite it explicitly — we did not invent the split, we shipped a same-family system.

**Retraction**: prior compass spec docs (`COMPASS_V2_SPEC_DRAFT.md` Layer 5, paper1, paper2 OUTLINE) cite OpenViking and MEME but omit GBrain. This is incomplete attribution. This spec corrects it.

---

## 2. Minion (deterministic) inventory · compass current mapping

| Minion operation | compass component | Status |
|---|---|---|
| parse markdown / extract frontmatter | `stop_hook.py` | ✅ shipped |
| BGE-m3 embed + cosine recall | `daemon.py` + `recall.py` | ✅ shipped v1.6.2 |
| drift_check (25+35 anchor AUC 0.83) | `daemon_anchor_apply.py` | ✅ shipped v1.6.2 |
| numeric_claims regex (anti-hallucination) | `audit_kpi.py` | ✅ shipped v1.5.2 |
| cite validation (Proof-of-Recall) | mcp_server `_validate_recall_proof` | ✅ shipped v1.5.2 spec |
| keyword retrieval | `session_search.py` | ✅ shipped |
| **link build `[[name]]` resolution** | — | ❌ NEW · borrow GBrain pattern |
| **schema parse `depends_on:` field** | — | ❌ NEW · see `SPEC_DECLARATION_FIELD.md` |

---

## 3. LLM (non-deterministic) inventory · compass v2.0 expansion

| LLM operation | compass component | Status |
|---|---|---|
| L2 nightly distillation (Ollama Qwen 2.5 7B · local · 0 token cost) | — | ❌ NEW · see `SPEC_OV_ADAPTER.md` |
| 6-agent prompt-pass for Proof-of-Recall (V5 / V7 / Kairos / HR / Hr-web / 创投日报) | `COMPASS_V2_SPEC_DRAFT.md` Layer 4 L57 | ❌ NOT shipped · prompts only |
| `depends_on:` DAG auto-inference (future · text → field) | — | ❌ NEW (post-v2.0) |

**Anchor**: compass core diff (no LLM at *ingest*) is preserved. LLM work moved to *consolidation* (nightly batch) and *agent-side* (prompt pass) — never on the hot ingest path.

---

## 4. "Opinionated EvoMap" framing

GBrain's brand is **opinionated** (strong-schema · convention-over-config). compass v2.0 adopts this framing for Layer 5 (adoption):

- **README rewrite**: tagline shifts from *"cross-agent memory layer"* → **"Opinionated EvoMap · deterministic-first · no LLM at ingest"**
- **`npx nautilus-compass init`** scaffolds: `.compass/` dir + `.env` template + anchor set (default = `anchors.json` · domain packs available) + Claude Code `stop_hook` wired
- **Convention enforced**: frontmatter required (`thread_id`, `thread_role`, optional `depends_on:`) — non-conforming files quarantined, not silently ingested
- **Brand line**: "compass is to memory what TypeScript is to JS — opinionated schema buys you cascade closure, drift gates, and Proof-of-Recall for free"

---

## 5. Borrowed-item matrix (each item · honest status)

| GBrain item (verbatim from README / brain-vs-memory.md) | compass current | Borrow path |
|---|---|---|
| auto-fix references | ❌ none | NEW · derive from validated `depends_on:` field (`SPEC_DECLARATION_FIELD.md`) |
| overnight memory consolidation | ❌ none | NEW · L2 nightly distillation (`SPEC_OV_ADAPTER.md`) |
| contradiction detection | 🟡 partial (numeric_claims only) | EXTEND · semantic contradictions via L2 distill pass |
| trajectory regression flag | ❌ none | NEW · drift gate at 3 stages (`COMPASS_V2_SPEC_DRAFT.md` Layer 4) |
| PostgreSQL backend | 🟡 sqlite now (v0.9.1 has Postgres-path planned) | BORROW · GBrain validates Postgres path · prioritize for v2.0 |
| keyword retrieval | ✅ shipped (`session_search.py`) | none — already converged |
| Minion + LLM split (philosophy) | ✅ shipped (no LLM at ingest) | CITE as prior art · framing borrowed |
| opinionated schema | 🟡 frontmatter convention exists, not enforced | EXTEND · `npx init` enforces · quarantine non-conforming |

---

## 6. Cross-spec relationships

- **`SPEC_OV_ADAPTER.md`** (separate · L0/L1/L2 hierarchical storage · OpenViking `viking://` URI adapter) — provides the *infrastructure* for GBrain-style overnight consolidation. L2 = compass's "dream layer" = GBrain's "overnight consolidate".
- **`SPEC_DECLARATION_FIELD.md`** (separate · MEME-extension paper3) — provides the *schema* (`depends_on:`) that makes GBrain-style auto-fix-references deterministic (no LLM needed to infer the link · the field declares it).
- **`COMPASS_V2_SPEC_DRAFT.md` Layer 5** (parent) — this framing *is* Layer 5 adoption work. README rewrite + `npx init` + brand line ship under sprint S2 (week 2).

---

## Attribution checklist (must appear in every v2.0 README / paper / promo)

- [ ] GBrain cited as prior art for Minion + LLM split (with link + verbatim quote)
- [ ] "Opinionated EvoMap" tagline credits GBrain's "opinionated" framing
- [ ] Acknowledgment: Garry Tan / GBrain (MIT · 14k stars) in README §Acknowledgments
- [ ] paper3 §Related Work cites GBrain alongside MEME, OpenViking, mem0, Letta, MemOS

---

## References (verbatim sources)

- **GBrain** · github.com/garrytan/gbrain · MIT · 14k stars (2026-05-19 snapshot)
- **GBrain brain-vs-memory.md** · "*most knowledge management operations are deterministic and don't need an LLM*" — verbatim from README
- **gbrain-evals** · github.com/garrytan/gbrain-evals · companion benchmark harness
- **Author** · Garry Tan · Y Combinator CEO · open-sourced 2026-04-05
