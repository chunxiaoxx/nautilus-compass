from services import soul_self_audit


class FakeDB:
    def __init__(self):
        self.executed = []
    def execute(self, *a, **k):
        self.executed.append((a, k)); return self
    def fetchone(self):
        return None
    def commit(self):
        pass


def test_run_self_audit_happy_path():
    db = FakeDB()
    out = soul_self_audit.run_self_audit(
        db, task_spec="add foo()", output="def foo(): return 1",
        bounty_id="soul-audit-test1",
        _check_fidelity=lambda spec, output: {"fidelity_score": 0.82},
        _persist=lambda db, bid, spec, output, fidelity_score, quality_score: "exec-1",
        _generate_certificate=lambda db, bid: {"@type": "AuditCertificate", "audit_id": bid, "signature": "x"},
        _verify_certificate=lambda cert: {"valid": True},
    )
    assert out["success"] is True
    assert out["fidelity_score"] == 0.82
    assert out["cert_valid"] is True
    assert out["bounty_id"] == "soul-audit-test1"


def test_run_self_audit_cert_error_returns_failure():
    db = FakeDB()
    out = soul_self_audit.run_self_audit(
        db, task_spec="x" * 5, output="y", bounty_id="b2",
        _check_fidelity=lambda s, o: {"fidelity_score": 0.5},
        _persist=lambda *a, **k: "e",
        _generate_certificate=lambda db, bid: {"error": "bounty_not_finalized"},
        _verify_certificate=lambda cert: {"valid": True},
    )
    assert out["success"] is False
    assert out["stage"] == "cert"


def test_attach_cert_to_pr_invokes_gh():
    calls = []
    def fake(cmd, **k):
        calls.append(cmd)
        class R:
            returncode = 0; stdout = ""; stderr = ""
        return R()
    ok = soul_self_audit.attach_cert_to_pr(
        "https://github.com/chunxiaoxx/nautilus-core/pull/9",
        {"audit_id": "a1", "signature": "s"}, "/tmp/r", _runner=fake)
    assert ok is True
    assert any("comment" in str(x) for x in calls[0])


def test_ship_with_self_audit_attaches_cert():
    attached = []
    out = soul_self_audit.ship_with_self_audit(
        task="add foo", base_dir="/tmp/r", branch="soul/x", commit_msg="m", db=object(),
        cycle_id="c1",
        _ship_to_draft_pr=lambda task, bd, br, cm, cycle_id=None: {"success": True, "pr_url": "u1", "commit": "abc", "cycle_id": cycle_id},
        _diff=lambda bd, sha: "def foo(): pass",
        _run_self_audit=lambda db, spec, output, bounty_id: {"cert_valid": True, "fidelity_score": 0.7, "cert": {"audit_id": bounty_id}},
        _attach=lambda pr, cert, bd: attached.append(pr) or True,
    )
    assert out["cert_valid"] is True
    assert out["fidelity_score"] == 0.7
    assert out["cert_attached"] is True
    assert attached == ["u1"]


def test_ship_with_self_audit_skips_audit_when_ship_fails():
    out = soul_self_audit.ship_with_self_audit(
        task="x", base_dir="/tmp/r", branch="soul/x", commit_msg="m", db=object(),
        _ship_to_draft_pr=lambda task, bd, br, cm, cycle_id=None: {"success": False, "stage": "check"},
        _run_self_audit=lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not audit")),
    )
    assert out["success"] is False
    assert "cert" not in out
