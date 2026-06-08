"""TDD for ops/corpus_sync.py — corpus selection + rsync wrappers (Phase 0 Task 2)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ops"))

import corpus_sync as C  # noqa: E402


def _make_tree(tmp_path):
    (tmp_path / "a.md").write_text("# a", encoding="utf-8")
    (tmp_path / "MEMORY.md").write_text("# index", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.md").write_text("# c", encoding="utf-8")
    # things that must be excluded
    (tmp_path / "transcript.jsonl").write_text("{}", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    pc = tmp_path / "__pycache__"
    pc.mkdir()
    (pc / "x.pyc").write_bytes(b"\x00")
    return tmp_path


def test_select_only_md(tmp_path):
    _make_tree(tmp_path)
    got = sorted(C.select_corpus_files(str(tmp_path)))
    assert got == ["MEMORY.md", "a.md", os.path.join("sub", "c.md")]


def test_select_excludes_jsonl_and_pycache(tmp_path):
    _make_tree(tmp_path)
    got = C.select_corpus_files(str(tmp_path))
    assert not any(p.endswith(".jsonl") for p in got)
    assert not any("__pycache__" in p for p in got)
    assert not any(p.endswith(".txt") for p in got)


def test_select_empty_dir(tmp_path):
    assert C.select_corpus_files(str(tmp_path)) == []


def test_push_corpus_builds_rsync_and_is_idempotent_flagged(tmp_path):
    _make_tree(tmp_path)
    calls = []

    def fake_runner(cmd):
        calls.append(cmd)
        return 0

    rc = C.push_corpus(str(tmp_path), "ubuntu@host", "/remote/corpus", runner=fake_runner)
    assert rc == 0
    assert len(calls) == 1
    cmd = calls[0]
    # archive + only-md include filter + delete for true mirror + checksum/size skip (idempotent)
    assert cmd[0] == "rsync"
    joined = " ".join(cmd)
    assert "--include=*/" in joined and "--include=*.md" in joined and "--exclude=*" in joined
    assert "ubuntu@host:/remote/corpus" in joined


def test_push_corpus_dry_run_uses_n_flag(tmp_path):
    _make_tree(tmp_path)
    calls = []
    C.push_corpus(str(tmp_path), "ubuntu@host", "/remote/corpus",
                  runner=lambda c: calls.append(c) or 0, dry_run=True)
    assert "-n" in calls[0] or "--dry-run" in calls[0]


def test_pull_corpus_reverses_direction(tmp_path):
    calls = []
    C.pull_corpus("ubuntu@host", "/remote/corpus", str(tmp_path),
                  runner=lambda c: calls.append(c) or 0)
    joined = " ".join(calls[0])
    # source is remote, dest is local
    assert "ubuntu@host:/remote/corpus" in joined
    assert str(tmp_path) in joined
