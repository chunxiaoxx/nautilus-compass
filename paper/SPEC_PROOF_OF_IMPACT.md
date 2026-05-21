# SPEC · Proof-of-Impact (PoI) · compass v2.0 Layer 4

> **Status**: Design only · 2026-05-21 · code ship deferred (~2 weeks effort)
> **Target**: v2.0 Layer 4 "Proof" tier · compass-only differentiation
> **Total LOC estimate**: ~400 (schema + calculator + emitter + MCP tool + drift gate + weighting)
> **Paper-4 candidate**: per v2 spec line 110

---

## 1. Context · why PoI

compass v1.5.2 already ships **Proof-of-Recall (PoR)**:
- `recall_token` (30min TTL) + `cited_snippets` validation
- Frontmatter `proof_of_recall: pass | fail | not_attempted`
- Verifies agent actually consumed top-K hits at recall time

PoR answers: *"Did the agent see the memory?"*

PoR cannot answer: **"Did the cited memory actually drive the agent's eventual action, and was the action useful?"**

### Failure modes PoR cannot catch

1. Agent recalled memory M, cited it formally, then ignored it · prior training won
2. Agent recalled M, cited it, took action that contradicts M
3. Agent recalled M, cited it, action used M correctly · M's *value* should be rewarded
4. Agent recalled stale/wrong M, cited it, action failed because M was misleading

PoI fills this gap: trace from **action outcome** back to memory M, score the memory's contribution, and emit a deterministic signal.

---

## 2. Design constraints (anchored)

- ✅ **No LLM at impact assessment** (compass core diff · violation kills the constraint)
- ✅ **Schema-driven score** (action outcome + cite list → score · arithmetic only)
- ✅ **Works for V5 / V7 / Kairos / HR-agent · all NAU-economy-aware agents**
- ❌ **NOT real-time RL gradient** (too expensive · use as offline credit signal accumulated to memory frontmatter)
- ❌ **NOT LLM judge of "did action use memory"** (subjective · violates determinism)

---

## 3. PoI schema

### 3.1 Python dataclass

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ProofOfImpact:
    action_id: str                       # external action ID (V5 bounty_id, V7 task_id, etc.)
    agent_id: str                        # acting agent
    cited_memory_paths: list[str]        # session_*.md paths (from prior PoR cite list)
    action_outcome: str                  # "success" | "failure" | "partial" | "pending"
    impact_score: float                  # 0.0 to 1.0 (or negative for failure penalty)
    timestamp_action: str                # ISO8601 when action started
    timestamp_outcome: str               # ISO8601 when outcome observed
    nau_emit: Optional[float] = None     # NAU to memory creators (None if no economy)
    declaration_type: str = "supports"   # "supports" | "contradicts" | "neutral"
    notes: str = ""                      # ≤200 char optional narrative
```

### 3.2 Memory frontmatter feedback (cumulative)

Memory `session_*.md` gains an automatic field updated by PoI events:

```yaml
---
# existing v1.7.1 fields
tier: working
decay_rate: 0.5
forget_at: null
promote_after: "5_access"
reinforce_count: 0
# NEW · PoI cumulative (v2.0)
cumulative_impact: 0.0                   # sum of impact_score across PoI events
impact_event_count: 0                    # number of PoI events touching this memory
last_impact_at: null                     # ISO8601 latest PoI event
---
```

---

## 4. Deterministic impact score formula (no LLM call)

```
impact_score = outcome_weight * cite_factor * drift_penalty

outcome_weight =
  +1.0  if action_outcome == "success"
  +0.5  if action_outcome == "partial"
  -0.5  if action_outcome == "failure"     (penalty signal · memory was misleading)
   0.0  if action_outcome == "pending"     (defer until resolved)

cite_factor = min(1.0, len(cited_memory_paths) / 3.0)
  # rationale: spread credit across cites · 3+ cites get full credit · single cite gets 0.33
  # prevents one memory hoarding all credit

drift_penalty = 1.0 if all cited memories have drift in {green, none}
              = 0.5 if any has drift == "yellow"
              = 0.1 if any has drift == "red"
  # red-drift cite still counts but heavily down-weighted
```

### 4.1 Examples

| outcome | cites | drift | impact_score |
|---|---|---|---|
| success | 1 path · all green | green | +0.33 |
| success | 3 paths · all green | green | +1.0 |
| success | 5 paths · 1 red | red | +0.10 |
| partial | 2 paths · all green | green | +0.33 |
| failure | 2 paths · all green | green | -0.33 |
| failure | 1 path · yellow | yellow | -0.165 |
| pending | any | any | 0.0 |

---

## 5. NAU emission (anchor #2 customer · platform economy)

### 5.1 Emission rule

```
For each cited_memory_path m:
  creator_agent = read_creator_from_frontmatter(m)  # frontmatter.agent_type
  if creator_agent == acting_agent_id:
    continue  # self-citation suppressed · prevents NAU farming
  nau_amount = impact_score * BASE_NAU_PER_ACTION / cite_factor
  emit_to_sidecar(creator_agent, nau_amount, m, action_id)
