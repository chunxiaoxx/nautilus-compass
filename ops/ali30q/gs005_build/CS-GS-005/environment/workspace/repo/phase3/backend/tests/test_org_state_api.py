"""组织状态标准化面(org_state v1 · 2026-10-04)——frames/rulings/verdicts 三端点。

工程化纪律:TDD 先行;数据源=既有件零新表(config/org_frames.json + org_mailbox
+ feishu_decisions + intervention_log.jsonl)。
"""
import asyncio
from unittest.mock import MagicMock

import models.agent_survival  # noqa: F401  # mapper 顺序坑(先注册再导 api.org)
from api.org import org_frames, org_rulings, org_verdicts, _load_frames_registry, _parse_interventions


class _BrokenDB:
    """execute 即抛——测 fail-soft 路径。"""

    def execute(self, *a, **k):
        raise RuntimeError("db down")


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _FakeDB:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, *a, **k):
        return _FakeResult(self._rows)


def test_frames_registry_schema():
    reg = _load_frames_registry()
    assert reg["schema"] == "org_frames.v1"
    assert len(reg["frames"]) >= 9
    for f in reg["frames"]:
        assert f.get("mainline") and f.get("criteria") and f.get("reach") and f.get("cadence"), f


def test_frames_endpoint_fail_soft_and_liveness():
    resp = asyncio.run(org_frames(db=_BrokenDB()))
    assert resp["success"] is True
    assert resp["meta"]["count"] >= 9
    assert all(f["last_letter"] is None for f in resp["data"])  # db 挂=活性缺省不炸
    # 正常路径:活性回填
    resp2 = asyncio.run(org_frames(db=_FakeDB([("v5", __import__("datetime").datetime(2026, 10, 4, 1, 0))])))
    v5 = next(f for f in resp2["data"] if f["frame"] == "v5")
    assert v5["last_letter"] is not None


def test_parse_interventions_shape():
    rows = _parse_interventions(limit=10)
    assert isinstance(rows, list)
    for r in rows:
        assert r["kind"] == "intervention" and r["by"] == "user" and r.get("ts")


def test_rulings_endpoint_merges_and_sorts():
    resp = asyncio.run(org_rulings(limit=30, db=_BrokenDB()))
    assert resp["success"] is True
    ts_list = [r["ts"] for r in resp["data"]]
    assert ts_list == sorted(ts_list, reverse=True)  # 降序
    assert resp["meta"]["hint"]


def test_verdicts_endpoint_maps_rows():
    import datetime as _dt
    db = _FakeDB([(1, "compass", "[writeback:w42] 用例", "writeback:w42:t1", _dt.datetime(2026, 10, 4))])
    resp = asyncio.run(org_verdicts(limit=10, db=db))
    assert resp["success"] is True
    assert resp["data"][0]["trace_id"] == "writeback:w42:t1"
    assert resp["meta"]["count"] == 1
