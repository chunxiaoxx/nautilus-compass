"""W1.3 · contract drift guard between the FdeVerdict model and the columns
compass's PoI consumer (from_checklist_verdict) reads.

The compass read path is a SELECT on fde_verdicts for these fields. If the model
ever drops/renames one, compass PoI silently breaks — this test fails first.
The contract is documented in docs/FDE_VERDICT_BUS_CONTRACT.md.
"""
from __future__ import annotations
import models.agent_survival  # noqa: F401 · register mapper
from models.fde_verdict import FdeVerdict

# Columns the compass PoI consumer contractually depends on (2026-06-06 lock ·
# compass ack ruled A: `source` is NOT a compass dependency — its 题级 PoI credit
# keys on task_uid only. The table KEEPS the source column; it's just not part of
# the compass read contract).
COMPASS_POI_FIELDS = {
    "verdict_id",   # idempotency / dedup key
    "task_uid",     # PoI credit attribution
    "overall_pass", # gate
    "veto_failed",  # forced-fail flag
    "score",        # PoI delta (passed/total)
    "items",        # per-item reason (避坑 feed)
    "created_at",   # settle window
}


def test_model_exposes_all_compass_poi_fields():
    cols = set(FdeVerdict.__table__.columns.keys())
    missing = COMPASS_POI_FIELDS - cols
    assert not missing, (
        f"FdeVerdict missing compass PoI contract field(s): {missing}. "
        f"Update docs/FDE_VERDICT_BUS_CONTRACT.md if this is intentional."
    )


def test_verdict_id_is_unique_for_idempotent_reads():
    """compass dedups on verdict_id · the column must carry a UNIQUE constraint."""
    col = FdeVerdict.__table__.columns["verdict_id"]
    assert col.unique is True, "verdict_id must be UNIQUE (idempotency contract)"


def test_to_dict_serializes_poi_fields():
    """The read-back serialization (GET endpoint / compass JSON) must include
    every PoI field."""
    v = FdeVerdict(
        verdict_id="t-1", task_uid="data_001", source="v5",
        overall_pass=True, veto_failed=False, score=1.0, items=[], artifacts={},
    )
    d = v.to_dict()
    assert COMPASS_POI_FIELDS <= set(d.keys())