```

### 5.2 Configuration

```
COMPASS_POI_BASE_NAU=1.0       # default NAU per full-credit action
COMPASS_POI_SUPPRESS_SELFCITE=true  # default true · prevent self-farming
COMPASS_POI_PLATFORM_DB=nautilus_production  # V5 platform DB target
```

### 5.3 Sidecar format

`~/.claude/plugins/nautilus-compass/.cache/poi_emit.jsonl`:

```json
{"ts":"2026-05-21T...","actor":"V5","creator":"Kairos","memory":"session_X.md","action":"b-abc","nau":0.66}
```

Platform-side consumer (V5 nautilus_production.poi_emit table) reads sidecar and applies NAU transfers within bounty completion flow.

---

## 6. 3-stage drift gate integration

compass already has 2 of 3 stages shipped:

| Stage | Gate | Status | What it does |
|---|---|---|---|
| **Write** (v1.6.2) | `drift_check` at ingest | ✅ shipped | Anchor-based score · red entries flagged on write |
| **Recall** (v1.5.2) | `drift_check` at recall | ✅ shipped | Red excluded from top-K · yellow caveat tag |
| **Act** (NEW · PoI) | drift gate post-action | ❌ this spec | Cite-from-red + outcome=failure → strong drift signal |

### 6.1 Act-stage logic

```python
# nautilus_compass/drift/gate_act.py
def act_stage_drift_check(poi: ProofOfImpact) -> dict:
    """Analyze PoI event for drift signals at act time."""
    signals = []
    cited_drifts = [load_drift(m) for m in poi.cited_memory_paths]
    if poi.action_outcome == "failure":
        if any(d == "red" for d in cited_drifts):
            signals.append({"severity": "high", "reason": "red-drift cite + failure"})
        elif any(d == "yellow" for d in cited_drifts):
            signals.append({"severity": "medium", "reason": "yellow-drift cite + failure"})
    if poi.declaration_type == "contradicts" and poi.action_outcome == "success":
        signals.append({"severity": "high", "reason": "action contradicts cite + still succeeded · memory may be stale"})
    return {"signals": signals, "count": len(signals)}
```

Signal accumulated to `.cache/drift_act_log.jsonl` for D13-style decision matrix (see 5/17 sprint baseline 15.05h close_loop_mean target).

---

## 7. Recall-time PoI weighting

Memories with high `cumulative_impact` should rank higher in future recalls (positive feedback loop · validated memories surface first).

```python
# nautilus_compass/recall/poi_weighting.py
def apply_poi_boost(cosine_score: float, memory_frontmatter: dict,
                    boost_factor: float = 0.1) -> float:
    """Boost cosine by cumulative impact · capped at 2x base score."""
    cumulative = memory_frontmatter.get("cumulative_impact", 0.0)
    # Asymptotic boost · prevents unbounded ranking
    boost = min(1.0, max(-0.5, cumulative * boost_factor))
    return cosine_score * (1.0 + boost)
