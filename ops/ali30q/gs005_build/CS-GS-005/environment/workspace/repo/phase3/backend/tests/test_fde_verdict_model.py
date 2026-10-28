"""W1.1 verdict-bus · FdeVerdict model (the 4-way coupling spine, first event type).

The FDE live loop (v5 产物 → soul QC → compass PoI → 用户感知) today writes its
checklist verdicts to a shared file + an invisible DB write. This table persists
them as the platform substrate's first-class event so:
  - compass reads `score`/`overall_pass`/`task_uid` for PoI credit (from_checklist_verdict)
  - soul/activity surfaces them (W2)
  - data_001 / data_002 真 verdict 回放 (W3.2 closure 锚)

Schema locked with the compass PoI consumer (2026-06-05 inbound). Distinct from
engine_cycle_outcomes (internal RSI semantics) — this is the EXTERNAL buyer
verdict, the only fitness signal that escapes the self-referential loop.
"""
from __future__ import annotations
import pytest
from sqlalchemy.exc import IntegrityError
import models.agent_survival  # noqa: F401 · register AgentSurvival mapper (Agent.survival rel)
from models.fde_verdict import FdeVerdict


def _data_001_verdict_kwargs():
    """data_001 真 verdict 形状: 11/11 items, overall_pass, no veto."""
    items = [
        {"id": f"c{i}", "pass": True, "veto": (i in (3, 9, 10, 11)), "reason": ""}
        for i in range(1, 12)
    ]
    return dict(
        verdict_id="data_001-v5-iter1",
        task_uid="data_001",
        source="v5",
        checklist_uid="data_001-checklist",
        overall_pass=True,
        veto_failed=False,
        score=1.0,
        items=items,
        artifacts={"docx": "out.docx", "xlsx": "out.xlsx", "pptx": "out.pptx"},
    )


def test_fde_verdict_roundtrips(db_session):
    """A verdict persists and reads back with all fields intact, including the
    jsonb items list and artifacts dict."""
    v = FdeVerdict(**_data_001_verdict_kwargs())
    db_session.add(v)
    db_session.commit()

    got = db_session.query(FdeVerdict).filter_by(task_uid="data_001").one()
    assert got.verdict_id == "data_001-v5-iter1"
    assert got.source == "v5"
    assert got.overall_pass is True
    assert got.veto_failed is False
    assert got.score == 1.0
    assert isinstance(got.items, list) and len(got.items) == 11
    assert got.items[2]["veto"] is True  # c3
    assert got.artifacts["pptx"] == "out.pptx"
    assert got.created_at is not None  # server/default timestamp set


def test_verdict_id_is_unique_idempotency_key(db_session):
    """verdict_id is the idempotency key — re-ingesting the same verdict must
    not create a duplicate row (DB-level UNIQUE guard)."""
    db_session.add(FdeVerdict(**_data_001_verdict_kwargs()))
    db_session.commit()

    db_session.add(FdeVerdict(**_data_001_verdict_kwargs()))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_failing_verdict_records_veto_and_reason(db_session):
    """A failed verdict (veto_failed True) keeps the per-item reason text that
    feeds the W6 避坑 corpus."""
    items = [
        {"id": "c2", "pass": False, "veto": True,
         "reason": "附件未使用·数据为编造"},
    ]
    v = FdeVerdict(
        verdict_id="data_x-soul-iter2",
        task_uid="data_x",
        source="soul",
        checklist_uid="data_x-checklist",
        overall_pass=False,
        veto_failed=True,
        score=0.0,
        items=items,
        artifacts={},
    )
    db_session.add(v)
    db_session.commit()

    got = db_session.query(FdeVerdict).filter_by(task_uid="data_x").one()
    assert got.veto_failed is True
    assert got.overall_pass is False
    assert got.items[0]["reason"] == "附件未使用·数据为编造"
