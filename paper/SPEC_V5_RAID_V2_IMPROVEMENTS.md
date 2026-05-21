# SPEC · V5 RAID-2 Improvements for High-Fidelity Code Dispatch

> **Status**: Design proposal · 2026-05-21 · written by compass-dialog after live audit
> **Audience**: nautilus-v5-dialog / V5 platform team
> **Trigger**: 2 live RAID-2 dispatches of compass bounties both produced 100% wrong task fidelity at 0.65-0.75 consensus score
> **Strategic anchor**: #1 agent first (platform agents implement, I write spec) requires RAID-2 to actually deliver fidelity

---

## 1. Audit evidence (verbatim · 2026-05-21 21:00-23:00 CST)

### 1.1 Compass pilot bounties (both failed task fidelity)

| Bounty | Spec context | RAID-2 output | Score | Fidelity |
|---|---|---|---|---|
| `b-l1-cli` | "compass v2.0 L1 builder CLI · 20 LOC Python · spec: paper/SPEC_LAYER2_L1_REWRITE.md" | Blockchain L1 (genesis block / node peers / hashing) | 0.75 | 0% |
| `b-l1-cli-v2` | Self-contained: "compass v1.7.1 · L1 overview tier · NOT blockchain · Python under 30 LOC · use argparse · do NOT add genesis/nodes" | Rust project (Cargo.toml + 60+ `.rs` files + tokio + clap) | 0.65 | 0% |

### 1.2 V5 own bounties (sampled · all failed)

| exec_id | Topic | Output | Score | Fidelity |
|---|---|---|---|---|
| `4f3f14a8-b7c` | "V5 cycle audit · platform critical fix" | "I don't have access to internal audit logs" | 0.88 | 0% (null) |
| `101f3720-a29` | "V5: Break the monitoring wheel" | Cybersecurity NTP attack guide | 0.85 | 0% |
| `43ef17de-d5c` | "harmony 长期低位" (V5 internal metric) | Harmony **ONE** cryptocurrency analysis | 0.89 | 0% |

### 1.3 Distribution from raid_executions (n=858)

| Score bucket | Count | Percent |
|---|---|---|
| ≥ 0.80 | 477 | 55.6% |
| 0.60 - 0.79 | 35 | 4.1% |
| 0.40 - 0.59 | 127 | 14.8% |
| 0.20 - 0.39 | 91 | 10.6% |
| < 0.20 | 128 | 14.9% |

**Hypothesis confirmed**: high consensus_score does not correlate with task fidelity. Score measures reviewer-executor agreement on the (potentially wrong) interpretation, not adherence to the original task.

---

## 2. Root cause analysis (3 missing pieces)

### 2.1 No context injection
RAID-2 agents process the bounty title + description in isolation. They have no access to:
- V5 platform internal vocabulary (V5 "harmony" ≠ Harmony ONE crypto)
- Compass repository structure or v1.7.1 lifecycle
- Referenced SPEC files (`metadata.spec_ref` field unused by RAID API)
- User strategic anchors (anchor_user_strategic_compass · 7 stances)

**Result**: agents default to standard-domain interpretation (L1 = blockchain, harmony = crypto, monitoring = cybersecurity).

### 2.2 No fidelity reviewer role
Current RAID-2 has 2 roles: `executor` writes output, `reviewer` checks quality. Neither role verifies "did the output address THIS specific task" — they only check internal consistency of the output.

**Result**: a polite "I don't have access" gets approved at 0.88 because the reviewer agrees the response is internally consistent.

### 2.3 No constraint enforcement
Bounty descriptions declare hard constraints (language=Python · LOC limit=20 · scope=skeleton-only · domain=NOT-blockchain) but RAID-2 has no pre-flight check to reject outputs that violate these constraints.

**Result**: agents free-style on language/size/scope. v2's explicit "Python under 30 LOC NOT blockchain" still produced Rust 60-file project.

---

## 3. Proposed fixes

### 3.1 Context injection pipeline (~200 LOC, V5 RAID API patch)

