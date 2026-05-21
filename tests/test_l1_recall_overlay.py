"""S3 module 4 · l1_recall_overlay.py smoke tests."""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.l1_recall_overlay import collapse_to_l1, fuse_l0_l1
from storage.l1_index import save_index


def test_1_empty_index_passthrough():
    with tempfile.TemporaryDirectory() as t:
        entries = [(0.9, {"path": "/x/s_1.md"}), (0.8, {"path": "/x/s_2.md"})]
        out = collapse_to_l1(entries, Path(t))
        # No index → unchanged
        assert len(out) == 2
        assert out[0][1]["path"] == "/x/s_1.md"
    print("OK 1 empty index passthrough")


def test_2_collapse_single_member():
    with tempfile.TemporaryDirectory() as t:
        l1_dir = Path(t)
        save_index(l1_dir, {"s_1.md": "t-A.md"})
        (l1_dir / "t-A.md").write_text("L1 content", encoding="utf-8")
        entries = [(0.9, {"path": "/x/s_1.md"})]
        out = collapse_to_l1(entries, l1_dir)
        assert len(out) == 1
        assert out[0][1].get("tier") == "episodic"
        assert out[0][1].get("collapsed_from") == "s_1.md"
    print("OK 2 collapse single member")


def test_3_collapse_dedup_same_l1():
    """Multiple L0 from same L1 → only 1 surfaces (default max=1)."""
    with tempfile.TemporaryDirectory() as t:
        l1_dir = Path(t)
        save_index(l1_dir, {"s_1.md": "t-A.md", "s_2.md": "t-A.md", "s_3.md": "t-A.md"})
        (l1_dir / "t-A.md").write_text("L1", encoding="utf-8")
        entries = [
            (0.9, {"path": "/x/s_1.md"}),
            (0.8, {"path": "/x/s_2.md"}),
            (0.7, {"path": "/x/s_3.md"}),
        ]
        out = collapse_to_l1(entries, l1_dir)
        assert len(out) == 1
    print("OK 3 dedup same L1")


def test_4_mix_collapsed_and_passthrough():
    with tempfile.TemporaryDirectory() as t:
        l1_dir = Path(t)
        save_index(l1_dir, {"s_1.md": "t-A.md"})
        (l1_dir / "t-A.md").write_text("L1", encoding="utf-8")
        entries = [
            (0.9, {"path": "/x/s_1.md"}),     # collapsed
            (0.8, {"path": "/x/orphan.md"}),  # passthrough
        ]
        out = collapse_to_l1(entries, l1_dir)
        assert len(out) == 2
        # First entry collapsed
        assert "collapsed_from" in out[0][1]
        # Second entry kept as-is
        assert out[1][1]["path"] == "/x/orphan.md"
    print("OK 4 mix collapsed and passthrough")


def test_5_no_path_field_kept():
    """Entries without 'path' field pass through unchanged."""
    with tempfile.TemporaryDirectory() as t:
        l1_dir = Path(t)
        entries = [(0.9, {"name": "no_path_entry"})]
        out = collapse_to_l1(entries, l1_dir)
        assert len(out) == 1
        assert out[0][1].get("name") == "no_path_entry"
    print("OK 5 no path field kept")


def test_6_fuse_fallback_no_recall_module():
    """fuse_l0_l1 falls back to concatenation if recall.py not importable.

    Hard to simulate · just verify it runs without exception with simple inputs.
    """
    l0 = [(0.9, {"path": "/x/a.md"})]
    l1 = [(0.8, {"path": "/x/b.md"})]
    out = fuse_l0_l1(l0, l1, top_k=5)
    assert isinstance(out, list)
    assert len(out) > 0
    print("OK 6 fuse runs (recall or fallback)")


def test_7_max_collapse_per_l1_param():
    """max_collapse_per_l1=2 allows 2 surfacings of same L1."""
    with tempfile.TemporaryDirectory() as t:
        l1_dir = Path(t)
        save_index(l1_dir, {"s_1.md": "t-A.md", "s_2.md": "t-A.md", "s_3.md": "t-A.md"})
        (l1_dir / "t-A.md").write_text("L1", encoding="utf-8")
        entries = [
            (0.9, {"path": "/x/s_1.md"}),
            (0.8, {"path": "/x/s_2.md"}),
            (0.7, {"path": "/x/s_3.md"}),
        ]
        out = collapse_to_l1(entries, l1_dir, max_collapse_per_l1=2)
        assert len(out) == 2
    print("OK 7 max_collapse_per_l1 param")


if __name__ == "__main__":
    tests = [test_1_empty_index_passthrough, test_2_collapse_single_member,
             test_3_collapse_dedup_same_l1, test_4_mix_collapsed_and_passthrough,
             test_5_no_path_field_kept, test_6_fuse_fallback_no_recall_module,
             test_7_max_collapse_per_l1_param]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} l1_recall_overlay smoke pass")
