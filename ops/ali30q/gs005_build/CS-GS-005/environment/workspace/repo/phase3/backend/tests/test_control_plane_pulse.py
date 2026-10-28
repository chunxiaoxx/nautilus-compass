"""破自循环 Step 2 · soul_alive 按最新 FDE 活动(max(verdict.created_at, fde_rsi_delta.created_at))算。

内循环(auto-mint / bench_eval cycle)继续跑但不再算活——只要有最近外部 FDE 活动（verdict / ΔReward）
就会把 soul_alive 置 True。
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
from models.fde_verdict import FdeVerdict
from models.fde_rsi_delta import FdeRsiDelta
from api.control_plane import _pulse_section


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    s = Session()
    yield s
    s.close()


def _verdict(vid, external_verified=False, external_verified_at=None, score=90.0):
    return FdeVerdict(
        verdict_id=vid, task_uid="task-x", source="producer-x",
        overall_pass=True, veto_failed=False, score=score, items=[],
        artifacts={}, external_verified=external_verified,
        external_verified_at=external_verified_at,
    )


def _rsi_delta(
    delta_id,
    task_uid="task-x",
    created_at=None,
    escapes=False,
    delta_reward=0.0,
):
    return FdeRsiDelta(
        delta_id=delta_id,
        benchmark="autolab_radix_sort",
        task_uid=task_uid,
        n_bare=5,
        n_grounded=5,
        bare_mean=0.2,
        grounded_mean=0.2 + delta_reward,
        delta_reward=delta_reward,
        p_value=0.01 if escapes else 0.2,
        escapes_noise=escapes,
        created_at=created_at,
    )


def test_fresh_verdict_contributes_to_activity_reference(db):
    """内循环产 verdict 仍计入活动窗口（与 external_verified 口径解耦）。"""
    db.add(_verdict("v-fresh-unverified"))
    db.commit()
    pulse = _pulse_section(db)
    assert pulse["soul_alive"] is True
    assert pulse["last_external_verified_at"] is None
    assert pulse["external_verified_total"] == 0


def test_fresh_external_verified_makes_soul_alive(db):
    db.add(_verdict("v-ext", external_verified=True,
                    external_verified_at=datetime.now(timezone.utc)))
    db.commit()
    pulse = _pulse_section(db)
    assert pulse["soul_alive"] is True
    assert pulse["last_external_verified_at"] is not None
    assert pulse["external_verified_total"] == 1
    assert pulse["stale_hours"] is not None and pulse["stale_hours"] < 1


def test_stale_external_verified_not_alive(db):
    db.add(_verdict("v-old", external_verified=True,
                    external_verified_at=datetime.now(timezone.utc) - timedelta(hours=72)))
    db.commit()
    pulse = _pulse_section(db)
    assert pulse["soul_alive"] is False
    assert pulse["external_verified_total"] == 1


def test_last_activity_prefers_latest_delta(db):
    """若最新活动来自 ΔReward，活动时间与 stale 应按 ΔReward 刷新。"""
    now = datetime.now(timezone.utc).replace(microsecond=0)
    db.add(_verdict("v-old", external_verified=True,
                    external_verified_at=now - timedelta(hours=10)))
    db.add(_rsi_delta("d-new", created_at=now - timedelta(hours=1)))
    db.commit()
    pulse = _pulse_section(db)
    assert pulse["last_activity_at"].startswith((now - timedelta(hours=1)).isoformat()[:16])
    assert pulse["soul_alive"] is True
    assert pulse["stale_hours"] is not None and pulse["stale_hours"] < 5
