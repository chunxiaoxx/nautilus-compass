"""Phase 2.I.2 · tier promotion driver tests · TDD RED first.

Driver reads all session_*.md frontmatter across project memory dirs ·
computes new tier from cumulative_impact via proof.tier_promotion ·
mutates `tier:` field in-place if changed · logs each mutation.
"""
from __future__ import annotations

from pathlib import Path

import pytest


# --- Helpers ---

def _make_session_md(path: Path, tier: str | None,
                     cumulative_impact: float | None,
                     body: str = "# body\n") -> None:
    """Write a session_*.md with optional tier / cumulative_impact frontmatter."""
    lines = ["---", f"name: {path.stem}", "description: test session"]
    if tier is not None:
        lines.append(f"tier: {tier}")
    if cumulative_impact is not None:
        lines.append(f"cumulative_impact: {cumulative_impact}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    path.write_text("\n".join(lines), encoding="utf-8")


def _read_tier_from_md(path: Path) -> str | None:
    """Extract `tier:` value from frontmatter for verification."""
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("tier:"):
            return line.split(":", 1)[1].strip()
    return None


# --- Promotion outcomes ---

def test_episodic_with_high_impact_promotes_to_semantic(tmp_path: Path):
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_test1.md"
    _make_session_md(f, tier="episodic", cumulative_impact=1.5)
    log = tmp_path / "promotion_log.jsonl"
    summary = run_driver(memory_dirs=[mem], log_path=log)
    assert _read_tier_from_md(f) == "semantic"
    assert summary["promoted"] == 1
    assert summary["demoted"] == 0
    assert summary["mutations"] == 1


def test_semantic_with_low_impact_demotes_to_episodic(tmp_path: Path):
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_test2.md"
    _make_session_md(f, tier="semantic", cumulative_impact=-0.8)
    summary = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _read_tier_from_md(f) == "episodic"
    assert summary["demoted"] == 1
    assert summary["promoted"] == 0


def test_in_band_no_mutation(tmp_path: Path):
    """impact within [-0.5, 1.0] · tier unchanged · no mutation logged."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_test3.md"
    _make_session_md(f, tier="working", cumulative_impact=0.3)
    summary = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _read_tier_from_md(f) == "working"
    assert summary["mutations"] == 0


# --- Defaults / fallbacks ---

def test_missing_tier_defaults_to_episodic_then_promotes(tmp_path: Path):
    """No tier field · high impact · adds tier=semantic (was implicit episodic)."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_test4.md"
    _make_session_md(f, tier=None, cumulative_impact=1.5)
    summary = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _read_tier_from_md(f) == "semantic"
    assert summary["mutations"] == 1


def test_missing_cumulative_impact_defaults_to_zero_no_change(tmp_path: Path):
    """No cumulative_impact field · 0.0 default · in-band · no mutation."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_test5.md"
    _make_session_md(f, tier="episodic", cumulative_impact=None)
    summary = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert _read_tier_from_md(f) == "episodic"
    assert summary["mutations"] == 0


def test_invalid_tier_in_frontmatter_falls_back(tmp_path: Path):
    """Frontmatter has tier=L2 (plan misnomer) · driver treats as episodic
    default + promotes given high impact · doesn't crash."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_test6.md"
    _make_session_md(f, tier="L2", cumulative_impact=1.5)
    summary = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    # episodic + 1.5 → semantic (the L2 in frontmatter was ignored as junk)
    assert _read_tier_from_md(f) == "semantic"
    assert summary["mutations"] == 1


# --- No-op cases ---

def test_no_frontmatter_skipped(tmp_path: Path):
    """File without --- frontmatter is skipped (not crashed)."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_test7.md"
    f.write_text("plain text · no frontmatter\n", encoding="utf-8")
    summary = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert summary["files_scanned"] == 1
    assert summary["mutations"] == 0


def test_non_session_files_ignored(tmp_path: Path):
    """Driver only globs session_*.md · other files left alone."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    # session file · should be processed
    _make_session_md(mem / "session_test8.md", tier="episodic", cumulative_impact=1.5)
    # non-session file · should be ignored even if it matches frontmatter shape
    _make_session_md(mem / "anchor_compass.md", tier="working", cumulative_impact=2.0)
    summary = run_driver(memory_dirs=[mem], log_path=tmp_path / "log.jsonl")
    assert summary["files_scanned"] == 1  # only session_test8.md
    assert _read_tier_from_md(mem / "session_test8.md") == "semantic"
    assert _read_tier_from_md(mem / "anchor_compass.md") == "working"  # unchanged


# --- Idempotency / log ---

def test_log_file_has_one_line_per_mutation(tmp_path: Path):
    import json
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    _make_session_md(mem / "session_a.md", tier="episodic", cumulative_impact=1.5)
    _make_session_md(mem / "session_b.md", tier="semantic", cumulative_impact=-1.0)
    log = tmp_path / "tier_promotion_log.jsonl"
    run_driver(memory_dirs=[mem], log_path=log)
    lines = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    records = [json.loads(ln) for ln in lines]
    # Required fields per record
    for r in records:
        assert "ts" in r
        assert "file" in r
        assert "old_tier" in r
        assert "new_tier" in r
        assert "cumulative_impact" in r


def test_idempotent_second_run_no_new_mutation(tmp_path: Path):
    """After first promotion · second run sees correct tier · no further mutation."""
    from scripts.tier_promotion_driver import run_driver
    mem = tmp_path / "mem"
    mem.mkdir()
    f = mem / "session_idem.md"
    _make_session_md(f, tier="episodic", cumulative_impact=1.5)
    log = tmp_path / "log.jsonl"
    s1 = run_driver(memory_dirs=[mem], log_path=log)
    s2 = run_driver(memory_dirs=[mem], log_path=log)
    assert s1["mutations"] == 1
    assert s2["mutations"] == 0
    assert _read_tier_from_md(f) == "semantic"


def test_multiple_memory_dirs_combined(tmp_path: Path):
    """Driver processes session files across multiple memory dirs."""
    from scripts.tier_promotion_driver import run_driver
    mem1 = tmp_path / "proj1" / "memory"
    mem2 = tmp_path / "proj2" / "memory"
    mem1.mkdir(parents=True)
    mem2.mkdir(parents=True)
    _make_session_md(mem1 / "session_p1.md", tier="episodic", cumulative_impact=1.5)
    _make_session_md(mem2 / "session_p2.md", tier="semantic", cumulative_impact=-1.0)
    summary = run_driver(memory_dirs=[mem1, mem2], log_path=tmp_path / "log.jsonl")
    assert summary["files_scanned"] == 2
    assert summary["promoted"] == 1
    assert summary["demoted"] == 1
