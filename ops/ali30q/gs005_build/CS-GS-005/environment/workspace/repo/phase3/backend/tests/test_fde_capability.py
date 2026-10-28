"""FDE verify-side 能力回写单测(2026-06-22)。

接线切片:FDE produce→verify 后,按 claimed_by(producer 字符串身份)把
"格式合规 + 质量分"回写现存表 platform_agent_capability_stats(string-keyed·
V5 读端 earned_capabilities 消费)。

🔴 grounding 纠正(本 session):该表 string-keyed(agent_id varchar128)=能存
"nautilus-prime-001"/"kairos";compass 当初指的 agent_capability_stats 是
integer-agent-keyed(FDE producer 不是 Agent 行·接不上)。V5 指对了表。

核心:capability(格式合规)≠ quality(正确性方差)。succeeded = 能产合规格式
计数(swe-unified-diff 可解析),非 F2P resolved;total_score = 累计质量分。
这能真捕获 V5 用例(kairos 产非 diff → 格式失败 → 合规率降 → 路由 demote)。
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 触发完整模型图注册(Agent.relationship 引用 AgentSurvival 等),否则 query 时
# SQLAlchemy 配置共享 Base registry 会因未导入的 mapper 名失败(单测隔离副作用)。
import models.agent_survival  # noqa: F401

from services.fde_capability import (
    PlatformAgentCapabilityStat,
    classify_format,
    derive_capability,
    record_capability,
    make_capability_fn,
)


def _spec_task(uid, claimed_by, extra):
    import json
    desc = json.dumps({"fde_class": 3, "kind": "code-fix", **extra})
    return {"task_uid": uid, "claimed_by": claimed_by, "description": desc,
            "output": "diff --git a/x b/x"}


# ── classify_format:格式合规三态 ──────────────────────────────────────────

def test_classify_format_ok_true_is_compliant():
    # verifier 跑成(diff 可解析·含 partial/patch-not-applied)→ 格式合规
    assert classify_format({"ok": True, "reward": 0.0, "reason": "patch not applied"}) is True
    assert classify_format({"ok": True, "reward": 1.0, "reason": "resolved"}) is True


def test_classify_format_non_diff_is_format_fail():
    # kairos 产整文件/非 diff → 格式失败(False·算 attempt 但不算 succeeded)
    r = {"ok": False, "reward": 0.0,
         "reason": "missing swe_instance_id or non-diff patch (need unified diff)"}
    assert classify_format(r) is False


def test_classify_format_empty_output_is_format_fail():
    r = {"ok": False, "reward": 0.0, "reason": "produced output has no solution code"}
    assert classify_format(r) is False


def test_classify_format_infra_failure_is_none_no_attribution():
    # harness 超时/无 report = infra 失败·非 producer 责任 → None(不归因)
    assert classify_format({"ok": False, "reason": "swe harness no report (not parsed)"}) is None
    assert classify_format({"ok": False, "reason": "gpu_eval failed: empty"}) is None
    assert classify_format({"ok": False, "reason": "task spec has no verifier_inline"}) is None


# ── derive_capability:从 (task, result) 推归因 ─────────────────────────────

def test_derive_swe_skill_tag():
    task = _spec_task("u1", "kairos", {"swe_instance_id": "psf__requests-2148",
                                       "bench_family": "requests"})
    res = {"ok": True, "reward": 0.6, "reason": "partial 6/10"}
    d = derive_capability(task, res)
    assert d["agent_id"] == "kairos"
    assert d["skill_tag"] == "swe-unified-diff"
    assert d["task_type"] == "requests"
    assert d["format_ok"] is True
    assert d["score"] == pytest.approx(0.6)
    assert d["bounty_id"] == "u1"


def test_derive_kernelbench_skill_tag():
    task = _spec_task("u2", "nautilus-prime-001", {"kb_problem_id": 13, "kb_level": 2})
    res = {"ok": True, "reward": 1.0}
    d = derive_capability(task, res)
    assert d["skill_tag"] == "kernelbench-kernel"
    assert d["task_type"] == "kernelbench"


def test_derive_no_claimed_by_returns_none():
    task = _spec_task("u3", None, {"swe_instance_id": "x"})
    assert derive_capability(task, {"ok": True, "reward": 1.0}) is None


def test_derive_infra_failure_returns_none():
    task = _spec_task("u4", "kairos", {"swe_instance_id": "x"})
    assert derive_capability(task, {"ok": False, "reason": "swe harness no report"}) is None


# ── record_capability:upsert 到现存表(sqlite) ────────────────────────────

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    PlatformAgentCapabilityStat.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def test_record_capability_creates_row(db):
    out = record_capability(db, "kairos", "requests", "swe-unified-diff",
                            format_ok=True, score=0.6, bounty_id="u1")
    assert out["attempts"] == 1
    assert out["succeeded"] == 1
    assert out["total_score"] == pytest.approx(0.6)
    row = db.query(PlatformAgentCapabilityStat).filter_by(
        agent_id="kairos", task_type="requests", skill_tag="swe-unified-diff").one()
    assert row.attempts == 1
    assert row.last_bounty_id == "u1"


def test_record_capability_accumulates_format_fail_lowers_rate(db):
    # 同 producer/skill:一次合规 + 一次格式失败 → attempts=2 succeeded=1(合规率 0.5)
    record_capability(db, "kairos", "swe", "swe-unified-diff", format_ok=True, score=0.6)
    out = record_capability(db, "kairos", "swe", "swe-unified-diff", format_ok=False, score=0.0)
    assert out["attempts"] == 2
    assert out["succeeded"] == 1
    assert out["total_score"] == pytest.approx(0.6)


def test_record_capability_distinct_skill_tags_separate_rows(db):
    record_capability(db, "a", "swe", "swe-unified-diff", format_ok=True, score=1.0)
    record_capability(db, "a", "kernelbench", "kernelbench-kernel", format_ok=True, score=1.0)
    rows = db.query(PlatformAgentCapabilityStat).filter_by(agent_id="a").all()
    assert len(rows) == 2


# ── make_capability_fn:poll_and_verify 注入的 fail-soft 钩子 ──────────────

def test_make_capability_fn_records_via_session_factory(db):
    def factory():
        return db
    cap_fn = make_capability_fn(factory, owns_session=False)
    task = _spec_task("u9", "kairos", {"swe_instance_id": "x", "bench_family": "requests"})
    cap_fn(task, {"ok": False, "reward": 0.0,
                  "reason": "missing swe_instance_id or non-diff patch (need unified diff)"})
    row = db.query(PlatformAgentCapabilityStat).filter_by(agent_id="kairos").one()
    assert row.attempts == 1
    assert row.succeeded == 0  # 格式失败 → 合规率算进去


def test_make_capability_fn_failsoft_swallows_errors():
    # capability 写崩绝不能炸 verify 主链
    def bad_factory():
        raise RuntimeError("db down")
    cap_fn = make_capability_fn(bad_factory)
    # 不抛
    cap_fn({"task_uid": "u", "claimed_by": "kairos", "description": "{}"},
           {"ok": True, "reward": 1.0})


def test_make_capability_fn_skips_infra_failure(db):
    def factory():
        return db
    cap_fn = make_capability_fn(factory, owns_session=False)
    task = _spec_task("u10", "kairos", {"swe_instance_id": "x"})
    cap_fn(task, {"ok": False, "reason": "swe harness no report (not parsed)"})
    assert db.query(PlatformAgentCapabilityStat).count() == 0


# ── make_http_capability_fn:poller 安全 HTTP poster(无 models 依赖) ──────────

def test_http_capability_fn_posts_derived_record(monkeypatch):
    from services import fde_bench_runner as r
    posted = {}

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=15):
        posted["url"] = req.full_url
        posted["body"] = json.loads(req.data.decode())
        return _Resp()

    import json
    monkeypatch.setattr(r.urllib.request, "urlopen", fake_urlopen)
    cap_fn = r.make_http_capability_fn("http://localhost:8000")
    task = _spec_task("u11", "kairos", {"swe_instance_id": "x", "bench_family": "requests"})
    cap_fn(task, {"ok": True, "reward": 0.6})
    assert posted["url"].endswith("/api/platform/fde/capability")
    assert posted["body"]["agent_id"] == "kairos"
    assert posted["body"]["skill_tag"] == "swe-unified-diff"
    assert posted["body"]["format_ok"] is True


def test_http_capability_fn_no_post_on_infra_or_no_claim(monkeypatch):
    from services import fde_bench_runner as r
    calls = []
    monkeypatch.setattr(r.urllib.request, "urlopen",
                        lambda req, timeout=15: calls.append(1))
    cap_fn = r.make_http_capability_fn("http://localhost:8000")
    # infra 失败 → 不 POST
    cap_fn(_spec_task("u12", "kairos", {"swe_instance_id": "x"}),
           {"ok": False, "reason": "swe harness no report"})
    # 无 claimed_by → 不 POST
    cap_fn(_spec_task("u13", None, {"swe_instance_id": "x"}), {"ok": True, "reward": 1.0})
    assert calls == []