```

Negative cumulative impact (memory caused failures) → ranking demotion.

---

## 8. Implementation plan · ~400 LOC

| Module | Path | LOC | Description |
|---|---|---|---|
| `poi_schema.py` | `nautilus_compass/proof/poi_schema.py` | 50 | ProofOfImpact dataclass + validators |
| `poi_calculator.py` | `nautilus_compass/proof/poi_calculator.py` | 80 | Deterministic impact score formula |
| `poi_emitter.py` | `nautilus_compass/proof/poi_emitter.py` | 70 | Sidecar write + frontmatter cumulative update |
| MCP tool patch | `mcp_server.py` `tool_proof_of_impact` | 80 | MCP tool · register in TOOLS dict |
| `drift/gate_act.py` | `nautilus_compass/drift/gate_act.py` | 60 | Act-stage drift gate |
| `recall/poi_weighting.py` | `nautilus_compass/recall/poi_weighting.py` | 60 | Recall ranking boost from cumulative impact |
| **Total** | | **~400** | |

---

## 9. Verification criteria

### 9.1 Smoke test (12 cases · deterministic · LLM-free)

1. PoI calculator · success outcome + 1 cite all green → `+0.33`
2. PoI calculator · success outcome + 3 cites all green → `+1.0`
3. PoI calculator · failure outcome + 2 cites all green → `-0.33`
4. PoI calculator · pending outcome + any → `0.0`
5. PoI calculator · success + cite has 1 red → impact \* 0.1 down-weight
6. NAU emit · creator != actor → sidecar entry written
7. NAU emit · creator == actor → suppressed (self-cite)
8. drift act-gate · red cite + failure → high-severity signal logged
9. drift act-gate · success + supports → no signal
10. recall weighting · high cumulative_impact → boosted rank
11. MCP tool · valid PoI args → 200 OK
12. Backward compat · recall path works without PoI sidecar

### 9.2 Production verification (post-ship · 2-week observation)

- V5 platform · ≥ 50 bounties produce PoI events in 7 days
- NAU economy · ≥ 1 cross-agent NAU transfer (Kairos memory → V5 actor)
- Drift act-gate · ≥ 3 high-severity signals captured + manual review
- Recall · Top-K composition shows high-impact memories surfacing

---

## 10. Open questions (defer)

- `BASE_NAU_PER_ACTION` default value (proposed 1.0 · platform decides at config time)
- L1 overview cite (from S3) · distribute impact to L1 members or credit L1 as unit?
- Cross-agent delegate actions (A delegates to B) · who owns impact?
- Long-tail outcome observation (30+ days lag) · re-emit policy
- Impact decay over time (use lifecycle `decay_rate` from llm-wiki2 fuse · already shipped)

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Outcome observation lag · PoI sits as `pending` forever | TTL on pending PoI · auto-`partial` after 30 days |
| Self-citation NAU farming | `COMPASS_POI_SUPPRESS_SELFCITE=true` default |
| Recall dominated by high-impact stale memory | Apply lifecycle `decay_rate` to cumulative_impact too · stale slowly demoted |
| LLM-free under-fits "true" value | Accept · alternatives violate core constraint · paper-4 will make this explicit |
| V5 platform DB schema change required | Coordinate with V5 dialog · separate sprint · NOT bundled |

---

## 12. Anchor contributions

| Anchor | Contribution |
|---|---|
| #1 agent first | PoI is what makes memory **valuable to** super-agents · they get credit for good memories |
| #2 真客户 onboard | Platform economy hook · NAU transfer is a real revenue/credit signal |
| #3 anti-D-maintenance | Single sprint · 400 LOC · clean 6-module breakdown |
| #4 differentiation | **Compass-only feature** · no other memory project has act-stage proof |
| #5 anti-reinvention | Reuses existing PoR (v1.5.2) + drift_check (v1.6.2) + lifecycle decay (v1.7.1) |
| #7 anti-overclaim | 12 smoke + 2-week production observation criteria explicit |

---

## 13. Why PoI matters for paper-3 / paper-4

paper-3 (MEME extension) currently claims novelty on declaration_field. PoI is a **separate paper-4 candidate** because:

- It's not in MEME's scope (MEME = memory benchmark, not action-impact)
- It connects compass to **platform economy** (NAU) · expands beyond pure memory layer
- It demonstrates **schema-driven RL signal** without LLM judge · a non-trivial claim

**Defer paper-4 writeup until PoI ships + 2-week production data.**

---

## 14. Sequence (ship order in 2-week sprint)

| Day | Module | Notes |
|---|---|---|
| 1-2 | `poi_schema.py` + `poi_calculator.py` | Pure logic · easy smoke (12 cases) |
| 3 | `poi_emitter.py` + sidecar format | Filesystem-only · no platform DB yet |
| 4-5 | MCP tool patch `mcp_server.py` | Follow add_worker pattern (Phase 2.B) |
| 6 | Frontmatter cumulative update logic | Touches recall.py · careful regression check |
| 7-8 | `drift/gate_act.py` + log sidecar | Logged-only initially · no auto-action |
| 9 | `recall/poi_weighting.py` | Optional boost · feature flag `COMPASS_POI_WEIGHTING=1` |
| 10 | Smoke 12 cases + backward-compat regression check | All v1.7.1 tests must still pass (31/31) |
| 11-14 | V5 platform DB sidecar consumer · separate coord with V5 dialog | NOT bundled in this sprint |

---

## 15. Related ship trail

- v2 spec source · `paper/COMPASS_V2_SPEC_DRAFT.md` Layer 4
- PoR (predecessor) · `mcp_server.py:_validate_recall_proof` (shipped v1.5.2)
- drift_check · `recall.py:drift_check_via_daemon` (shipped v1.6.2 + sidecar v1.7.0)
- Cite mechanism · `session_writer.py:46-67` `cited_snippets` field
- Lifecycle decay · `recall.py:promote_lifecycle_tier` (shipped 5/22 d1764e3)
- 3-stage drift gate spec · `paper/COMPASS_V2_SPEC_DRAFT.md` Layer 4
- Plan reference · `~/.claude/plans/scalable-drifting-seahorse.md`
- Companion spec · `paper/SPEC_LAYER2_L1_REWRITE.md` (S3 · shipped this session)