```python
# nautilus_v5/api/raid/context_inject.py
def build_agent_context(bounty: dict) -> dict:
    """Assemble context bundle for RAID-2 agents."""
    return {
        "platform_glossary": load_v5_glossary(),  # V5 terms · harmony / monitoring / RAID / ...
        "spec_content": fetch_spec_ref(bounty["metadata"].get("spec_ref")),  # full SPEC file inline
        "compass_overview": read_compass_readme_top(200),  # what compass is
        "active_anchors": load_user_anchors(),  # 7 stances from anchor_user_strategic_compass
        "recent_commits": git_log_last_n(20),  # repo HEAD context
    }
```

Each RAID-2 agent receives this bundle as a `<context>` block prepended to the task description.

### 3.2 Fidelity reviewer role (~250 LOC, RAID-2 protocol extension)

Extend RAID-2 from 2-role (executor + reviewer) to 3-role (executor + reviewer + **fidelity_checker**):

```python
# nautilus_v5/api/raid/fidelity_checker.py
def fidelity_check(task_description: str, agent_output: str,
                   context: dict) -> dict:
    """Verify output addresses the SPECIFIC task, not a generic reinterpretation."""
    return {
        "fidelity_score": 0.0-1.0,  # separate from quality_score
        "constraints_violated": [...],  # which spec constraints were ignored
        "domain_drift": bool,  # did agent reinterpret to different domain (L1=blockchain etc)
        "null_response": bool,  # did agent decline to answer
    }
```

**Final consensus = `quality_score × fidelity_score`**. A 0.88-quality null-response becomes `0.88 × 0.0 = 0` correctly.

### 3.3 Constraint enforcement (~150 LOC, pre-flight gate)

Spec parser extracts hard constraints from bounty description:

```python
# nautilus_v5/api/raid/constraint_extractor.py
HARD_CONSTRAINT_PATTERNS = {
    "language": r"(?:must use|written in|Python|Rust|TypeScript|Go)",
    "loc_limit": r"under (\d+) LOC",
    "scope": r"(skeleton only|full implementation|stub)",
    "negative_domain": r"NOT (\w+)",  # "NOT blockchain"
}

def enforce_constraints(output: str, constraints: dict) -> dict:
    """Pre-flight check before reviewer/fidelity sees output."""
    violations = []
    if constraints.get("language") == "Python" and detect_language(output) != "python":
        violations.append("language_mismatch")
    if constraints.get("loc_limit") and count_loc(output) > constraints["loc_limit"] * 1.5:
        violations.append("loc_exceeded")
    return {"pass": len(violations) == 0, "violations": violations}
```

Output failing pre-flight is **rejected before consuming reviewer/fidelity rounds** · saves API cost + prevents wrong-domain outputs from inflating consensus.

---

## 4. Borrowing from compass v1.7.1 (cross-pollination)

compass v1.7.1 already has the right mechanism for declarative constraints:

| compass mechanism (already shipped) | RAID-2 application |
|---|---|
| `declaration_field` (depends_on / declaration_type / supersedes) | Bounty `requires_context` declaration · explicit context dependencies |
| `promote_lifecycle_tier` (schema-driven · LLM-free) | Constraint enforcement (rule-based · no LLM judge of "is this Python") |
| `verify_cascade_closure` (BFS validation) | Spec-content closure · ensure all `spec_ref` files reachable in context bundle |
| 9 lifecycle hooks (SessionStart / PostToolUse / etc) | RAID-2 round hooks · `PreReviewer` / `PostExecutor` / etc |

Total cross-pollination opportunity: **compass's schema-first paradigm is what RAID-2 needs**. Compass already proved this works at write time (no LLM at ingest); RAID-2 needs to apply the same paradigm at dispatch time.

---

## 5. Implementation plan · ~600 LOC

