"""两条 RSI+FDE 闭环回放数据装配 TDD.

build_loop_replays(db=None) 返舰桥 scrollytelling 用的闭环回放:
  - radix_rsi:grounded-retrieval RSI 首个真外部增量(escapes=True)
  - data_001_fde:买方题闭环(过 soul QC)

🔴 融合闭环接真:db 给定时,关键数值从真实表(fde_rsi_deltas / fde_verdicts)
装配(provenance source="db");db None 或行缺时 fail-soft 回退 curated 叙述
(source="curated")。叙述脚手架(phase/label)不变,只让数值变活。
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register mappers
from models.fde_verdict import FdeVerdict
from models.fde_rsi_delta import FdeRsiDelta
from services.control_plane_loops import build_loop_replays


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_loops_replay_shape():
    """无 db(db=None)→ curated 回退 · 形状契约不变(向后兼容)。"""
    loops = build_loop_replays()
    assert isinstance(loops, list)
    assert len(loops) == 2

    for loop in loops:
        assert "loop_id" in loop
        assert "title" in loop and loop["title"]
        assert "steps" in loop and isinstance(loop["steps"], list)
        assert len(loop["steps"]) > 0
        for step in loop["steps"]:
            assert set(step.keys()) >= {"phase", "label", "data"}

    rsi = loops[0]
    assert rsi["loop_id"] == "radix_rsi"
    assert any(s["data"].get("escapes_noise") is True for s in rsi["steps"])

    fde = loops[1]
    assert fde["loop_id"] == "data_001_fde"
    assert any(s["data"].get("overall_pass") is True for s in fde["steps"])


def test_loops_replay_no_db_marks_curated():
    """db None → 两条都标 source=curated(诚实标注数据来源·非伪装真值)。"""
    loops = build_loop_replays(None)
    assert all(loop.get("source") == "curated" for loop in loops)


def test_loops_replay_db_backed_radix(db):
    """db 有真 rsi_delta 行 → radix 回放数值取自该行 · source=db。"""
    db.add(FdeRsiDelta(
        delta_id="t-radix-001", benchmark="autolab_radix_sort", task_uid="radix_sort",
        producer_model="deepseek-chat", n_bare=13, n_grounded=13,
        bare_mean=0.1835, grounded_mean=0.2568, delta_reward=0.0733,
        p_value=0.0215, escapes_noise=True,
    ))
    db.commit()

    loops = build_loop_replays(db)
    radix = next(l for l in loops if l["loop_id"] == "radix_rsi")
    assert radix["source"] == "db"
    # escapes_judgment step 的数值来自 DB 行(delta 0.0733·非 curated 0.0734)。
    judg = next(s for s in radix["steps"] if s["phase"] == "escapes_judgment")
    assert judg["data"]["escapes_noise"] is True
    assert abs(judg["data"]["delta_reward"] - 0.0733) < 1e-9


def test_loops_replay_db_backed_data001(db):
    """db 有真 data_001 verdict 行 → FDE 回放 verdict step 取自该行 · source=db。"""
    db.add(FdeVerdict(
        verdict_id="t-data001-001", task_uid="data_001", source="soul",
        overall_pass=True, veto_failed=False, score=1.0, items=[],
    ))
    db.commit()

    loops = build_loop_replays(db)
    fde = next(l for l in loops if l["loop_id"] == "data_001_fde")
    assert fde["source"] == "db"
    verdict_step = next(s for s in fde["steps"] if s["phase"] == "verdict")
    assert verdict_step["data"]["overall_pass"] is True
    assert verdict_step["data"]["source"] == "soul"


def test_loops_replay_db_missing_rows_falls_back(db):
    """db 给定但相关行缺(空表)→ fail-soft 回退 curated(不崩·标 curated)。"""
    loops = build_loop_replays(db)
    assert len(loops) == 2
    assert all(loop.get("source") == "curated" for loop in loops)
