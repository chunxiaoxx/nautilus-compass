"""Unit tests for scripts/release_notes_extract.py.

Guards against CHANGELOG format drift: the release workflow depends on
this script correctly slicing `## [VERSION] ...` sections. If someone
changes the header style, these tests break before the workflow does.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from release_notes_extract import _find_slice  # noqa: E402


SAMPLE = """# Changelog

## [2.0.0] · 2026-09-01 — "future"

Big stuff.

### Section
- bullet

## [1.0.0-rc1] · 2026-05-07 — "rc1"

Middle stuff.

- item

## [0.9.0] · 2026-01-01

Oldest.
""".splitlines(keepends=True)


def test_top_slice_picks_first_header():
    start, end, version = _find_slice(SAMPLE, None)
    assert version == "2.0.0"
    assert "## [2.0.0]" in SAMPLE[start]
    # must stop at the next header, not run to EOF
    assert "## [1.0.0-rc1]" in SAMPLE[end]


def test_specific_version_middle():
    start, end, version = _find_slice(SAMPLE, "1.0.0-rc1")
    assert version == "1.0.0-rc1"
    body = "".join(SAMPLE[start:end])
    assert "Middle stuff." in body
    assert "Big stuff." not in body
    assert "Oldest." not in body


def test_specific_version_last():
    start, end, version = _find_slice(SAMPLE, "0.9.0")
    assert version == "0.9.0"
    # last section · end should be EOF
    assert end == len(SAMPLE)
    assert "Oldest." in "".join(SAMPLE[start:end])


def test_missing_version_raises():
    with pytest.raises(LookupError):
        _find_slice(SAMPLE, "99.99.99")


def test_real_changelog_has_rc1():
    """Smoke against the actual CHANGELOG.md · catches header-style regressions."""
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines(keepends=True)
    start, end, version = _find_slice(changelog, "1.0.0-rc1")
    assert version == "1.0.0-rc1"
    assert end > start + 10, "rc1 slice suspiciously short"
    body = "".join(changelog[start:end])
    # spot-check markers that should be inside the rc1 section
    assert "integrity chain" in body.lower() or "merkle" in body.lower()
