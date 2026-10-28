# -*- coding: utf-8 -*-
"""org_assay(b 档数据验证)端点单测:M3 契约草案 v0.1(docs/M3_B_TIER_API_DRAFT_20261006.md)。
run: cd backend && python -m pytest tests/test_org_assay.py -q
隔离:专用 engagement_id 前缀,测后清行,不触生产数据。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# conftest 会强制 localhost 测试库;本套件走平台隧道库(org_fuel 同库先例)——须在 import main 前扳回
os.environ["DATABASE_URL"] = os.environ.get("B_TIER_TEST_DSN",
                                            "postgresql://nautilus_user:nautilus2024@127.0.0.1:15432/nautilus_production")

import utils.database as _udb  # noqa: E402  # conftest 先建 engine(测试库),此处重绑到隧道库
from sqlalchemy import create_engine as _ce  # noqa: E402

_udb.engine = _ce(_udb.DATABASE_URL, pool_pre_ping=True)
_udb.SessionLocal.configure(bind=_udb.engine)

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)
H = {"X-Platform-Key": os.environ["PLATFORM_DISPATCH_KEY"]} if os.environ.get("PLATFORM_DISPATCH_KEY") else {}
PFX = "test-b-tier-"


def _traj(qid, msgs=None):
    return {"qid": qid, "trajectory": msgs or [{"role": "user", "content": "x"},
                                                {"role": "assistant", "content": "y"}]}


def test_validate_roundtrip_and_machine_gates():
    eng = PFX + "e1"
    body = {"engagement_id": eng, "criteria_sha": "ea20d6fd",
            "trajectories": [_traj("bt-1"), _traj("bt-2"), _traj("bt-2"),  # qid 重复
                             {"qid": "bt-3", "trajectory": []},             # render 空
                             _traj("bt-1")]}                                # 跨行 prompt 同纹(qid 同)
    r = client.post("/api/platform/org/assay/validate", json=body, headers=H)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["received_n"] == 5 and d["engagement_id"] == eng
    assert "sla_deadline" in d

    g = client.get(f"/api/platform/org/assay/validate/{eng}", headers=H).json()
    items = {i["qid"]: i for i in g["per_item"]}
    assert items["bt-1"]["gates"]["render_nonempty"] == "pass"
    assert items["bt-2"]["gates"]["qid_unique"] == "fail"                # 批内第二份
    assert items["bt-3"]["gates"]["render_nonempty"] == "fail"
    # 深门(需判读臂/held-out)未接入=UNVERIFIABLE 照报,非缺席
    assert items["bt-1"]["gates"]["heldout_disjoint"] == "unverifiable"
    assert g["summary"]["n"] == 5


def test_auth_required():
    import pytest
    if not os.environ.get("PLATFORM_DISPATCH_KEY"):
        pytest.skip("dev 无 key 配置,鉴权面放行(生产 fail-closed 由 platform_auth 保证)")
    r = client.post("/api/platform/org/assay/validate",
                    json={"engagement_id": PFX + "x", "trajectories": []})
    assert r.status_code in (401, 403)


def test_engagement_not_found():
    r = client.get(f"/api/platform/org/assay/validate/{PFX}none", headers=H)
    assert r.status_code == 404


def teardown_module():
    from utils.database import SessionLocal
    from sqlalchemy import text
    s = SessionLocal()
    s.execute(text("DELETE FROM assay_engagements WHERE engagement_id LIKE :p"), {"p": PFX + "%"})
    s.commit()
    s.close()
