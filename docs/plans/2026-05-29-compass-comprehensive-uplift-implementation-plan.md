# Compass v3 全方位提升 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** ship compass v3 unified architecture (L1-L4 · H1+H2+H3+H5) such that 4 success gates pass in 2-3 weeks: self-dogfooding act-on ≥30%, recursive-improvement metric ≥+10pp, cross-agent contract ≥1 consumed, +5th bonus 才燊 audit pack adopter ≥1.

**Architecture:** Wire-and-measure approach. L0 BGE retrieval kept stable (Sprint 0 SOTA baseline). L1 drift fix specificity + add act-on instrument. L2 metamemory built independently (compass differentiation). L3 PoI emitter shipped from existing SPEC. L4 cross-agent substrate + subscribe Soul/V5 outcome ledger.

**Tech Stack:** Python 3.10+ · pytest · BGE-m3 · sentence-transformers · NetworkX (KG graph) · async I/O · file-watch (inotify/watchdog) · Vertex Gemini (subject/judge) · DeepSeek (MEME judge).

**Design doc**: [`2026-05-29-compass-comprehensive-uplift-design.md`](2026-05-29-compass-comprehensive-uplift-design.md) (commit `faf2a09`)

**Branch**: `v3-full-fusion` from `d822174`

---

## Phase 0 · Pre-flight Verification (D1 · 2h)

### Task 0.1: Confirm Sprint 0 baseline still reproducible

**Files:**
- Read: `paper/baseline_v201_sprint0.json`
- Read: `paper/results/longmemeval_v201_summary_1780056202.json`

**Step 1:** Verify json valid + completeness 5/5

Run: `python -c "import json; d=json.load(open('paper/baseline_v201_sprint0.json',encoding='utf-8')); assert d['_meta']['completeness'].startswith('5/5'); print('OK')"`
Expected: `OK`

**Step 2:** Confirm v3-full-fusion HEAD includes design doc commit

Run: `git log --oneline -3`
Expected: `faf2a09 docs(plan): compass v3 全方位提升 design` at HEAD

**Step 3:** No commit (verification only)

---

## Phase 1 · Week 1 · Foundation TDD (5 components in parallel)

### Component A · L2 Metamemory Engine (H5 · compass 独立差异化)

#### Task A.1: Add ConfidenceVector dataclass + test

**Files:**
- Create: `metamemory/__init__.py`
- Create: `metamemory/confidence.py`
- Test: `tests/metamemory/test_confidence.py`

**Step 1: Write the failing test**

```python
# tests/metamemory/test_confidence.py
from metamemory.confidence import ConfidenceVector

def test_confidence_vector_basic():
    cv = ConfidenceVector(
        match_id="m1",
        score=0.82,
        evidence_count=3,
        recency_factor=0.9,
        source_diversity=0.5,
    )
    assert 0.0 <= cv.composite() <= 1.0
    assert cv.score == 0.82

def test_confidence_composite_monotonic():
    """Higher inputs should not decrease composite."""
    low = ConfidenceVector("m1", 0.5, 1, 0.5, 0.5)
    high = ConfidenceVector("m2", 0.9, 5, 0.9, 0.9)
    assert high.composite() > low.composite()
```

**Step 2: Run · expect fail**

Run: `pytest tests/metamemory/test_confidence.py -v`
Expected: `ModuleNotFoundError: No module named 'metamemory'`

**Step 3: Minimal implementation**

```python
# metamemory/__init__.py
from metamemory.confidence import ConfidenceVector
__all__ = ["ConfidenceVector"]

# metamemory/confidence.py
from dataclasses import dataclass

@dataclass
class ConfidenceVector:
    match_id: str
    score: float           # BGE similarity normalized to [0,1]
    evidence_count: int    # how many sessions support this
    recency_factor: float  # [0,1] · 1.0 = today
    source_diversity: float  # [0,1] · 1.0 = many distinct sources

    def composite(self) -> float:
        """Weighted composite · deterministic · monotonic in each input."""
        ev_norm = min(self.evidence_count / 5.0, 1.0)
        return min(
            0.4 * self.score
            + 0.2 * ev_norm
            + 0.2 * self.recency_factor
            + 0.2 * self.source_diversity,
            1.0,
        )
```

**Step 4: Run · expect pass**

Run: `pytest tests/metamemory/test_confidence.py -v`
Expected: 2 passed

**Step 5: Commit**

