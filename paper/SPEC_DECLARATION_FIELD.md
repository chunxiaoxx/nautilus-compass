# SPEC · `depends_on:` Declaration Field

**Status**: Design spec · 2026-05-19 · paper3-MEME-extension P0 contribution
**Scope**: compass v2.0 Layer 3 (chain) · v1.7 ship target
**Not**: implementation · this is design only
**Relation**: `paper/OUTLINE_PAPER3_MEME_EXTENSION.md` §3.1 · `paper/COMPASS_V2_SPEC_DRAFT.md` Layer 3

---

## 0. Why this spec exists

MEME (Jung et al. arXiv 2605.12477) benchmarks `Cas / Del / Abs`. Current compass v1.6.2 hits Cas 12.8% on 100ep nofiller (paper avg 3% · +9.8pp absolute), but the dataset is `nofiller` so unfair vs published `filler32k`. Seokwon Jung 5/19 verbatim: *"we'd expect it to do well, especially on Absence ... your repo is the natural home for the adapter."* The P0 contribution that makes Cas jump (estimate 35-50%) is **explicit cross-observation dependency at ingest time, without LLM extraction**. This spec defines it.

Design philosophy borrowed:
- **OpenViking** L0/L1/L2 hierarchical layering · we slot `depends_on:` into L0 metadata so L1/L2 distill can DAG-walk.
- **GBrain** Minion+LLM separation · ingest stays black-box (no LLM at write · `$3.50/100M tokens` invariant from v1.6.2 holds), LLM only at retrieval-time judging.

---

## 1. Frontmatter schema

Add **one optional list field** to existing v0.8 session_*.md frontmatter (see `session_writer.py:46-64` for current schema). Backward compatible: omitting `depends_on:` MUST not break ingest or recall.

```yaml
---
name: session-2026-05-19-cascade-X
description: After X, we decided Y because of Z.
type: decision
concept: problem-solution
drift: green
drift_signals: []
thread_id: thread_paper3_meme
thread_role: self_note
# NEW · v1.7 · MEME-extension P0
depends_on:
  - session_20260518-event-Y.md          # explicit ancestor (file basename)
  - session_20260517-event-Z.md
declaration_type: cascade                # NEW · enum: cascade | absence | deletion | none
                                         # cascade = needs ancestors to interpret
                                         # absence = asserts "X did NOT happen" (MEME Abs)
                                         # deletion = supersedes/retracts an earlier obs (MEME Del)
                                         # none = standalone (default if omitted)
supersedes:                              # NEW · OPTIONAL · only when declaration_type=deletion
  - session_20260510-old-claim.md
---
```

**Field semantics (binding)**:

| field | type | required | meaning |
|---|---|---|---|
| `depends_on:` | list[str] | optional | file basenames of ancestor session_*.md · order = causal order |
| `declaration_type:` | enum | optional · default `none` | cascade / absence / deletion / none |
| `supersedes:` | list[str] | optional · only valid when `declaration_type=deletion` | which obs(s) this entry retracts |

**Why basenames not paths**: paths bind to a project root; basenames are stable across `claude-mem` rename and cross-project recall. The recall pass at `recall.py:176-210` already keys on `path.name`.

**Naming-collision note**: `depends_on:` already exists in `mcp_server.py:983,991,1047,1122,1147,1170` for V7 phase-DAG task orchestration (V7 actuator-collapse spec). The two namespaces are **disjoint** — V7 uses it inside `pf_observation` task definitions; this spec uses it inside `session_*.md` memory frontmatter. The parser at `recall.py:182-189` only reads session frontmatter, so no collision occurs. Spec writers MUST keep this disjoint — do NOT route memory `depends_on:` through V7's `phase_id` graph.

---

## 2. Ingest hook · where the parser plugs in

### Two ingest paths exist today (both must accept the new field)

