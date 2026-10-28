"""④ capability LINK 单测(2026-06-22)· 让 5/21 起死的 capability_evolution 表真跑。

compass 7 齿轮实测:④结算+capability_evolution 双断(verdict 无 agent_id·死表)。
正道(V5 实测·LINK 不 register):FDE producer 字符串 claimed_by 别名到**整数注册身份**
(nautilus-prime-001→9000002·kairos→9000003·v7-telegram→9000004),verdict settle 时喂
现成 `capability_evolution.record_task_outcome`(整数键·接 survival/marketplace)。
不 register 新 agent·不动 claim 历史·复用现成能力系统不另造。
"""
from __future__ import annotations

import models.agent_survival  # noqa: F401  触发完整 mapper 图(同 distill 测)
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Agent
from services.fde_capability_link import (
    resolve_agent_id,
    derive_task_type,
    link_capability_from_verdict,
    DEFAULT_AGENT_ALIASES,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Agent.__table__.create(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()


# ── resolve_agent_id:字符串 claimed_by → 整数注册 agent_id ──────────────

def test_resolve_known_alias_no_db_needed():
    assert resolve_agent_id(None, "nautilus-prime-001") == 9000002
    assert resolve_agent_id(None, "kairos") == 9000003
    assert resolve_agent_id(None, "v7-telegram") == 9000004


def test_resolve_falls_back_to_agents_name_lookup(db):
    db.add(Agent(agent_id=7777, owner="0xabc", name="custom-daemon"))
    db.commit()
    assert resolve_agent_id(db, "custom-daemon") == 7777


def test_resolve_unknown_returns_none(db):
    # 未知 producer → None(不臆造·不冤枉记到某 agent)
    assert resolve_agent_id(db, "some-random-dialog") is None
    assert resolve_agent_id(None, "") is None
    assert resolve_agent_id(None, None) is None


def test_default_aliases_are_registered_integer_ids():
    # V5 实测:这三个是真注册整数身份(别 register 新的造碎片)
    assert DEFAULT_AGENT_ALIASES["nautilus-prime-001"] == 9000002


# ── derive_task_type:从 task spec 推能力 task_type ───────────────────────

def test_derive_task_type_swe_uses_bench_family():
    import json
    desc = json.dumps({"fde_class": 3, "swe_instance_id": "psf__requests-2148", "bench_family": "requests"})
    assert derive_task_type({"description": desc}) == "swe:requests"


def test_derive_task_type_fallback_generic():
    assert derive_task_type({"description": "not json"}) == "fde"


# ── link_capability_from_verdict:解析→喂 record_task_outcome ─────────────

def test_link_calls_record_with_integer_id_and_mapped_quality():
    calls = []
    def stub_record(db, agent_id, task_type, success, quality_score):
        calls.append((agent_id, task_type, success, quality_score))
    out = link_capability_from_verdict(
        None, claimed_by="nautilus-prime-001", task_type="swe:requests",
        overall_pass=True, score=0.8, record_fn=stub_record)
    assert out is not None
    assert calls == [(9000002, "swe:requests", True, pytest.approx(4.0))]  # 0.8*5=4.0


def test_link_skips_unknown_producer():
    calls = []
    def stub_record(*a, **k):
        calls.append(a)
    out = link_capability_from_verdict(
        None, claimed_by="random-dialog", task_type="fde",
        overall_pass=True, score=1.0, record_fn=stub_record)
    assert out is None        # 未知 producer → 不记
    assert calls == []


def test_link_failsoft_swallows_record_error():
    def boom(*a, **k):
        raise RuntimeError("db down")
    # 不抛(能力记账绝不炸 verdict 主链)
    out = link_capability_from_verdict(
        None, claimed_by="kairos", task_type="fde",
        overall_pass=False, score=0.0, record_fn=boom)
    assert out is None