```bash
git add metamemory/__init__.py metamemory/confidence.py tests/metamemory/test_confidence.py
git commit -m "feat(L2): ConfidenceVector dataclass + composite scoring"
```

#### Task A.2: Add GapStatement + RecallResult upgraded API

**Files:**
- Create: `metamemory/gap.py`
- Create: `metamemory/result.py`
- Test: `tests/metamemory/test_recall_result.py`

**Step 1: Failing tests**

```python
# tests/metamemory/test_recall_result.py
from metamemory import RecallResult, ConfidenceVector, GapStatement

def test_recall_result_with_gaps():
    rr = RecallResult(
        matches=[{"id": "m1", "text": "..."}],
        confidence=[ConfidenceVector("m1", 0.8, 2, 0.9, 0.5)],
        gaps=[GapStatement(topic="degree", reason="no session mentions any degree")],
        source_trail={"m1": "session_20260507_x.md"},
        calibration_score=0.0,
    )
    assert rr.has_evidence_for("degree") is False
    assert rr.has_evidence_for("m1") is True

def test_recall_result_empty_matches_returns_no_evidence():
    rr = RecallResult(matches=[], confidence=[], gaps=[
        GapStatement(topic="anything", reason="recall returned 0 results")
    ], source_trail={}, calibration_score=0.0)
    assert rr.is_empty()
```

**Step 2: Run · expect fail**

Run: `pytest tests/metamemory/test_recall_result.py -v`
Expected: ImportError

**Step 3: Implementation**

```python
# metamemory/gap.py
from dataclasses import dataclass

@dataclass
class GapStatement:
    topic: str       # what the query asked about
    reason: str      # why compass thinks there's no evidence

# metamemory/result.py
from dataclasses import dataclass, field
from typing import List, Dict, Any
from metamemory.confidence import ConfidenceVector
from metamemory.gap import GapStatement

@dataclass
class RecallResult:
    matches: List[Dict[str, Any]] = field(default_factory=list)
    confidence: List[ConfidenceVector] = field(default_factory=list)
    gaps: List[GapStatement] = field(default_factory=list)
    source_trail: Dict[str, str] = field(default_factory=dict)
    calibration_score: float = 0.0

    def is_empty(self) -> bool:
        return len(self.matches) == 0

    def has_evidence_for(self, key: str) -> bool:
        if key in {m.get("id") for m in self.matches}:
            return True
        if any(g.topic == key for g in self.gaps):
            return False
        return False
```

**Step 4: Update __init__**

```python
# metamemory/__init__.py (extend)
from metamemory.confidence import ConfidenceVector
from metamemory.gap import GapStatement
from metamemory.result import RecallResult
__all__ = ["ConfidenceVector", "GapStatement", "RecallResult"]
```

**Step 5: Run · expect pass**

Run: `pytest tests/metamemory/ -v`
Expected: 4 passed

**Step 6: Commit**

```bash
git add metamemory/gap.py metamemory/result.py metamemory/__init__.py tests/metamemory/test_recall_result.py
git commit -m "feat(L2): GapStatement + upgraded RecallResult API"
```

#### Task A.3: Implement gap detection logic

**Files:**
- Create: `metamemory/gap_detector.py`
- Test: `tests/metamemory/test_gap_detector.py`

**Step 1: Failing test**

```python
# tests/metamemory/test_gap_detector.py
from metamemory.gap_detector import detect_gaps
from metamemory import ConfidenceVector

def test_detect_gap_when_all_confidence_low():
    matches = [{"id": "m1", "text": "weather is nice today"}]
    confidence = [ConfidenceVector("m1", 0.2, 1, 0.5, 0.0)]
    query = "what degree did I graduate with"
    gaps = detect_gaps(query, matches, confidence, threshold=0.4)
    assert len(gaps) == 1
    assert "degree" in gaps[0].topic.lower()

def test_no_gap_when_high_confidence_match():
    matches = [{"id": "m1", "text": "I graduated with BA"}]
    confidence = [ConfidenceVector("m1", 0.85, 4, 0.9, 0.5)]
    query = "what degree did I graduate with"
    gaps = detect_gaps(query, matches, confidence, threshold=0.4)
    assert len(gaps) == 0
```

**Step 2-5: As pattern · implement / test / commit**