| path | trigger | current hook point |
|---|---|---|
| **A · auto** | session end · Claude Code Stop hook | `stop_hook.py:39-56` finds latest `session_*.md` · `session_writer.py:281-289` writes it · downstream `cloud_ingest.py:249-253` pushes to remote |
| **B · explicit** | agent calls `tool_ingest_obs` via MCP | `mcp_server.py:392-479` (current `tool_ingest_obs`) · writes `session_*.md` at line 444 |

### Hook patches required

**Path A · session_writer SYSTEM_PROMPT** (`session_writer.py:46-64`):

Add 3 lines to the YAML template the LLM distiller fills. The distiller (DeepSeek-v3.2 currently) already fills `contracts:` (lines 53-63) — `depends_on:` follows the same nested-YAML pattern, so prompt cost is ~12 extra prompt tokens.

```text
# Add after line 52 (drift_signals) in SYSTEM_PROMPT:
depends_on: [<0-5 file basenames of session_*.md this entry causally depends on · empty list if standalone>]
declaration_type: <cascade | absence | deletion | none>
supersedes: [<only when declaration_type=deletion · file basenames being retracted>]
```

The distiller has the full transcript in context already, so dependency identification is a free side-effect of summarization — **no separate LLM call**, no break of black-box ingest invariant.

**Path B · `tool_ingest_obs`** (`mcp_server.py:392-479`):

Add to function signature parsing block (insert after line 424, before line 426 PoR validation):

```python
depends_on = args.get("depends_on") or []
declaration_type = (args.get("declaration_type") or "none").strip()
if declaration_type not in ("cascade", "absence", "deletion", "none"):
    declaration_type = "none"
supersedes = args.get("supersedes") or []
if declaration_type != "deletion":
    supersedes = []  # only valid when deletion
```

Emit into frontmatter block (insert after line 450 `thread_lines`):

```python
dep_lines = ""
if depends_on:
    dep_lines += "\ndepends_on:\n  - " + "\n  - ".join(depends_on)
dep_lines += f"\ndeclaration_type: {declaration_type}"
if supersedes:
    dep_lines += "\nsupersedes:\n  - " + "\n  - ".join(supersedes)
```

Append `dep_lines` to the `md` f-string at line 454-473 (insert between `proof_lines` and the closing `---`).

Update `inputSchema` block (`mcp_server.py:1202-1206`) to advertise the three new args.

**LOC**: schema parser ~30 LOC across both paths combined.

---

## 3. Recall hook · transitive BFS

### Current recall (no chain awareness)

