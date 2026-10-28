"""Task 1 · GET /api/platform/control-plane 聚合脊柱 TDD.

自建 app + include control_plane router + override get_db(sqlite·空表 fail-soft)。
不 import main(本地不可 import)。参考 test_fde_grounding 的 fixture 模式。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register mappers
from models.fde_verdict import FdeVerdict  # noqa: F401
from models.fde_rsi_delta import FdeRsiDelta  # noqa: F401
from utils.database import get_db
from api.control_plane import router as control_plane_router


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(control_plane_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_control_plane_returns_four_systems_and_loops(client):
    r = client.get("/api/platform/control-plane")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]

    # 四系统 + loops + pulse 全在
    assert set(data.keys()) >= {"soul", "compass", "dmas", "loops", "pulse"}

    # soul 半边 = verdict 流 + RSI ΔReward
    assert "verdicts" in data["soul"]
    assert "rsi_deltas" in data["soul"]
    assert "generalization" in data["soul"]
    assert "provenance" in data["soul"]
    assert data["soul"]["generalization"]["verdict"] == "no_data"
    assert data["soul"]["provenance"]["status"] == "offline"

    # compass = recall(fail-soft·可 offline 占位)
    assert "recall" in data["compass"]

    # dmas = agent 编队
    assert "agents" in data["dmas"]

    # loops = 两条闭环回放
    assert isinstance(data["loops"], list)
    assert len(data["loops"]) == 2

    # pulse = 系统脉搏
    assert "today_verdicts" in data["pulse"]


def test_rerun_probe_runs_grounding_probe(client):
    """POST /control-plane/rerun-probe → 真调 grounding_probe_twosample(只读度量)。

    融贯改造:rerun probe 是 control-plane 自己命名空间下的只读统计重算,
    不再占用 /api/platform/dispatch(那是既有 platform_dispatch.py 的鉴权机器
    控制 dispatch · 不重造 · 不撞车)。
    """
    r = client.post(
        "/api/platform/control-plane/rerun-probe",
        json={
            "bare": [0.0, 0.26, 0.27, 0.28, 0.0, 0.27],
            "grounded": [0.32, 0.36, 0.28, 0.26, 0.0, 0.30],
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert "escapes_noise" in data
    assert isinstance(data["escapes_noise"], bool)
    assert "delta_reward" in data
    assert isinstance(data["delta_reward"], (int, float))


def test_rerun_probe_rejects_missing_arrays(client):
    """缺 bare/grounded 数组 → 边界 fail-fast(success=False·不进探针)。"""
    r = client.post(
        "/api/platform/control-plane/rerun-probe",
        json={"bare": [0.1, 0.2]},  # 缺 grounded
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is False
    assert body.get("data") is None


def test_rerun_probe_no_longer_collides_with_platform_dispatch(client):
    """回归守卫:control-plane router 不得再注册 /api/platform/dispatch。

    旧版在 /dispatch 上注册无鉴权 dispatch,遮蔽了既有 platform_dispatch.py 的
    鉴权 dispatch(CRITICAL)。融贯后该 path 必须从 control-plane 移除。
    """
    paths = {getattr(r, "path", None) for r in control_plane_router.routes}
    assert "/api/platform/dispatch" not in paths, (
        f"control-plane 仍占用 /dispatch(撞既有鉴权端点):{paths}"
    )


def test_rerun_probe_rejects_oversized_payload(client):
    """HIGH·DoS guard:超体量 payload(C(n,k)>200k)→ 快速拒绝,绝不爆炸枚举。

    50 元素(bare 25 + grounded 25)· C(50,25)≈1.26e14 远超 _PERM_EXACT_CAP=200000。
    无 guard 时会尝试枚举 ~1e14 次置换 = 计算型 DoS(端点挂死)。
    期望:快速返回(秒级)· success=False · error 提示超上限。
    """
    import time

    t0 = time.monotonic()
    r = client.post(
        "/api/platform/control-plane/rerun-probe",
        json={"bare": [0.1] * 25, "grounded": [0.2] * 25},
    )
    elapsed = time.monotonic() - t0
    # 必须快速返回(没有进入爆炸枚举)。宽松上限 5s 兜异常环境抖动。
    assert elapsed < 5.0, f"guard 未生效·耗时 {elapsed:.2f}s(疑似进入置换枚举)"
    body = r.json()
    assert body["success"] is False, r.text
    assert body.get("data") is None
    err = (body.get("error") or "").lower()
    assert ("上限" in (body.get("error") or "")) or ("too large" in err), body
