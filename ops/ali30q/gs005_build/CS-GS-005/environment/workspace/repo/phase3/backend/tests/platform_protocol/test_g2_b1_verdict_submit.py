"""Offline tests: verdict submission (fake poster) — no backend, no LLM."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

import g2_b1_executor_agent as ex  # noqa: E402


def _evidence(passed=True):
    return {
        "schema_version": "g2b1-exec-run-v1",
        "executor": ex.EXECUTOR_NAME,
        "task": {"reference_fix_commit": "c7646a57f97a7182225486e7c65841b9a95f915b",
                 "buggy_commit": "5ea2fc32dc088db3e57b1edc0d96f7c5f8a3f172"},
        "test_id": "tests/x.py::t", "source_rel": "tests/x.py",
        "provider": "ark_glm", "test_passed": passed,
        "total_tokens": 30353, "turns": [{"turn": 1}],
    }


def test_submit_verdict_payload():
    posts = []

    def fake_post(url, body):
        posts.append((url, body))
        return type("R", (), {"status_code": 200, "text": "ok"})()

    out = ex.submit_verdict(_evidence(True), backend_base="http://x",
                            poster=fake_post)
    url, body = posts[0]
    assert url == "http://x/api/platform/fde/verdict"
    assert body["verdict_id"] == "g2b1-c7646a57f9-ark_glm"
    assert body["task_uid"] == "g2b1:c7646a57f97a"
    assert body["overall_pass"] is True and body["score"] == 1.0
    assert body["artifacts"]["autonomous"] is True
    assert body["artifacts"]["producer_agent_id"] in (9000010, None)  # cred file
    assert out["status"] == 200


def test_submit_verdict_falls_back_to_default_base(monkeypatch):
    """base 缺失不得静默吞 POST(8/28 复活实测:schtasks 环境无 env → 零 verdict 假 done)。"""
    monkeypatch.delenv("NAUTILUS_BACKEND_BASE", raising=False)
    posts = []

    def fake_post(url, body):
        posts.append(url)
        return type("R", (), {"status_code": 200, "text": "ok"})()

    out = ex.submit_verdict(_evidence(), poster=fake_post)
    assert posts == [f"{ex.DEFAULT_BACKEND_BASE}/api/platform/fde/verdict"]
    assert out["status"] == 200


def test_submit_verdict_skipped_marker_when_no_base_at_all(monkeypatch):
    monkeypatch.delenv("NAUTILUS_BACKEND_BASE", raising=False)
    monkeypatch.setattr(ex, "DEFAULT_BACKEND_BASE", None)
    out = ex.submit_verdict(_evidence(), poster=lambda u, b: None)
    assert out is not None and out["status"] == "SKIPPED_NO_BASE"


def test_anthropic_style_providers_registered():
    """ARK 欠费后提案/燃料臂多元化(用户 8/28 授权:GLM coding plan + minimax m3)。"""
    assert "glm_plan" in ex.PROVIDERS
    assert "minimax_m3" in ex.PROVIDERS
    assert ex.PROVIDERS["minimax_m3"][0] == "https://api.minimaxi.com/anthropic"
    assert ex.PROVIDERS["minimax_m3"][1] == "anthropic/MiniMax-M3"
    assert ex.PROVIDERS["minimax_m3"][2] == "MINIMAX_API_KEY"
    assert ex.ANTHROPIC_PROVIDERS == {"glm_plan", "minimax_m3"}
    assert "ark_glm" not in ex.ANTHROPIC_PROVIDERS


def test_completer_retries_once_on_429(monkeypatch):
    """GLM coding plan RPM 限速(8/28 pilot4 实测崩批)→ 20s 退避重试一次。"""
    calls = {"n": 0}

    class FakeResp:
        # 2026-09-15:补 text 属性——9/5 生产代码加空 body 防护读 response.text,mock 未跟上
        text = '{"choices": []}'
        @property
        def status_code(self):
            return 429 if calls["n"] == 1 else 200
        def json(self):
            return {"choices": [{"message": {"content": "ok"},
                                 "finish_reason": "stop"}]}

    class FakeClient:
        def __init__(self, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def post(self, *a, **kw):
            calls["n"] += 1
            return FakeResp()

    monkeypatch.setattr(ex.httpx, "Client", FakeClient)
    monkeypatch.setattr(ex.time, "sleep", lambda s: None)
    monkeypatch.setenv("ARK_API_KEY", "test-key")
    out = ex.make_completer("ark_glm")("x")
    assert calls["n"] == 2 and out["content"] == "ok"


def test_record_verdict_post_writes_status(tmp_path):
    """POST 结果必须写回 evidence——8/28 实测:POST 瞬时失败零留痕,verdict 永丢。"""
    import json
    ev = _evidence(True)
    p = tmp_path / "g2b1-exec-c7646a57f9-ark_glm.json"
    p.write_text(json.dumps(ev), encoding="utf-8")

    def fake_post(url, body):
        return type("R", (), {"status_code": 200, "text": "ok"})()

    r = ex._record_verdict_post(ev, p, poster=fake_post)
    assert r["status"] == 200
    assert json.loads(p.read_text(encoding="utf-8"))["verdict_post_status"] == 200


def test_replay_backfills_missing_verdict_post(tmp_path):
    """replay 遇无 verdict_post_status 的旧 evidence → 补发(端点幂等)。"""
    import json
    ev = _evidence(True)
    p = tmp_path / "g2b1-exec-c7646a57f9-ark_glm.json"
    p.write_text(json.dumps(ev), encoding="utf-8")
    calls = []

    def fake_post(url, body):
        calls.append(url)
        return type("R", (), {"status_code": 200, "text": "ok"})()

    ex._backfill_replay_verdict(ev, p, poster=fake_post)
    assert len(calls) == 1
    assert json.loads(p.read_text(encoding="utf-8"))["verdict_post_status"] == 200


def test_replay_backfill_skips_when_already_posted(tmp_path):
    import json
    ev = _evidence(True)
    ev["verdict_post_status"] = 200
    p = tmp_path / "g2b1-exec-c7646a57f9-ark_glm.json"
    p.write_text(json.dumps(ev), encoding="utf-8")
    ex._backfill_replay_verdict(ev, p, poster=lambda u, b: (_ for _ in ()).throw(
        AssertionError("must not re-post when verdict_post_status == 200")))


def test_evidence_path_row_uid_vs_legacy():
    """带行 task_uid(变体)用 uid 命名;不带(模板)保持 ref10 老公式。"""
    task = {"reference_fix_commit": "c7646a57f97a7182225486e7c65841b9a95f915b"}
    assert ex._evidence_path_for(task, "ark_glm", Path("/e")).name == \
        "g2b1-exec-c7646a57f9-ark_glm.json"
    task_v = dict(task, task_uid="g2b1:abc123def456")
    assert ex._evidence_path_for(task_v, "ark_glm", Path("/e")).name == \
        "g2b1-exec-abc123def4-ark_glm.json"


def test_submit_verdict_uses_row_uid():
    """变体行自带 task_uid → verdict_id/task_uid 走行 uid(与模板 verdict 不撞幂等键)。"""
    posts = []

    def fake_post(url, body):
        posts.append(body)
        return type("R", (), {"status_code": 200, "text": "ok"})()

    task = {"reference_fix_commit": "c7646a57f97a7182225486e7c65841b9a95f915b",
            "task_uid": "g2b1:abc123def456"}
    ev = _evidence(True)
    ev["task"] = task
    ex.submit_verdict(ev, backend_base="http://x", poster=fake_post)
    assert posts[0]["task_uid"] == "g2b1:abc123def456"
    assert posts[0]["verdict_id"] == "g2b1-abc123def456-ark_glm"
