"""access→tier wire · TDD RED first.

Closes the LLM-WIKI2 gap flagged in
session_20260623_compass_phase1_merge_done_t4_deploy_topology_grounded:
reinforce_count accumulates (access events) but never drove tier promotion.

The driver now runs TWO companion axes per file:
  · impact axis (existing) · cumulative_impact delta → calculate_new_tier
  · access axis (this wire) · reinforce_count → recall.promote_lifecycle_tier
Impact takes priority; access fires only when impact leaves the tier unchanged.
Access promotes only (never demotes) · rising thresholds (1/5/20_access) make
the absolute-count check naturally idempotent (no baseline stamp needed).
"""
from __future__ import annotations

from pathlib import Path


def _make_md(path: Path, tier=None, cumulative_impact=None,
             reinforce_count=None, promote_after=None) -> None:
    lines = ["---", f"name: {path.stem}", "description: test"]
    if tier is not None:
        lines.append(f"tier: {tier}")
    if cumulative_impact is not None:
        lines.append(f"cumulative_impact: {cumulative_impact}")
    if reinforce_count is not None:
        lines.append(f"reinforce_count: {reinforce_count}")
    if promote_after is not None:
        lines.append(f"promote_after: {promote_after}")
    lines += ["---", "", "# body\n"]
    path.write_text("\n".join(lines), encoding="utf-8")


def _tier(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("tier:"):
            return line.split(":", 1)[1].strip()
    return None


def test_working_with_one_access_promotes_to_episodic(tmp_path):
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"; mem.mkdir()
    f = mem / "session_a.md"
    _make_md(f, tier="working", reinforce_count=1)  # threshold working=1_access
    s = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _tier(f) == "episodic"
    assert s["promoted"] == 1


def test_working_zero_access_no_change(tmp_path):
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"; mem.mkdir()
    f = mem / "session_b.md"
    _make_md(f, tier="working", reinforce_count=0, cumulative_impact=0.2)
    s = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _tier(f) == "working"
    assert s["mutations"] == 0


def test_episodic_needs_five_access(tmp_path):
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"; mem.mkdir()
    lo = mem / "session_lo.md"; hi = mem / "session_hi.md"
    _make_md(lo, tier="episodic", reinforce_count=3)   # < 5 → stay
    _make_md(hi, tier="episodic", reinforce_count=5)   # >= 5 → semantic
    run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _tier(lo) == "episodic"
    assert _tier(hi) == "semantic"


def test_impact_priority_then_access_fallback(tmp_path):
    """impact in-band (0.3) leaves tier · access (count=1) then promotes."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"; mem.mkdir()
    f = mem / "session_c.md"
    _make_md(f, tier="working", cumulative_impact=0.3, reinforce_count=1)
    s = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _tier(f) == "episodic"
    assert s["promoted"] == 1


def test_access_idempotent_second_run(tmp_path):
    """working(count=1)→episodic · 2nd run: episodic needs 5, count=1 → no move."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"; mem.mkdir()
    f = mem / "session_d.md"
    _make_md(f, tier="working", reinforce_count=1)
    s1 = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    s2 = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert s1["mutations"] == 1
    assert s2["mutations"] == 0
    assert _tier(f) == "episodic"


def test_access_mutation_log_records_axis(tmp_path):
    import json
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"; mem.mkdir()
    _make_md(mem / "session_e.md", tier="working", reinforce_count=1)
    log = tmp_path / "log.jsonl"
    run_driver(memory_dirs=[mem], log_path=log)
    rec = json.loads(log.read_text(encoding="utf-8").strip().splitlines()[0])
    assert rec["axis"] == "access"
    assert rec["old_tier"] == "working"
    assert rec["new_tier"] == "episodic"