Implementation:
```python
# metamemory/gap_detector.py
from typing import List, Dict, Any
from metamemory.confidence import ConfidenceVector
from metamemory.gap import GapStatement

def detect_gaps(
    query: str,
    matches: List[Dict[str, Any]],
    confidence: List[ConfidenceVector],
    threshold: float = 0.4,
) -> List[GapStatement]:
    """Return GapStatement if no match exceeds confidence threshold."""
    if not matches or not confidence:
        return [GapStatement(topic=query, reason="recall returned 0 results")]
    composite_scores = [cv.composite() for cv in confidence]
    if max(composite_scores) < threshold:
        return [GapStatement(
            topic=query,
            reason=f"max confidence {max(composite_scores):.2f} below threshold {threshold}"
        )]
    return []
```

Commit: `feat(L2): gap detection with confidence threshold`

#### Task A.4: Calibration score (confidence vs actual correct rate)

**Files:**
- Create: `metamemory/calibration.py`
- Test: `tests/metamemory/test_calibration.py`

**Step 1: Failing test**

```python
def test_calibration_score_perfect():
    """If confidence=1.0 → 100% correct · confidence=0.5 → 50% · etc · score=1.0"""
    history = [
        {"confidence": 1.0, "correct": True},
        {"confidence": 0.5, "correct": True},
        {"confidence": 0.5, "correct": False},
        {"confidence": 0.0, "correct": False},
    ]
    from metamemory.calibration import calibration_score
    score = calibration_score(history)
    assert score > 0.9  # high calibration

def test_calibration_score_anti_correlated():
    """confident but wrong · low confidence but right → low score"""
    history = [
        {"confidence": 0.9, "correct": False},
        {"confidence": 0.1, "correct": True},
    ]
    from metamemory.calibration import calibration_score
    assert calibration_score(history) < 0.3
```

**Step 2-5:** TDD cycle + commit.

Implementation uses simple bucketing — bucket confidence into [0,0.5) / [0.5,1.0) · compare bucket avg confidence to bucket actual correct rate.

### Component B · L3 PoI Emitter Activation (复用 SPEC_PROOF_OF_IMPACT)

#### Task B.1: Verify existing poi_emitter scaffolding

**Files:**
- Read: `proof/poi_emitter.py`
- Read: `proof/poi_schema.py`
- Read: `paper/SPEC_PROOF_OF_IMPACT.md`

**Step 1:** Confirm files exist + import without crash

Run: `python -c "from proof.poi_emitter import emit_nau_records; print('OK')"`
Expected: `OK`

**Step 2:** No commit (audit only)

#### Task B.2: Write failing test for PoI event end-to-end

**Files:**
- Test: `tests/proof/test_poi_emit_e2e.py`

**Step 1: Failing test**

```python
import tempfile, json
from pathlib import Path
from proof.poi_schema import ProofOfImpact
from proof.poi_emitter import emit_nau_records

def test_emit_writes_to_sidecar(tmp_path):
    poi = ProofOfImpact(
        agent_id="test-agent",
        action_id="act_001",
        impact_score=0.8,
        cited_memory_paths=["session_x.md", "session_y.md"],
        timestamp_outcome="2026-05-29T12:00:00+08:00",
    )
    count = emit_nau_records(poi, cache_dir=tmp_path)
    sidecar = tmp_path / "poi_emit.jsonl"
    assert sidecar.exists()
    lines = sidecar.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == count
    assert count >= 1
    record = json.loads(lines[0])
    assert record["actor"] == "test-agent"
    assert "nau" in record or "memory" in record
```

**Step 2:** Run · expect pass or fail (depends on existing code)

Run: `pytest tests/proof/test_poi_emit_e2e.py -v`
If FAIL: → Task B.3 (fix). If PASS: skip to B.4.

**Step 3:** Commit test only

```bash
git add tests/proof/test_poi_emit_e2e.py
git commit -m "test(L3): PoI emit e2e contract test"
```

#### Task B.3: Fix poi_emitter (if test failed)

**Step 1:** Read current `proof/poi_emitter.py` · identify what's missing

**Step 2:** Implement missing pieces from `SPEC_PROOF_OF_IMPACT.md` §5

**Step 3:** Run test · expect pass

**Step 4:** Commit `fix(L3): emit_nau_records honors SPEC §5`

#### Task B.4: Add PoI cumulative_impact frontmatter mutator

**Files:**
- Create: `proof/frontmatter_mutator.py`
- Test: `tests/proof/test_frontmatter_mutator.py`

