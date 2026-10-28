"""最小本地 dev server · 只挂 control_plane router(绕开 main.py 本地不可 import)。

main.py 在本地不可 import(`api/agents.py` 拉 `services.agent_service`,该模块
只在 cloud fork 存在 · master/fork 分歧)。本脚本自建一个极小 FastAPI app,
只 include control_plane router,供本地 curl 验证 Task4 binding-DONE,不 import main。

跑法:
    cd phase3/backend && python scripts/run_control_plane_local.py
然后另开终端:
    curl http://127.0.0.1:8077/api/platform/control-plane
    curl -X POST http://127.0.0.1:8077/api/platform/dispatch \
        -H "Content-Type: application/json" \
        -d '{"action":"rerun_grounding_probe","payload":{"bare":[0.0,0.26,0.27,0.28,0.0,0.27],"grounded":[0.32,0.36,0.28,0.26,0.0,0.30]}}'

DB:连本地 postgres 5433 db=nautilus(PGCLIENTENCODING=UTF8)。连不上 → fail-soft
(空 db session · 各 section try/except 退回空结构 / loops 是 hardcode 真值不依赖 DB)。
"""
from __future__ import annotations

import os
import sys

# backend/ 入 sys.path(本脚本在 backend/scripts/ 下)。
_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# postgres client 编码(避免本地 locale 乱码)· 在建 engine 前设。
os.environ.setdefault("PGCLIENTENCODING", "UTF8")

import uvicorn  # noqa: E402
from fastapi import FastAPI  # noqa: E402

# 注册 AgentSurvival 到 mapper registry · 否则 control_plane 的 rsi_deltas section
# 用 ORM(db.query(FdeRsiDelta))会触发全 registry 配置,而 models.database.Agent
# 有 relationship('AgentSurvival')未加载 → InvalidRequestError → 该 section 静默
# fail-soft 返空(rsi_deltas 永远空)。生产 main.py 导入全部 model 不受影响,这里
# 是最小 dev server 才暴露的 latent bug · 显式 import 修复(仅本地验证脚本)。
import models.agent_survival  # noqa: E402,F401

from api.control_plane import router as control_plane_router  # noqa: E402

# 本地 postgres 5433 db=nautilus · 连不上则 fail-soft(section 各自 try/except)。
_LOCAL_DB_URL = os.getenv(
    "CONTROL_PLANE_LOCAL_DB_URL",
    "postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/nautilus",
)

_SessionLocal = None
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    _engine = create_engine(
        _LOCAL_DB_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3, "client_encoding": "utf8"},
    )
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
except Exception as exc:  # noqa: BLE001 — fail-soft · 无 DB 也要能起
    print(f"[dev-server] DB engine init failed (fail-soft · empty db): {exc}")
    _SessionLocal = None


class _NullDB:
    """无 DB 时的空 session 占位 · query 抛错 → section fail-soft 退回空结构。"""

    def query(self, *a, **k):  # noqa: ANN001
        raise RuntimeError("no local DB connection (fail-soft)")

    def rollback(self):  # noqa: D401
        pass

    def close(self):
        pass


def _local_get_db():
    """get_db 依赖覆盖 · 连本地 postgres 5433;连不上则给空 session 占位。"""
    if _SessionLocal is None:
        db = _NullDB()
        try:
            yield db
        finally:
            db.close()
        return
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Control Plane (local dev · Task4 verify)")
app.include_router(control_plane_router)

# 覆盖 control_plane.py 里 Depends(get_db) → 指向本地 5433(或空占位)。
from utils.database import get_db  # noqa: E402

app.dependency_overrides[get_db] = _local_get_db


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8077)
