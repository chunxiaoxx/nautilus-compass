"""
v1.7.1 · S3 module 1 · storage/l1_grouper.py smoke tests · pure logic · NO BGE call

Reuses daemon BGE-m3 in production but tests skip BGE-dependent paths to
keep smoke fast (BGE first-load is ~30s).

Run:
    python tests/test_l1_grouper.py
"""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.l1_grouper import (
    parse_session_frontmatter,
    group_by_thread,
    cluster_by_topic,
    group_sessions,
    THREAD_MIN_SIZE,
    TOPIC_MIN_SIZE,
)


def _write_session(tmp: Path, name: str, thread_id: str = "",
                   description: str = "test") -> Path:
    """Write a fake session_*.md with frontmatter for testing."""
    path = tmp / name
    front = ["---", f"name: {name}", f"description: {description}"]
    if thread_id:
        front.append(f"thread_id: {thread_id}")
    front.extend(["---", "body line"])
    path.write_text("\n".join(front) + "\n", encoding="utf-8")
    return path


def test_1_parse_frontmatter():
    """parse_session_frontmatter extracts thread_id and description."""
    with tempfile.TemporaryDirectory() as t:
        p = _write_session(Path(t), "s.md", thread_id="t-abc", description="hello")
        front = parse_session_frontmatter(p)
        assert front["thread_id"] == "t-abc"
        assert front["description"] == "hello"
    print("OK 1 parse_frontmatter")


def test_2_thread_below_threshold_excluded():
    """2 sessions sharing thread_id stay below min_size=3 default."""
    with tempfile.TemporaryDirectory() as t:
        ps = [_write_session(Path(t), f"s_{i}.md", thread_id="t-A") for i in range(2)]
        groups = group_by_thread(ps)
        assert "t-A" not in groups
    print("OK 2 thread below threshold not grouped")


def test_3_thread_at_threshold_grouped():
    """3 sessions sharing thread_id meet min_size=3 default."""
    with tempfile.TemporaryDirectory() as t:
        ps = [_write_session(Path(t), f"s_{i}.md", thread_id="t-B") for i in range(3)]
        groups = group_by_thread(ps)
        assert "t-B" in groups
        assert len(groups["t-B"]) == 3
    print("OK 3 thread at threshold grouped")


def test_4_thread_less_excluded_from_group_by_thread():
    """Sessions without thread_id are not in group_by_thread output."""
    with tempfile.TemporaryDirectory() as t:
        ps = [_write_session(Path(t), f"s_{i}.md") for i in range(5)]
        groups = group_by_thread(ps)
        assert groups == {}
    print("OK 4 thread-less excluded from group_by_thread")


def test_5_thread_id_whitespace_normalized():
    """thread_id with leading/trailing whitespace gets stripped on parse."""
    with tempfile.TemporaryDirectory() as t:
        p = _write_session(Path(t), "s.md", thread_id="  t-C  ", description="x")
        front = parse_session_frontmatter(p)
        assert front["thread_id"] == "t-C"
    print("OK 5 thread_id whitespace normalized")


def test_6_no_frontmatter_returns_empty():
    """File without --- delimiters returns empty dict."""
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "no_front.md"
        p.write_text("just body · no frontmatter\n", encoding="utf-8")
        assert parse_session_frontmatter(p) == {}
    print("OK 6 no frontmatter")


def test_7_nonexistent_file_returns_empty():
    """Missing file path returns empty dict (graceful)."""
    assert parse_session_frontmatter(Path("/tmp/nonexistent_l1_test.md")) == {}
    print("OK 7 nonexistent file")


def test_8_cluster_empty_input():
    """cluster_by_topic with empty list returns empty dict (no BGE load)."""
    assert cluster_by_topic([], embedder=None) == {}
    print("OK 8 cluster empty input no BGE")


def test_9_multiple_threads_separate_groups():
    """Multiple thread_ids produce separate groups."""
    with tempfile.TemporaryDirectory() as t:
        ps = []
        for i in range(3):
            ps.append(_write_session(Path(t), f"a_{i}.md", thread_id="t-A"))
        for i in range(3):
            ps.append(_write_session(Path(t), f"b_{i}.md", thread_id="t-B"))
        groups = group_by_thread(ps)
        assert set(groups.keys()) == {"t-A", "t-B"}
        assert len(groups["t-A"]) == 3
        assert len(groups["t-B"]) == 3
    print("OK 9 multiple threads separate")


def test_10_constants_match_spec():
    """Constants match paper/SPEC_LAYER2_L1_REWRITE.md section 3.2."""
    assert THREAD_MIN_SIZE == 3, "SPEC says thread min >= 3"
    assert TOPIC_MIN_SIZE == 4, "SPEC says topic min >= 4"
    print("OK 10 constants match SPEC")


if __name__ == "__main__":
    tests = [test_1_parse_frontmatter, test_2_thread_below_threshold_excluded,
             test_3_thread_at_threshold_grouped, test_4_thread_less_excluded_from_group_by_thread,
             test_5_thread_id_whitespace_normalized, test_6_no_frontmatter_returns_empty,
             test_7_nonexistent_file_returns_empty, test_8_cluster_empty_input,
             test_9_multiple_threads_separate_groups, test_10_constants_match_spec]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        print(f"\nFAIL {len(failures)}/{len(tests)} failures")
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} l1_grouper smoke tests pass")
