"""org_state 扩展:sinks 端点(2026-10-04 · 沉淀物注册表,compass #2797 提前开工件)。

通用单端点替代三专属端点(契约类平台裁):各框体系级正本指针卡——
sink_id/frame/title/repo/path/sha16/status(planned|live)/consumers/criteria_ref。
沿 _sediment_endpoint 工厂零新表同款:registry JSON,缺失=fail-soft 空列表。
"""
import asyncio

import models.agent_survival  # noqa: F401
from api.org import org_sinks


def test_sinks_reads_registry(monkeypatch):
    import api.org as m
    monkeypatch.setattr(m, "_load_json_registry", lambda name: {
        "sinks": [{"sink_id": "compass-memory-io", "frame": "compass", "status": "planned"}]})
    resp = asyncio.run(org_sinks())
    assert resp["success"] is True
    assert resp["data"][0]["sink_id"] == "compass-memory-io"
    assert resp["meta"]["count"] == 1
    assert resp["meta"]["schema"] == "sinks.v1"


def test_sinks_missing_file_fail_soft(monkeypatch):
    import api.org as m
    def _boom(name):
        raise FileNotFoundError(name)
    monkeypatch.setattr(m, "_load_json_registry", _boom)
    resp = asyncio.run(org_sinks())
    assert resp["success"] is True
    assert resp["data"] == []
    assert resp["meta"]["count"] == 0


def test_sinks_registry_file_contract():
    """正本文件契约:schema=sinks.v1,行含必备指针字段(planned 件 sha16 可空)。"""
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "registry" / "sinks.json"
    reg = json.loads(p.read_text(encoding="utf-8"))
    assert reg["schema"] == "sinks.v1"
    for row in reg["sinks"]:
        assert {"sink_id", "frame", "title", "repo", "path", "status"} <= set(row)
        assert row["status"] in ("planned", "live")
        if row["status"] == "live":
            assert row.get("sha16"), "live 件必须锚 sha16"


def test_compass_ledgers_registry_contract():
    """compass 两台账代合并(#2871 方式②)正本契约:文件+键+owner=compass+负结果字段在。"""
    import json
    from pathlib import Path
    reg = Path(__file__).resolve().parents[1] / "registry"
    jp = json.loads((reg / "judging_pipelines.json").read_text(encoding="utf-8"))
    assert len(jp["judging_pipelines"]) == 3
    for row in jp["judging_pipelines"]:
        assert row["owner"] == "compass"
        assert "negative_result" in row, "负结果照报字段必在"
    mio = json.loads((reg / "memory_io.json").read_text(encoding="utf-8"))
    assert len(mio["memory_io"]) == 1 and mio["memory_io"][0]["owner"] == "compass"
