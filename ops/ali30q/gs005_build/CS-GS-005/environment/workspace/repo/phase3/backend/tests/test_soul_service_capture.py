"""Task 1.1b · soul_service.generate(capture_content=True) returns real file content."""
from services import soul_service


class _FakeResult:
    applied = True
    files_planned = [{"path": "scratch/x.py", "size": 17, "lang": "python"}]
    check_result = {"passed": True}
    errors = None
    git_commit = None


def test_generate_capture_content(tmp_path):
    def fake_ship(engine, task, base_dir, **k):
        import os
        os.makedirs(os.path.join(base_dir, "scratch"), exist_ok=True)
        with open(os.path.join(base_dir, "scratch", "x.py"), "w") as fh:
            fh.write("def x(): return 1")
        return _FakeResult()

    out = soul_service.generate(
        "add x", base_dir=str(tmp_path), cycle_id="c1",
        capture_content=True, _ship=fake_ship, _engine_factory=lambda b, d: object(),
    )
    assert out["success"] is True
    assert out["files_planned"][0]["content"] == "def x(): return 1"


def test_generate_capture_blocks_path_escape(tmp_path):
    """Escaping paths in files_planned must NOT read files outside the temp dir."""
    class _R:
        applied = True
        files_planned = [
            {"path": "/etc/hostname", "size": 5, "lang": "text"},             # absolute escape
            {"path": "../../../../etc/hostname", "size": 5, "lang": "text"},  # traversal escape
        ]
        check_result = {"passed": True}
        errors = None
        git_commit = None

    def fake_ship(engine, task, base_dir, **k):
        return _R()

    out = soul_service.generate(
        "x", base_dir=str(tmp_path), capture_content=True,
        _ship=fake_ship, _engine_factory=lambda b, d: object(),
    )
    for f in out["files_planned"]:
        assert f["content"] == "", f"escaping path {f['path']} must be blocked"


def test_generate_default_no_content_field(tmp_path):
    """capture_content=False (default) keeps the lean dry-run shape (no content key)."""
    def fake_ship(engine, task, base_dir, **k):
        return _FakeResult()

    out = soul_service.generate(
        "add x", base_dir=str(tmp_path), cycle_id="c1",
        _ship=fake_ship, _engine_factory=lambda b, d: object(),
    )
    assert out["success"] is True
    assert "content" not in out["files_planned"][0]