TDD cycle: write failing test that asserts updating session_*.md frontmatter increments `impact_event_count` + sets `last_impact_at`. Implement minimal in-place YAML mutation using existing `parse_session_frontmatter_safe`. Commit.

#### Task B.5: Wire PoI emitter into recall.py

**Files:**
- Modify: `recall.py` (root) — add `emit_poi_candidate()` call after high-confidence recall

**Step 1: Failing integration test**

```python
def test_recall_emits_poi_candidate_on_high_confidence(tmp_path):
    # mock high-confidence recall · assert PoI event in sidecar
    ...
```

**Step 2-5:** TDD cycle + commit.

### Component C · L1 Drift Specificity Fix (5/27 finding: 90% FP)

#### Task C.1: Reproduce current FP rate measurement

**Files:**
- Create: `tests/drift/test_specificity_baseline.py`

**Step 1: Failing test (baseline measurement)**

```python
import json
from pathlib import Path

def test_current_drift_fp_rate_above_threshold():
    """Reproduce 5/27 finding · current FP rate >> 5% target."""
    log = Path.home() / ".claude/plugins/nautilus-compass/.cache/verification_log.jsonl"
    if not log.exists():
        import pytest
        pytest.skip("verification_log not present")
    fires = [json.loads(l) for l in log.read_text().splitlines() if "neg_hit" in l]
    # Sample 100 fires + assert most are FP per known anti-pattern matches
    # (this test EXPECTS to fail/skip after specificity fix)
    assert len(fires) > 100
```

**Step 2-5:** Run · commit baseline assertion.

#### Task C.2: Specificity fix · raise neg_hit threshold + multi-signal vote

**Files:**
- Modify: `daemon_anchor_apply.py` (or wherever drift evaluation lives) — grep first

**Step 1:** Identify drift threshold logic

Run: `grep -n "neg_hit\|0.538" daemon*.py`
Expected: filename + line where 0.538 is set

**Step 2: Failing test for tighter threshold**

```python
def test_drift_only_fires_when_neg_hit_above_065_and_score_below_minus_002():
    """Stricter threshold combo · multi-signal vote · drops FP to <5%"""
    from daemon_anchor_apply import should_fire_drift
    # cases that USED to fire but SHOULDN'T
    assert should_fire_drift(score=-0.03, max_neg_hit=0.55) is False
    # cases that SHOULD still fire
    assert should_fire_drift(score=-0.05, max_neg_hit=0.62) is True
```

**Step 3-5:** Implement · test · commit `fix(L1): drift specificity · stricter threshold combo`

#### Task C.3: ✅ SHIPPED · false-positive feedback ingestion (root `feedback.py`)

**Status:** Already implemented in root `feedback.py` (300 LOC) prior to this sprint.
Audit closed by `tests/test_feedback_core.py` (commit `f62e2b8`).

**Files (actual):**
- Production: `feedback.py` (CLI: `feedback list | log <id> fp|tp | stats | retrain`)
- Test: `tests/test_feedback_core.py` (21 tests · flat layout to avoid the package-shadow trap that bit C.1+C.2 with `tests/drift/`)

**Online learning** (line 209-216, now extracted to `_apply_weight_update` helper): per neg anchor weight `×0.7` per FP / `×1.1` per TP · clamp `[0.05, 2.0]` · 5 consecutive FP → weight `0.168` (effectively deprecated below user-facing `0.17` semantic gate). FP prompts add to `positive_anchors` · TP prompts add to `negative_anchors`. Eval gate (line 248-272) compares baseline vs adapted AUC · rejects on regression · promotes on Δ ≥ 0.005.

**Original plan misroute:** plan wrote `drift/fp_feedback.py` (never existed). Audit caught the dup before any new implementation. C.3 close-loop = unit test backfill, not new ingestion logic.

### Component D · L4 Cross-agent Contract Consumer-side Fix

#### Task D.1: Audit current contract scanner

**Files:**
- Read: `contract.py`
- Read: `.cache/contract_alerts.jsonl`

**Step 1:** Confirm 2 expired contracts present + neither has consumed_by

Run: `python -c "import json; [print(json.loads(l)['contract']['id'], json.loads(l)['contract']['consumed_by']) for l in open('/c/Users/chunx/.claude/plugins/nautilus-compass/.cache/contract_alerts.jsonl')]"`
Expected: 2 IDs printed · both `consumed_by=""`