`recall.py:603-665` ranks entries by cosine, takes `TOP_K` (default 5), renders top-3 with full body (`BODY_TOP=3`). Frontmatter is parsed at `recall.py:176-210` into a `dict` that currently throws away unknown keys (loop at lines 186-189 keeps all but downstream `return` dict at 199-210 doesn't surface them).

### Patch

**3a · widen parser** (`recall.py:199-210`): add `"depends_on": fm.get("depends_on", []), "declaration_type": fm.get("declaration_type", "none"), "supersedes": fm.get("supersedes", [])` to the returned dict. The YAML list parsing at line 186-189 currently does `partition(":")` which produces a single string for list-valued YAML — strengthen this single block to detect indented `- ` list items and accumulate. ~15 LOC.

**3b · transitive BFS pass** (new function, insert after `render_v02_vector_mode` at `recall.py:603`):

```text
def transitive_close(top: list, all_entries: list, max_depth: int = 3) -> list:
    """v1.7 · MEME chain · expand top-K with ancestors via depends_on BFS.

    Returns top + reachable ancestors, deduped, preserving cosine order of seeds.
    Ancestors are NOT re-cosined; they are pinned because the seed declared them.
    Depth cap = 3 (Seokwon noted 32k filler dataset has avg chain depth 2.4).
    """
    index = {e["path"]: e for e in all_entries}
    seen = {e["path"] for _, e in top}
    out = list(top)
    frontier = [(0, e) for _, e in top]
    while frontier:
        depth, e = frontier.pop(0)
        if depth >= max_depth:
            continue
        for parent_name in e.get("depends_on", []) or []:
            parent = index.get(parent_name)
            if parent is None or parent["path"] in seen:
                continue
            seen.add(parent["path"])
            # synthetic score: -depth · sort below cosine top but above fresh fallback
            out.append((-depth - 1.0, parent))
            frontier.append((depth + 1, parent))
    return out
```

Call site: `recall.py:640` between `top = scored[:TOP_K]` and `if not top:`. Wrap with env flag `COMPASS_CHAIN_RECALL=1` for v1.7 staged rollout.

**3c · cascade closure verifier** (new function, also lives near transitive_close):

```text
def verify_cascade_closure(top: list, query: str) -> dict:
    """Given recall result and a query targeting a 'cascade' obs · verify that
    every depends_on ancestor of every cascade-typed top hit is also in top.
    Returns {"complete": bool, "missing": [...], "cascade_hits": int}.
    For MEME bench Cas scoring."""
```

Used only by the eval harness (`code/agents/compass_memory.py` MEME adapter), not by production recall path. ~30 LOC.

**LOC**: recall hook ~50 LOC total (15 parser + 30 BFS + verifier ~30 if eval-side).

---

## 4. Cascade closure experiment (MEME bench)

| variable | values | rationale |
|---|---|---|
| `depends_on` | on / off | core ablation |
| `drift_filter` | on / off | confirm drift doesn't drop chain ancestors |
| `BFS depth` | 1 / 2 / 3 | dataset chain-depth distribution |
| filler | nofiller / filler32k | Seokwon comparability |

**Hypothesis (testable)**: with `depends_on:` on · BFS=3 · filler32k · Cas accuracy → **35-50%** (vs published baseline avg 3% · vs compass-current 12.8% nofiller).

**Null result criterion**: if `depends_on:` on yields Δ Cas < +10pp absolute over `off`, the schema field is **not a sufficient causal mechanism** and the paper3 P0 contribution claim fails. Pre-register this threshold before E3 runs.

**Pass criterion**: Cas Δ ≥ +20pp absolute AND Del/Abs not regressed by > -3pp (lateral integrity check).

Test harness LOC: ~80 LOC sketch in `code/agents/compass_memory.py` (already exists from E1 run · extend ingest path to fill `depends_on:` from MEME ground-truth DAG · extend recall path to call `transitive_close`).

---

## 5. LOC budget summary

| component | file | LOC estimate |
|---|---|---|
| schema parser (both ingest paths) | `session_writer.py` + `mcp_server.py` | ~30 |
| ingest hook patch (mcp tool + schema) | `mcp_server.py:421-479,1202-1206` | ~20 |
| recall parser widen + BFS + verifier | `recall.py:176-210,603` | ~50 |
| MEME eval harness extension | `code/agents/compass_memory.py` | ~80 |
| **total** | | **~180 LOC** |

Ship effort: 6h (per `paper/COMPASS_V2_SPEC_DRAFT.md` S1 sprint), excluding 24-48h GPU for filler32k re-run (E2 + E4).

---

## 6. Open decisions (defer · NOT in this spec)

- [ ] Auto-extract `depends_on:` via post-hoc DAG inference for un-tagged legacy memory (~7000 existing session_*.md). Out of scope for v1.7 · paper4 candidate.
- [ ] Should `supersedes:` trigger soft-delete of the superseded entry from recall index, or just down-weight? Down-weight = safer · pick down-weight for v1.7, revisit after MEME Del numbers come in.
- [ ] Cross-project chain (depends_on a session in a different project)? v1.7 = same-project only. Cross-project = S3 spec territory (see `specs/SPEC-S3-cross-project-recall.md`).

---

— compass-dialog · paper3-MEME-extension P0 design spec · 2026-05-19 · audit-only · no code shipped
