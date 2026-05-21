"""S3 module 3 · l1_index.py smoke tests · pure logic · no BGE."""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.l1_index import (
    load_index, save_index, update_index, lookup_l1_for_session, INDEX_FILENAME,
)


def test_1_load_missing():
    with tempfile.TemporaryDirectory() as t:
        assert load_index(Path(t)) == {}
    print("OK 1 load missing returns empty")


def test_2_save_and_load_roundtrip():
    with tempfile.TemporaryDirectory() as t:
        idx_in = {"s_1.md": "_l1/thread_a.md", "s_2.md": "_l1/thread_a.md"}
        save_index(Path(t), idx_in)
        idx_out = load_index(Path(t))
        assert idx_out == idx_in
    print("OK 2 save+load roundtrip")


def test_3_index_file_exists():
    with tempfile.TemporaryDirectory() as t:
        save_index(Path(t), {"a": "b"})
        assert (Path(t) / INDEX_FILENAME).exists()
    print("OK 3 index filename")


def test_4_corrupt_json_returns_empty():
    with tempfile.TemporaryDirectory() as t:
        (Path(t) / INDEX_FILENAME).write_text("{ bad json", encoding="utf-8")
        assert load_index(Path(t)) == {}
    print("OK 4 corrupt JSON graceful")


def test_5_update_index_from_l1_file():
    with tempfile.TemporaryDirectory() as t:
        l1_dir = Path(t)
        l1_file = l1_dir / "thread_t-A.md"
        l1_file.write_text(
            "---\n"
            "name: l1-t-A\n"
            "l1_members:\n"
            "  - s_1.md\n"
            "  - s_2.md\n"
            "  - s_3.md\n"
            "---\n"
            "# L1 Overview\n",
            encoding="utf-8",
        )
        idx = update_index(l1_dir, {"t-A": l1_file})
        assert "s_1.md" in idx
        assert idx["s_1.md"] == "thread_t-A.md"
        assert idx["s_3.md"] == "thread_t-A.md"
    print("OK 5 update_index parses l1_members")


def test_6_lookup_session():
    with tempfile.TemporaryDirectory() as t:
        save_index(Path(t), {"s_1.md": "_l1/t-A.md"})
        assert lookup_l1_for_session(Path(t), "s_1.md") == "_l1/t-A.md"
        assert lookup_l1_for_session(Path(t), "missing.md") == ""
    print("OK 6 lookup_l1_for_session")


def test_7_atomic_write_no_partial():
    """save_index uses .tmp + replace · no partial file on success."""
    with tempfile.TemporaryDirectory() as t:
        save_index(Path(t), {"k": "v"})
        tmps = list(Path(t).glob("*.tmp"))
        assert len(tmps) == 0
    print("OK 7 atomic write no partial")


def test_8_unicode_safe():
    with tempfile.TemporaryDirectory() as t:
        idx_in = {"中文_session.md": "_l1/中文_thread.md"}
        save_index(Path(t), idx_in)
        idx_out = load_index(Path(t))
        assert idx_out == idx_in
    print("OK 8 unicode safe roundtrip")


if __name__ == "__main__":
    tests = [test_1_load_missing, test_2_save_and_load_roundtrip, test_3_index_file_exists,
             test_4_corrupt_json_returns_empty, test_5_update_index_from_l1_file,
             test_6_lookup_session, test_7_atomic_write_no_partial, test_8_unicode_safe]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} l1_index smoke pass")
