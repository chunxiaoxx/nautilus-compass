"""S3 module 2 · l1_renderer.py smoke tests · pure logic."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.l1_renderer import (
    _first_sentence,
    render_l1_overview,
    write_l1_file,
    render_all,
)


def _make_session(tmp: Path, name: str, description: str = "",
                  thread_id: str = "", numeric_claims: str = "") -> Path:
    front = ["---", f"name: {name}", f"description: {description}"]
    if thread_id:
        front.append(f"thread_id: {thread_id}")
    if numeric_claims:
        front.append(f"numeric_claims: {numeric_claims}")
    front.extend(["---", "body"])
    p = tmp / name
    p.write_text("\n".join(front) + "\n", encoding="utf-8")
    return p


def test_1_first_sentence_dot():
    assert _first_sentence("Hello. World.") == "Hello"
    print("OK 1 first_sentence dot")


def test_2_first_sentence_chinese():
    assert _first_sentence("你好。世界。") == "你好"
    print("OK 2 first_sentence chinese")


def test_3_first_sentence_truncate():
    long = "x" * 300
    assert len(_first_sentence(long, max_chars=160)) == 160
    print("OK 3 first_sentence truncate")


def test_4_render_overview_basic():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        members = [
            _make_session(tmp, "s_1.md", description="First session about X", thread_id="t-A"),
            _make_session(tmp, "s_2.md", description="Second session about Y", thread_id="t-A"),
            _make_session(tmp, "s_3.md", description="Third session about Z", thread_id="t-A"),
        ]
        content = render_l1_overview("t-A", [str(p) for p in members])
        assert "name: l1-t-A" in content
        assert "tier: episodic" in content
        assert "l1_member_count: 3" in content
        assert "First session about X" in content
        assert "# L1 Overview · t-A" in content
    print("OK 4 render basic")


def test_5_write_l1_file():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        out_dir = tmp / "_l1"
        s = _make_session(tmp, "s.md", description="hi", thread_id="t-B")
        p = write_l1_file(out_dir, "t-B", [str(s)])
        assert p.exists()
        assert "name: l1-t-B" in p.read_text(encoding="utf-8")
    print("OK 5 write_l1_file")


def test_6_safe_filename():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        out_dir = tmp / "_l1"
        s = _make_session(tmp, "s.md", description="hi", thread_id="weird:thread/id")
        p = write_l1_file(out_dir, "weird:thread/id", [str(s)])
        # colons and slashes replaced
        assert ":" not in p.name
        assert "/" not in p.name
    print("OK 6 safe filename escape")


def test_7_render_all_dispatch():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        out_dir = tmp / "_l1"
        groups = {
            "t-X": [str(_make_session(tmp, "tx_1.md", description="thread x 1")),
                    str(_make_session(tmp, "tx_2.md", description="thread x 2"))],
            "topic_000": [str(_make_session(tmp, "tp_1.md", description="topic 1"))],
        }
        written = render_all(groups, out_dir)
        assert "t-X" in written
        assert "topic_000" in written
        # group_type tagged
        tx_content = Path(written["t-X"]).read_text(encoding="utf-8")
        tp_content = Path(written["topic_000"]).read_text(encoding="utf-8")
        assert "l1_group_type: thread" in tx_content
        assert "l1_group_type: topic" in tp_content
    print("OK 7 render_all dispatch")


def test_8_numeric_claims_aggregation():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        members = [
            _make_session(tmp, "n_1.md", description="d1", numeric_claims="users=100"),
            _make_session(tmp, "n_2.md", description="d2", numeric_claims="tokens=5000"),
        ]
        content = render_l1_overview("t-N", [str(p) for p in members])
        assert "Aggregated numeric claims" in content
        assert "users=100" in content
        assert "tokens=5000" in content
    print("OK 8 numeric_claims aggregation")


def test_9_empty_descriptions():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        members = [_make_session(tmp, "e.md", description="")]
        content = render_l1_overview("t-E", [str(members[0])])
        assert "(no description)" in content
    print("OK 9 empty description fallback")


if __name__ == "__main__":
    tests = [test_1_first_sentence_dot, test_2_first_sentence_chinese,
             test_3_first_sentence_truncate, test_4_render_overview_basic,
             test_5_write_l1_file, test_6_safe_filename, test_7_render_all_dispatch,
             test_8_numeric_claims_aggregation, test_9_empty_descriptions]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} l1_renderer smoke pass")
