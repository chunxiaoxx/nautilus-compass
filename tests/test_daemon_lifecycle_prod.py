#!/usr/bin/env python3
"""Task 1.5 · production lifecycle forget-filter behind COMPASS_PROD_LIFECYCLE.

Activates the dormant LLM-WIKI2 Ebbinghaus forgetting in the recall hot path
(README:104 notes it built-but-not-wired). Pure schema arithmetic (no LLM):
reuses recall.promote_lifecycle_tier()'s Rule C forget check. Default OFF.

  · parse_memory_file surfaces forget_at frontmatter into the entry dict.
  · _apply_lifecycle_filter drops archived (forget_at in the past) entries when
    the flag is on; passthrough when off.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_lifecycle_flag(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_LIFECYCLE_USE", False, raising=False)
    yield


def _write_mem(tmp_path: Path, name: str, forget_at: str | None) -> Path:
    fm = ["---", f"name: {name}", "description: test entry", "type: ingest"]
    if forget_at is not None:
        fm.append(f"forget_at: {forget_at}")
    fm += ["---", "", "body text here"]
    p = tmp_path / f"{name}.md"
    p.write_text("\n".join(fm), encoding="utf-8")
    return p


def test_parse_surfaces_forget_at(tmp_path):
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    p = _write_mem(tmp_path, "m1", future)
    info = zmd.parse_memory_file(p)
    assert info.get("forget_at") == future


def test_parse_no_forget_at_is_empty(tmp_path):
    p = _write_mem(tmp_path, "m2", None)
    info = zmd.parse_memory_file(p)
    assert info.get("forget_at", "") == ""


def test_filter_helper_exists():
    assert hasattr(zmd, "_apply_lifecycle_filter")


def test_flag_off_keeps_archived(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_LIFECYCLE_USE", False, raising=False)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    entries = [{"path": "live.md", "forget_at": ""},
               {"path": "dead.md", "forget_at": past}]
    out = zmd._apply_lifecycle_filter(entries)
    assert {e["path"] for e in out} == {"live.md", "dead.md"}


def test_flag_on_drops_archived(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_LIFECYCLE_USE", True, raising=False)
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    entries = [{"path": "live.md", "forget_at": ""},
               {"path": "future.md", "forget_at": future},
               {"path": "dead.md", "forget_at": past}]
    out = zmd._apply_lifecycle_filter(entries)
    paths = {e["path"] for e in out}
    assert "dead.md" not in paths          # forgotten → dropped
    assert paths == {"live.md", "future.md"}  # not-yet-forgotten kept


def test_flag_on_no_forget_at_all_kept(monkeypatch):
    monkeypatch.setattr(zmd, "_PROD_LIFECYCLE_USE", True, raising=False)
    entries = [{"path": "a.md"}, {"path": "b.md", "forget_at": ""}]
    out = zmd._apply_lifecycle_filter(entries)
    assert {e["path"] for e in out} == {"a.md", "b.md"}


def test_flag_on_malformed_forget_at_kept(monkeypatch):
    # a garbage forget_at must never silently drop a memory
    monkeypatch.setattr(zmd, "_PROD_LIFECYCLE_USE", True, raising=False)
    entries = [{"path": "x.md", "forget_at": "not-a-date"}]
    out = zmd._apply_lifecycle_filter(entries)
    assert [e["path"] for e in out] == ["x.md"]
