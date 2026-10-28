"""Tests for Soul service · generate (dry-run) + ship_to_draft_pr (branch+draft PR).

Engine ship + subprocess are dependency-injected, so no real LLM / git calls.
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services import soul_service


class _FakeResult:
    def __init__(self, passed=True, files=None, applied=False, commit=None, errors=None):
        self.check_result = {"passed": passed, "checks": []}
        self.files_planned = files or [{"path": "services/foo.py", "size": 400, "lang": "python"}]
        self.applied = applied
        self.git_commit = commit
        self.errors = errors


def _fake_engine_factory(base_dir, dry_run):
    return object()


def test_generate_dry_run_returns_shape():
    def fake_ship(engine, task, base_dir, **kw):
        assert kw["apply"] is False  # generate never applies
        return _FakeResult(passed=True)
    out = soul_service.generate("add foo", "/tmp/ws", cycle_id="c1",
                                _ship=fake_ship, _engine_factory=_fake_engine_factory)
    assert out["success"] is True
    assert out["cycle_id"] == "c1"
    assert out["files_planned"][0]["path"] == "services/foo.py"


def test_ship_to_draft_pr_rejects_failed_check():
    def fake_ship(engine, task, base_dir, **kw):
        return _FakeResult(passed=False)
    out = soul_service.ship_to_draft_pr("bad", "/tmp/ws", "soul/x", "msg",
                                        _ship=fake_ship, _engine_factory=_fake_engine_factory)
    assert out["success"] is False
    assert out["stage"] == "check"


def test_ship_to_draft_pr_rejects_blacklist():
    def fake_ship(engine, task, base_dir, **kw):
        return _FakeResult(passed=True, files=[{"path": ".env", "size": 40, "lang": "text"}])
    out = soul_service.ship_to_draft_pr("touch env", "/tmp/ws", "soul/x", "msg",
                                        _ship=fake_ship, _engine_factory=_fake_engine_factory)
    assert out["success"] is False
    assert out["stage"] == "pr_gate"


def test_ship_to_draft_pr_refuses_master():
    def fake_ship(engine, task, base_dir, **kw):
        return _FakeResult(passed=True)
    out = soul_service.ship_to_draft_pr("x", "/tmp/ws", "master", "msg",
                                        _ship=fake_ship, _engine_factory=_fake_engine_factory)
    assert out["success"] is False
    assert out["stage"] == "branch"


def test_ship_to_draft_pr_happy_path_creates_draft():
    calls = []

    def fake_ship(engine, task, base_dir, **kw):
        # dry-run call has apply=False; apply call has apply=True
        if kw.get("apply"):
            return _FakeResult(passed=True, applied=True, commit="abc123")
        return _FakeResult(passed=True)

    def fake_runner(cmd, **kw):
        calls.append(cmd)
        class R:
            returncode = 0
            stdout = "https://github.com/chunxiaoxx/nautilus-core/pull/42\n"
            stderr = ""
        return R()

    out = soul_service.ship_to_draft_pr(
        "add foo", "/tmp/ws", "soul/c1", "soul: add foo", cycle_id="c1",
        _ship=fake_ship, _engine_factory=_fake_engine_factory, _runner=fake_runner,
    )
    assert out["success"] is True
    assert "pull/42" in out["pr_url"]
    assert out["commit"] == "abc123"
    # gh pr create must carry --draft
    assert any("--draft" in c for c in calls if isinstance(c, list))
    # must create a branch (checkout -b), never commit to master directly
    assert any(c[:4] == ["git", "-C", "/tmp/ws", "checkout"] for c in calls if isinstance(c, list))


def test_ship_to_draft_pr_cleans_branch_on_apply_failure():
    """Apply failure must return to master + delete the dangling branch."""
    calls = []

    def fake_ship(engine, task, base_dir, **kw):
        if kw.get("apply"):
            return _FakeResult(passed=True, applied=False, errors=["no parseable file blocks"])
        return _FakeResult(passed=True)  # dry-run passes gate

    def fake_runner(cmd, **kw):
        calls.append(cmd)
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    out = soul_service.ship_to_draft_pr(
        "vague task", "/tmp/ws", "soul/cleanup-test", "soul: vague", cycle_id="c2",
        _ship=fake_ship, _engine_factory=_fake_engine_factory, _runner=fake_runner,
    )
    assert out["success"] is False
    assert out["stage"] == "apply"
    # cleanup: must checkout master + delete the branch
    assert any(c == ["git", "-C", "/tmp/ws", "checkout", "master"] for c in calls if isinstance(c, list))
    assert any(c == ["git", "-C", "/tmp/ws", "branch", "-D", "soul/cleanup-test"] for c in calls if isinstance(c, list))