| Module | Path (V5 repo) | LOC | Description |
|---|---|---|---|
| `context_inject.py` | `nautilus_v5/api/raid/context_inject.py` | 200 | Section 3.1 |
| `fidelity_checker.py` | `nautilus_v5/api/raid/fidelity_checker.py` | 250 | Section 3.2 |
| `constraint_extractor.py` | `nautilus_v5/api/raid/constraint_extractor.py` | 100 | Section 3.3 extractor |
| `constraint_enforcer.py` | `nautilus_v5/api/raid/constraint_enforcer.py` | 50 | Section 3.3 enforcer + pre-flight |
| DB migration | `raid_votes` add `fidelity_score` + `constraints_violated` columns | minimal | Schema update |
| **Total** | | **~600** | |

---

## 6. Verification criteria

Re-dispatch `b-l1-cli-v2` (Python · 30 LOC · NOT blockchain) after V5 RAID-2 v2 ships:

| Expected outcome | Threshold | Indicates |
|---|---|---|
| consensus_score = quality × fidelity | ≥ 0.70 | Both dimensions pass |
| Output language detected | "python" | Constraint enforced |
| LOC count | ≤ 45 (1.5× limit) | Size enforced |
| Domain check | NOT contains "genesis"/"blockchain"/"node peers" | Domain enforced |
| Spec ref fetched | YES | Context injection worked |
| Fidelity score | ≥ 0.6 | Task understood, not reinterpreted |

If 4+ of 6 pass, RAID-2 v2 is ready for batch dispatch of remaining 15 bounties.

---

## 7. Anchor contributions

| Anchor | Contribution |
|---|---|
| #1 agent first | Makes RAID-2 actually usable for platform agent dispatch (the bottleneck blocking anchor #1 realization) |
| #2 真客户 onboard | Once RAID-2 works, caishen 200 enterprise customers can dispatch AI tasks reliably |
| #3 anti-D-maintenance | Cross-pollinate compass paradigm to V5 RAID-2 instead of inventing new mechanism |
| #5 anti-reinvention | Reuse compass declaration_field + lifecycle + hook patterns (already shipped, proven) |
| #7 anti-overclaim | Pre-registered verification criteria before re-dispatch |

---

## 8. Risks + Open questions

| Risk | Mitigation |
|---|---|
| Fidelity checker becomes its own LLM judge bottleneck | Keep fidelity check rule-based (regex / pattern match) where possible · LLM only for ambiguous cases |
| Context bundle inflation (LongMemEval shows context bloat hurts) | Cap context bundle at 2K tokens · prioritize spec_ref > glossary > anchors |
| V5 dialog scope · this is V5 territory not compass | Cross-dialog handoff · this SPEC is a proposal, V5 dialog implements |
| Backward compat with 858 historical runs | Pure additive · new columns + new role · old runs grandfathered |
| Constraint extractor false positives (regex misses) | Conservative defaults · err on "unclear constraint" = no enforcement |

---

## 9. Cross-dialog handoff

This SPEC is the deliverable from **compass-dialog** to **nautilus-v5-dialog**:

- **Action requested**: V5 team review proposal · decide ship sprint timing
- **Compass-side ready to contribute**: declaration_field paradigm code references · pattern matching from `recall.py promote_lifecycle_tier`
- **Compass-side blocked on**: cannot ship V5 RAID-2 changes (not OSS dialog scope per `docs/PLATFORM_HANDSHAKE.md`)
- **Cross-validation pilot**: once V5 RAID-2 v2 ships, re-dispatch `b-l1-cli-v3` (Python 30 LOC) · compare fidelity vs current 0% baseline

---

## 10. Related ship trail

- audit source · `/home/ubuntu/nautilus-v5/logs/raid_trigger.log` + `raid_executions` + `raid_votes` tables (2026-05-21 22:00 audit)
- compass paradigm reference · commit `d1764e3` (lifecycle), `c68dc6c` (hooks), `2ed77b4` (add_worker + RRF)
- Companion paper · `paper/RAID_DISPATCH_BATCH_PLAN.md` (15 bounty manifest · blocked until V5 RAID-2 v2)
- Boundary doc · `docs/PLATFORM_HANDSHAKE.md` (OSS vs SaaS scope · this SPEC is cross-boundary proposal)
- User strategic anchor · `anchor_user_strategic_compass.md` stance #1 (agent first realization gated by RAID-2 fidelity)