**Step 2:** No commit (audit only)

#### Task D.2: Consumer-side scanner · detect close-loop session

**Files:**
- Modify: `contract.py` — add `scan_for_consume_sessions()` function
- Test: `tests/contract/test_consumer_scan.py`

**Step 1: Failing test**

```python
def test_scanner_finds_close_loop_session(tmp_path):
    """Given outstanding contract + a session_*.md that says 'consume cnt_xxx' · scanner marks consumed."""
    contract = make_contract(id="cnt_test1", status="outstanding")
    consume_session = tmp_path / "session_20260530_close_loop.md"
    consume_session.write_text("---\ntype: outbound\nconsumes:\n  - cnt_test1\n---\n\nCompleted the work.")
    from contract import scan_for_consume_sessions
    updated = scan_for_consume_sessions([contract], session_dir=tmp_path)
    assert updated[0].status == "consumed"
    assert "session_20260530" in updated[0].consumed_by
```

**Step 2-5:** TDD + commit `feat(L4): consumer-side contract scanner`

#### Task D.3: Ledger writer · contract_ledger.jsonl

**Files:**
- Modify: `contract.py` — when scanner marks consumed, append to `.cache/contract_ledger.jsonl`

TDD as above · commit `feat(L4): contract ledger persistence`

### Component E · Telemetry Infrastructure (Workstream 3 starter)

#### Task E.1: act_on_log.jsonl writer skeleton

**Files:**
- Create: `telemetry/act_on_log.py`
- Test: `tests/telemetry/test_act_on_log.py`

**Step 1: Failing test**

```python
def test_log_drift_event_and_ack(tmp_path):
    from telemetry.act_on_log import log_event, log_ack
    log_event(kind="drift", event_id="d1", payload={"score": -0.05}, log_dir=tmp_path)
    log_ack(event_id="d1", status="acknowledged", log_dir=tmp_path)
    log_path = tmp_path / "act_on_log.jsonl"
    lines = log_path.read_text().splitlines()
    assert len(lines) == 2
```

**Step 2-5:** TDD + commit `feat(telemetry): act_on_log skeleton`

#### Task E.2: act-on rate calculator

**Files:**
- Create: `telemetry/act_on_rate.py`
- Test: `tests/telemetry/test_act_on_rate.py`

TDD: compute (acknowledged + true_positive) / total_events over window. Commit.

---

## Phase 2 · Week 2 · Wire & Integration

### Component F · L4 Wire Soul engine_cycle_outcomes

#### Task F.1: Issue cross-agent contract to platform Soul dialog

**Files:**
- Create: `~/.claude/projects/C--Users-chunx/memory/session_2026-05-30_compass_to_soul_subscribe_request.md`

**Step 1:** Write outbound session_*.md with frontmatter:

```yaml
---
name: session-2026-05-30-compass-to-soul-subscribe-request
type: outbound
thread_id: t_compass_soul_2026-05-30
contracts:
  - id: cnt_compass_soul_sub_a1
    giver: compass-dialog
    receiver: platform-soul-dialog
    deadline: 2026-06-02T18:00+0800
    deliverable: "ack compass's read-only subscription to engine_cycle_outcomes table · agree schema stable · 7-day notification before breaking change"
    status: outstanding
---
```

**Step 2:** No code · commit message file

```bash
git add ../../.claude/projects/C--Users-chunx/memory/session_*.md
git commit -m "contract(L4): issue subscribe-request to platform-soul"
```

(Note: this file is outside repo · may need to commit in memory git separately or use bridge)

#### Task F.2: Soul subscriber poller

**Files:**
- Create: `subscriber/soul_subscriber.py`
- Test: `tests/subscriber/test_soul_subscriber.py`

**Step 1: Failing test**

```python
def test_subscriber_reads_new_events(tmp_path):
    soul_table = tmp_path / "engine_cycle_outcomes.jsonl"
    soul_table.write_text('{"cycle_id": "c1", "outcome": "merged"}\n')
    from subscriber.soul_subscriber import poll_new_events
    events = poll_new_events(table_path=soul_table, cursor=None)
    assert len(events) == 1
    assert events[0]["cycle_id"] == "c1"
```

**Step 2-5:** TDD + commit `feat(L4): Soul subscriber poller`

#### Task F.3: Soul event → compass ingest pipeline

