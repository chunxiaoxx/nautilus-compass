"""v1.0 · Merkle chain integrity tests.

Exercises the public contract of merkle_chain (update_chain + verify_chain)
end-to-end against a temporary memory directory. No daemon / no GPU / no
external deps — runs under pytest in < 1 second.

Scenarios covered:
  1. empty dir → empty chain · verify returns valid=True
  2. init + verify clean (no tampering)
  3. edit a file → verify flags it in tampered_files
  4. delete a file → verify flags it in missing_files
  5. add a new file without re-baselining → verify still valid for old set
  6. re-baseline after accepting new files → verify clean again
  7. corrupted .chain.json → verify surfaces it as invalid, does not crash
  8. deterministic head: same input bytes + order → same head across runs
  9. chain ordering: files sorted by filename, not by mtime
 10. tamper detection survives mtime-only changes (content === hash)

Run:  pytest tests/test_merkle_chain.py -q
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Make plugin root importable
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

import merkle_chain as mc  # noqa: E402


# ─── helpers ───────────────────────────────────────────────────────

def _write_session(memdir: Path, slug: str, body: str = "hello world") -> Path:
    """Create a session_<ts>_<slug>.md with deterministic name."""
    p = memdir / f"session_2026-01-01T00-00-00Z_{slug}.md"
    p.write_text(body, encoding="utf-8")
    return p


# ─── 1. empty dir ──────────────────────────────────────────────────

def test_empty_dir_is_valid_empty_chain(tmp_path):
    result = mc.update_chain(tmp_path)
    assert result["count"] == 0
    assert result["head"] == ""
    assert result["algorithm"] == "sha256"

    v = mc.verify_chain(tmp_path)
    assert v["valid"] is True
    assert v["expected_head"] == ""
    assert v["actual_head"] == ""
    assert v["tampered_files"] == []
    assert v["missing_files"] == []


# ─── 2. init + verify clean ────────────────────────────────────────

def test_init_then_verify_clean(tmp_path):
    _write_session(tmp_path, "a", "content A")
    _write_session(tmp_path, "b", "content B")
    _write_session(tmp_path, "c", "content C")

    summary = mc.update_chain(tmp_path)
    assert summary["count"] == 3
    assert summary["head"]  # non-empty head

    v = mc.verify_chain(tmp_path)
    assert v["valid"] is True, f"unexpected invalid: {v}"
    assert v["tampered_files"] == []
    assert v["missing_files"] == []
    assert v["expected_head"] == v["actual_head"]


# ─── 3. edit detects tampering ─────────────────────────────────────

def test_edit_flags_tampered(tmp_path):
    f = _write_session(tmp_path, "t", "original")
    mc.update_chain(tmp_path)

    f.write_text("TAMPERED", encoding="utf-8")

    v = mc.verify_chain(tmp_path)
    assert v["valid"] is False
    assert f.name in v["tampered_files"]
    assert v["missing_files"] == []
    assert v["expected_head"] != v["actual_head"]


# ─── 4. delete detects missing ─────────────────────────────────────

def test_delete_flags_missing(tmp_path):
    a = _write_session(tmp_path, "a", "aaa")
    _write_session(tmp_path, "b", "bbb")
    mc.update_chain(tmp_path)

    a.unlink()

    v = mc.verify_chain(tmp_path)
    assert v["valid"] is False
    assert a.name in v["missing_files"]
    assert v["tampered_files"] == []


# ─── 5. new file without re-baseline ──────────────────────────────

def test_new_file_not_flagged_before_rebaseline(tmp_path):
    """verify_chain focuses on known-should-still-match. New files are
    only adopted by update_chain · this keeps verify semantically clean."""
    _write_session(tmp_path, "a", "aaa")
    mc.update_chain(tmp_path)

    # Add a new file WITHOUT re-running update_chain.
    _write_session(tmp_path, "z_new", "brand new content")

    v = mc.verify_chain(tmp_path)
    # The old chain is still intact; new file is simply not in the chain.
    assert v["tampered_files"] == []
    assert v["missing_files"] == []
    # valid depends on whether the chain head still matches the old subset —
    # since all chained files are intact, it should be True.
    assert v["valid"] is True, f"unexpected: {v}"


# ─── 6. re-baseline accepts the new set ──────────────────────────

def test_rebaseline_after_additions(tmp_path):
    _write_session(tmp_path, "a", "aaa")
    first = mc.update_chain(tmp_path)

    _write_session(tmp_path, "b", "bbb")
    _write_session(tmp_path, "c", "ccc")
    second = mc.update_chain(tmp_path)

    assert second["count"] == 3
    assert second["head"] != first["head"]

    v = mc.verify_chain(tmp_path)
    assert v["valid"] is True
    assert v["tampered_files"] == []
    assert v["missing_files"] == []


# ─── 7. corrupted .chain.json ──────────────────────────────────────

def test_corrupt_chain_file_does_not_crash(tmp_path):
    _write_session(tmp_path, "a", "aaa")
    mc.update_chain(tmp_path)

    # Corrupt the sidecar.
    (tmp_path / mc.CHAIN_FILENAME).write_text("{not json", encoding="utf-8")

    # verify_chain should not raise; treat as if no chain.
    v = mc.verify_chain(tmp_path)
    # With no usable chain, the function reports expected_head="" while the
    # disk files still hash to a non-empty actual_head → valid=False.
    assert v["expected_head"] == ""
    assert v["actual_head"]  # non-empty: there's a session file on disk
    assert v["valid"] is False


# ─── 8. determinism ───────────────────────────────────────────────

def test_head_is_deterministic(tmp_path):
    _write_session(tmp_path, "a", "same content")
    _write_session(tmp_path, "b", "other content")

    h1 = mc.update_chain(tmp_path)["head"]

    # Rerun with no changes.
    h2 = mc.update_chain(tmp_path)["head"]

    assert h1 == h2 and h1  # stable + non-empty


def test_head_depends_on_content_not_filename_order(tmp_path_factory):
    """Two dirs with same {filename → bytes} map must produce same head,
    regardless of creation order or filesystem mtime."""
    d1 = tmp_path_factory.mktemp("d1")
    d2 = tmp_path_factory.mktemp("d2")

    # d1: a first, then b
    _write_session(d1, "a", "content A")
    time.sleep(0.01)  # ensure different mtime
    _write_session(d1, "b", "content B")

    # d2: b first, then a (reverse mtime order)
    _write_session(d2, "b", "content B")
    time.sleep(0.01)
    _write_session(d2, "a", "content A")

    h1 = mc.update_chain(d1)["head"]
    h2 = mc.update_chain(d2)["head"]

    assert h1 == h2, "chain must sort by filename, not mtime"


def test_different_bytes_produce_different_head(tmp_path_factory):
    d1 = tmp_path_factory.mktemp("a")
    d2 = tmp_path_factory.mktemp("b")
    _write_session(d1, "x", "version 1")
    _write_session(d2, "x", "version 2")

    h1 = mc.update_chain(d1)["head"]
    h2 = mc.update_chain(d2)["head"]
    assert h1 != h2


# ─── 9. mtime-only touch is not tampering ────────────────────────

def test_mtime_only_touch_is_not_tampering(tmp_path):
    f = _write_session(tmp_path, "a", "body")
    mc.update_chain(tmp_path)

    # Touch: update mtime but keep bytes identical.
    st = f.stat()
    import os
    os.utime(f, (st.st_atime + 1000, st.st_mtime + 1000))

    v = mc.verify_chain(tmp_path)
    assert v["valid"] is True, f"mtime touch wrongly flagged: {v}"
    assert v["tampered_files"] == []


# ─── 10. chain.json shape contract ────────────────────────────────

def test_chain_json_shape(tmp_path):
    _write_session(tmp_path, "a", "aaa")
    _write_session(tmp_path, "b", "bbb")
    mc.update_chain(tmp_path)

    payload = json.loads((tmp_path / mc.CHAIN_FILENAME).read_text(encoding="utf-8"))
    assert payload["version"] == mc.SCHEMA_VERSION
    assert payload["algorithm"] == "sha256"
    assert payload["head"]
    assert len(payload["entries"]) == 2
    for e in payload["entries"]:
        assert set(e.keys()) >= {"file", "file_hash", "chain_hash"}
    assert "updated_at" in payload
    # ISO-8601 Z
    assert payload["updated_at"].endswith("Z")