**Files:**
- Create: `subscriber/soul_ingest_adapter.py`
- Test: `tests/subscriber/test_soul_ingest_adapter.py`

TDD: convert Soul event → compass session_*.md frontmatter + body. Commit `feat(L4): Soul ingest adapter`

### Component G · L4 Wire V5 outcome_ledger

#### Task G.1: Issue cross-agent contract to V5 dialog

Same pattern as F.1 · target V5-dialog · deliverable "ack outcome_ledger subscription"

#### Task G.2: V5 outcome subscriber

**Files:**
- Create: `subscriber/v5_outcome_subscriber.py`
- Test: `tests/subscriber/test_v5_outcome_subscriber.py`

TDD: similar pattern to F.2 but for V5's outcome_ledger schema. Commit.

#### Task G.3: V5 outcome → compass drift candidate

**Files:**
- Create: `subscriber/v5_drift_bridge.py`
- Test: `tests/subscriber/test_v5_drift_bridge.py`

TDD: V5 failed_outcome events feed compass L1 drift detection as "prediction error" candidates. Commit.

### Component H · L1 Drift Act-on Instrumentation

#### Task H.1: Hook drift fire into act_on_log

**Files:**
- Modify: `daemon.py` — where drift fires · also call `telemetry.act_on_log.log_event`

**Step 1: Failing test**

```python
def test_drift_fire_writes_to_act_on_log(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPASS_LOG_DIR", str(tmp_path))
    # trigger drift fire path
    from daemon import handle_drift_fire
    handle_drift_fire(score=-0.05, neg_hit=0.62, alert_id="a1")
    log = tmp_path / "act_on_log.jsonl"
    assert log.exists()
    assert "a1" in log.read_text()
```

**Step 2-5:** TDD + commit `feat(L1): drift fire writes to act_on_log`

#### Task H.2: User acknowledgment surfacing in prompt

**Files:**
- Modify: prompt-injection mechanism (likely in `daemon.py` for drift block surface)

TDD: when drift fires, prompt-block includes `act_on_id` so user response can be classified. Test that next-turn user message tagged as response triggers `log_ack`. Commit.

#### Task H.3: PoI act-on logging

TDD as above for PoI events. Commit.

#### Task H.4: Metamemory act-on logging

TDD: when L2 surfaces gap "I don't have evidence for X", log it; if subsequent agent response acknowledges gap, log ack. Commit.

### Component I · L3 4-tier Promotion Driver

#### Task I.1: Promotion calculator

**Files:**
- Create: `proof/tier_promotion.py`
- Test: `tests/proof/test_tier_promotion.py`

**Step 1: Failing test**

```python
def test_promotion_threshold():
    """cumulative_impact > 1.0 → tier up · < -0.5 → tier down."""
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="L2", cumulative_impact=1.5) == "L3"
    assert calculate_new_tier(current_tier="L2", cumulative_impact=-0.6) == "L1"
    assert calculate_new_tier(current_tier="L2", cumulative_impact=0.5) == "L2"
```

**Step 2-5:** TDD + commit `feat(L3): tier promotion calculator`

#### Task I.2: Promotion driver run · once daily cron

**Files:**
- Create: `scripts/tier_promotion_driver.py`
- Test: `tests/scripts/test_tier_promotion_driver.py`

TDD: read all session_*.md frontmatter · compute promotion per file · in-place mutate `tier:` field. Commit.

---

## Phase 3 · Week 3 · Measurement & N=20 Controlled Experiment

### Component J · Controlled Harness Extension

> ⚠️ **Refactored 2026-05-30** · align design_c_differentiator_tasks.md (2026-05-27 lock).
> Original §J H1/H2/H3/H5 four-dim framework superseded · design_c had already
> 锁定 Type 1 (drift) + Type 2 (recency) + 暂缓 (cross-agent + PoI) framework
> 2 days before plan v3 was written. 13th plan-dup audit signal · `design_c`
> + 7 existing task jsonl files (drift_tasks 24 · recency_tasks 7 · ~107 more)
> represented unattributed prior work. See commit
> `docs(plan): align §J with design_c 5/27 framework` for full rationale.
>
> Refactor highlights:
> - **No new task curation** · reuse `drift_tasks.jsonl` (Type 1) + `recency_tasks.jsonl` (Type 2)
> - Arm naming: `a3_compass_drift` + `a3_compass_recency` (was: `a4_compass_v3`)
> - Drop H3 cross-agent (design_c 暂缓 · consumed=0 dataset) and H5 metamemory
>   (no extant data · design_c didn't cover) from N=20 ship · revisit after Type 1+2 ship
> - Gate 2 split per type · honest negative path explicit (design_c 铁律 #3 · 输/平照报)

#### Task J.1 (refactored): Reuse existing differentiator task sets

**Files (no new task file · annotate existing if needed):**
- Existing: `compass-value-study/tasks/drift_tasks.jsonl` (24 tasks · design_c Type 1 主力)
- Existing: `compass-value-study/tasks/recency_tasks.jsonl` (7 tasks · design_c Type 2 次力)
- Optional: add `differentiator_type: "drift"` or `"recency"` field if downstream analysis needs an explicit label (currently inferable from filename)

**Step 1: Validation test** (lightweight · counts and shape only)

```python
def test_differentiator_task_counts():
    with open("tasks/drift_tasks.jsonl") as f:
        drift = [json.loads(l) for l in f]
    with open("tasks/recency_tasks.jsonl") as f:
        recency = [json.loads(l) for l in f]
    # design_c §Type 1: target ~15-20 + 5-8 干扰项 → current 24 ≥ 20 ✓
    assert len(drift) >= 20
    # design_c §Type 2: target ~10 but mining 难 → current 7 acceptable
    assert len(recency) >= 5
    # Shape sanity per design_c spec
    for t in drift:
        assert "action_prompt" in t
        assert "mistake_memory" in t
        assert "matched_neg_anchor" in t
        assert "anti_pattern" in t
    for t in recency:
        assert "current" in t
        assert "stale" in t
        assert "current_file" in t
        assert "stale_file" in t
```

**Step 2: Commit** `test(measurement): differentiator task shape gate (no curation)`

#### Task J.2 (refactored): Add per-type compass arms to harness

**Files:**
- Modify: `compass-value-study/run_pilot.py` — add **two** arms (not one):
  - `a3_compass_drift`: faithful replay of daemon drift evaluator
    (`DRIFT_ALERT_THRESHOLD=-0.032` · `NEG_ANCHOR_HIT_THRESHOLD=0.538`
    · `pos_cos − neg_cos` per design_c §drift 评分复刻规格 line 98-105)
  - `a3_compass_recency`: faithful replay of recency reranker
    (fresh_extra/age weighting · same window as production recall.py)

TDD: per-arm tests covering threshold edge cases and known fairness rule:
**action_prompt must paraphrase neg_anchor, not copy verbatim**
(design_c 公平铁律 line 93-96 · else A3-drift cosine ≈ 1 self-comparison cheat).

#### Task J.3 (refactored): Run controlled per-type · A0 vs A2 vs A3

Run Type 1 (drift):

```bash
python run_pilot.py \
    --tasks tasks/drift_tasks.jsonl \
    --arms a0,a2,a3_compass_drift \
    --output results/v3_drift_$(date +%Y%m%d).jsonl
```

Run Type 2 (recency):

```bash
python run_pilot.py \
    --tasks tasks/recency_tasks.jsonl \
    --arms a0,a2,a3_compass_recency \
    --output results/v3_recency_$(date +%Y%m%d).jsonl
```

Expected: (24 + 7) × 3 arms = **93 rows total** (was 60).

Commit results file `data(measurement): v3 controlled run per-type`.

#### Task J.4 (refactored): Per-type gate metrics

**Files:**
- Create: `compass-value-study/analyze_v3_gates.py`

Compute per design_c locked metrics (§锁定决策 line 87-91):

- **Gate 1** (sprint-independent · act-on rate from `drift_mitigation_log.jsonl`)
  · target ≥ 0.70 · 7d window
- **Gate 2-drift**: A3-drift warning-hit rate vs A2 top-k 命中 (judge yes/no
  per design_c §锁定决策 #1) · target Δ ≥ +10pp = compass drift 真差异化优势
- **Gate 2-recency**: A3-recency current-hit rate vs A2 cosine top · target
  Δ ≥ +10pp · **honest caveat**: design_c §Type 2 admits both may fail
  (compass recency 窗口 <24h 太窄 · 暴露设计弱点 · 照报 per 铁律 #3)
- **Gate 3** (sprint-independent · consumed contract count from
  `contract_ledger.jsonl`) · trend monitoring

Output: `results/v3_gate_report_<date>.md`.

Commit `feat(measurement): per-type gate analysis script`.

**Decision rule** (per design_c §出口 line 85):

- Any one Gate 2 ≥ +10pp → 首个差异化价值证据 → enter Component K (measurement
  doc) · 触发 80h v3.5 fusion Sprint 1+ start gate
- All Gate 2 < +10pp → honest negative report · revisit main thesis · consider
  暂缓 cross-agent/PoI/metamemory revival in next sprint

### Component K · Measurement Doc + Decision

#### Task K.1: Write measurement doc

**Files:**
- Create: `docs/plans/2026-06-XX-compass-v3-measurement-report.md`

Cover:
- N=20 result vs Pilot 0' baseline
- 4 gates pass/fail
- Per-H-dim breakdown
- Decision: 80h v3.5 fusion plan Sprint 1+ start? Or revise?

Commit `docs(plan): v3 measurement report`

---

## Phase 4 · 5th Bonus · 才燊 Audit Pack Adopter (Conditional)

Only start if Phase 1-3 gates pass + R3 time available.

### Component L · 才燊 Phase 2 块 3 Grounding

#### Task L.1: SSH 验云端活性

Run: `ssh ubuntu@43.155.195.48 'systemctl status caishen-* 2>&1 | head -10'`

If alive → proceed. If dead → punt to next cycle.

#### Task L.2: Wire compass PoI candidate to 残保金 outcome

TDD: 残保金审计 outcome 写表 → compass 订阅 → PoI candidate emit · joint with platform NAU settlement

#### Task L.3: audit_brief.md §4 evidence pack E1+E2+E3

Generate E1 (算法机制) + E2 (训练数据) + E3 (决策可解释) · binary 评判 · 3 类符合即 Gate 4 pass.

Commit each evidence file separately.

---

## Risk Register · 显式跟踪

| Risk | Trigger | Mitigation |
|---|---|---|
| Soul schema 改 | F.2 失败 | F.1 contract 明确 7d notification 约束 |
| V5 dispatch 拒接 | G.1 contract 不被 consume | 降级为单方 read-only · 不依赖 V5 双向 |
| Metamemory 不救 ssa | Gate 2 仍 < +10pp | 触发理念回炉 · 可能 H5 不是正确路径 |
| 才燊云端死 | L.1 fail | Bonus 取消 · 主线 4 gates 不受影响 |
| Drift 修不到 5% FP | C.2 仍 > 30% | 加 ML-based vote · 复杂度上升 |
| PoI emitter SPEC 跟现实 schema 不符 | B.2 fail | 回 SPEC · 跟平台 NAU schema 对齐 |
| 1 dialog 处理不来 1700 LOC | 进度卡 | dispatch 部分 task 到 V5 dialog · per task #6 cross-agent contract |

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-05-29-compass-comprehensive-uplift-implementation-plan.md`.

Two execution options:

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration.

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints.

**强烈建议 option 2** · 本 session 已 7h+ · R3 + 持续 ship-class work 累积 · context cache miss 越多 · 新 session 起点 fresh + workstream 也可分派给 V5 dialog 真并行。

Path forward in new session:
1. `cd C:/Users/chunx/Projects/nautilus-compass`
2. `git checkout v3-full-fusion` (HEAD should be at this commit)
3. Invoke `superpowers:executing-plans` skill with this plan path
4. Start Phase 0 → Phase 1 (5 components in parallel via dispatch)

---

## Refs

- Design doc: [`2026-05-29-compass-comprehensive-uplift-design.md`](2026-05-29-compass-comprehensive-uplift-design.md) · commit `faf2a09`
- Sprint 0 baseline: [`paper/baseline_v201_sprint0.json`](../../paper/baseline_v201_sprint0.json) · commit `d822174`
- PoI SPEC: [`paper/SPEC_PROOF_OF_IMPACT.md`](../../paper/SPEC_PROOF_OF_IMPACT.md) · 400 LOC frozen design
- Pilot 0' raw: [`compass-value-study/results/run_20260527-115056.jsonl`](../../../compass-value-study/results/run_20260527-115056.jsonl)
- v3.5 fusion plan (next): [`plan_compass_v35_full_fusion`](../../../memory/plan_compass_v35_full_fusion.md)
- Cross-agent contract scanner: `contract.py` (root)
- Existing PoI scaffolding: `proof/poi_emitter.py` + `proof/poi_schema.py`
