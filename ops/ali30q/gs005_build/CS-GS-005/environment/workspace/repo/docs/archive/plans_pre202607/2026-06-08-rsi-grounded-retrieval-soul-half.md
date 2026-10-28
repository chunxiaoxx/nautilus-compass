# RSI grounded-retrieval soul 半边 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 `fde_verdicts.items[].reason`(打回项避坑知识·当前死记录)暴露成 producer 可跨题检索的 grounding feed,并建一个可证伪的 pass@k probe 度量 harness。

**Architecture:** 两个独立纯组件。(1) `extract_grounding` 纯核跨 verdict 行展平打回 items + 薄 `GET /api/platform/fde/grounding` 路由(复用 `FdeVerdict` 模型,只读)。(2) `grounding_probe` 薄 adapter,复用 `escape_noise_stats.aggregate_paired_multiseed`(配对符号检验 + escapes_noise)+ `benchmark_verifier.pass_at_k_from_results`。无语义检索(compass turf)、无注入(V5 turf)。

**Tech Stack:** Python 3.11 · FastAPI · SQLAlchemy(sqlite in-memory 测试 fixture)· pytest · 纯函数 0 第三方新依赖。

**Gated(G-rsi·anchor#3):** 全 fixture TDD。**不**改 `main.py`(不 live wire 路由进生产)、**不**部署、**不**接 compass/V5 真回路。路由经独立 TestClient app 验(镜像 `test_fde_verdict_api.py`)。

---

## Task 1: `extract_grounding` 纯核(展平打回 items)

**Files:**
- Create: `phase3/backend/services/fde_grounding.py`
- Test: `phase3/backend/tests/test_fde_grounding.py`

**Step 1: Write the failing test**

`phase3/backend/tests/test_fde_grounding.py`:
```python
"""W6 RSI soul 半边 · grounding 暴露端纯核 extract_grounding.

跨 fde_verdicts 行展平打回项(pass is False)→ 可检索 grounding feed。
只读派生·fail-soft·无语义检索(compass turf)。
"""
from __future__ import annotations

from services.fde_grounding import extract_grounding


def _verdict(task_uid, source, items, *, checklist_uid="cl", score=0.5,
             created_at="2026-06-08T10:00:00"):
    return {"task_uid": task_uid, "source": source, "checklist_uid": checklist_uid,
            "score": score, "created_at": created_at, "items": items}


def test_emits_only_failed_items_with_reason_and_keys():
    rows = [_verdict("data_002", "soul", [
        {"id": "c1", "pass": True, "veto": True, "reason": ""},
        {"id": "c5", "pass": False, "veto": True,
         "reason": "veto: xlsx 与 docx 客户数不一致"},
        {"id": "c8", "pass": False, "veto": False, "reason": "图表缺单位"},
    ])]
    out = extract_grounding(rows)
    assert len(out) == 2                      # 只 c5 + c8 打回项·c1 pass 跳过
    c5 = next(r for r in out if r["item_id"] == "c5")
    assert c5["reason"] == "veto: xlsx 与 docx 客户数不一致"
    assert c5["task_uid"] == "data_002"
    assert c5["checklist_uid"] == "cl"
    assert c5["veto"] is True
    assert c5["source"] == "soul"
    assert c5["score"] == 0.5
    assert c5["created_at"] == "2026-06-08T10:00:00"


def test_veto_only_filters_to_hard_rules():
    rows = [_verdict("t", "soul", [
        {"id": "c5", "pass": False, "veto": True, "reason": "硬约束违反"},
        {"id": "c8", "pass": False, "veto": False, "reason": "软缺陷"},
    ])]
    out = extract_grounding(rows, veto_only=True)
    assert [r["item_id"] for r in out] == ["c5"]


def test_source_and_since_and_limit_filters():
    rows = [
        _verdict("a", "soul", [{"id": "x", "pass": False, "veto": False, "reason": "r1"}],
                 created_at="2026-06-01T00:00:00"),
        _verdict("b", "v5", [{"id": "y", "pass": False, "veto": False, "reason": "r2"}],
                 created_at="2026-06-08T00:00:00"),
    ]
    assert [r["item_id"] for r in extract_grounding(rows, source="v5")] == ["y"]
    assert [r["item_id"] for r in extract_grounding(rows, since="2026-06-05T00:00:00")] == ["y"]
    assert len(extract_grounding(rows, limit=1)) == 1


def test_fail_soft_on_malformed_items():
    rows = [
        {"task_uid": "t", "source": "soul", "items": None},          # items 非 list
        {"task_uid": "t", "source": "soul", "items": ["notadict",    # item 非 dict
            {"id": "z", "pass": False, "reason": "ok"}]},            # 缺 veto/checklist_uid
    ]
    out = extract_grounding(rows)
    assert len(out) == 1
    assert out[0]["item_id"] == "z"
    assert out[0]["veto"] is False        # 缺 veto → False
    assert out[0]["reason"] == "ok"


def test_pass_none_is_not_a_failure():
    rows = [{"task_uid": "t", "source": "soul",
             "items": [{"id": "q", "pass": None, "reason": "未判"}]}]
    assert extract_grounding(rows) == []   # pass is not False → 不算打回
```

**Step 2: Run test to verify it fails**

Run: `cd phase3/backend && python -m pytest tests/test_fde_grounding.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'services.fde_grounding'`

**Step 3: Write minimal implementation**

`phase3/backend/services/fde_grounding.py`:
```python
"""W6 RSI soul 半边 · grounding 暴露端纯核.

跨 fde_verdicts 行展平打回项(pass is False)→ 可检索 grounding feed,每条带
reason 原文 + 已有结构键。纯派生·只读·fail-soft·**无语义检索**(compass bge-m3 turf)、
**无注入**(V5 producer turf)。复活 design_20260605 指的"死记录":verdict items[].reason。

resurrects the per-item fail-reason — the content-level RSI signal that V5 agent-fitness
(scalar pass率) and compass PoI (score) both discard.
"""
from __future__ import annotations

from typing import Iterable, Optional


def extract_grounding(
    verdict_rows: Iterable[dict],
    *,
    source: Optional[str] = None,
    veto_only: bool = False,
    since: Optional[str] = None,   # ISO8601 字符串·按 created_at 字典序比较
    limit: Optional[int] = None,
) -> list[dict]:
    """展平 verdict 行的打回 items(pass is False)成 grounding 记录列表.

    一条打回 item = ``it.get("pass") is False``(缺/None 不算失败·fail-soft)。
    veto_only=True 只留硬约束(veto)规则。返回纯 JSON-able dict 列表。
    """
    out: list[dict] = []
    for v in verdict_rows:
        if not isinstance(v, dict):
            continue
        if source is not None and v.get("source") != source:
            continue
        created = v.get("created_at")
        if since is not None and created is not None and created < since:
            continue
        items = v.get("items")
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            if it.get("pass") is not False:        # 只打回项
                continue
            veto = bool(it.get("veto"))
            if veto_only and not veto:
                continue
            out.append({
                "reason": it.get("reason", ""),
                "task_uid": v.get("task_uid"),
                "checklist_uid": v.get("checklist_uid"),
                "item_id": it.get("id"),
                "veto": veto,
                "source": v.get("source"),
                "score": v.get("score"),
                "created_at": created,
            })
    if limit is not None:
        out = out[:limit]
    return out
```

**Step 4: Run test to verify it passes**

Run: `cd phase3/backend && python -m pytest tests/test_fde_grounding.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add phase3/backend/services/fde_grounding.py phase3/backend/tests/test_fde_grounding.py
git commit -m "feat(rsi): extract_grounding 纯核 · 展平 fde_verdicts 打回项成可检索 feed"
```

---

## Task 2: `GET /api/platform/fde/grounding` 薄路由

**Files:**
- Create: `phase3/backend/api/fde_grounding.py`
- Test: append to `phase3/backend/tests/test_fde_grounding.py`

**Step 1: Write the failing test**

Append to `phase3/backend/tests/test_fde_grounding.py`:
```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 · register mappers
from models.fde_verdict import FdeVerdict  # noqa: F401
from utils.database import get_db
from api.fde_verdict import router as verdict_router
from api.fde_grounding import router as grounding_router


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
    app.include_router(verdict_router)
    app.include_router(grounding_router)
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def _ingest(client, verdict_id, task_uid, source, items, score=0.5):
    return client.post("/api/platform/fde/verdict", json={
        "verdict_id": verdict_id, "task_uid": task_uid, "source": source,
        "checklist_uid": task_uid + "-cl", "overall_pass": False,
        "veto_failed": True, "score": score, "items": items})


def test_grounding_endpoint_returns_failed_items_across_tasks(client):
    _ingest(client, "v1", "data_002", "soul", [
        {"id": "c5", "pass": False, "veto": True, "reason": "客户数不一致"},
        {"id": "c1", "pass": True, "veto": True, "reason": ""}])
    _ingest(client, "v2", "data_009", "v5", [
        {"id": "c3", "pass": False, "veto": False, "reason": "缺单位"}])

    r = client.get("/api/platform/fde/grounding")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    reasons = {g["item_id"]: g["reason"] for g in body["data"]}
    assert reasons == {"c5": "客户数不一致", "c3": "缺单位"}   # 跨 2 题·只打回项


def test_grounding_endpoint_veto_only_and_source_filters(client):
    _ingest(client, "v1", "t", "soul", [
        {"id": "c5", "pass": False, "veto": True, "reason": "硬"},
        {"id": "c8", "pass": False, "veto": False, "reason": "软"}])
    r = client.get("/api/platform/fde/grounding?veto_only=true")
    assert [g["item_id"] for g in r.json()["data"]] == ["c5"]
    r2 = client.get("/api/platform/fde/grounding?source=v5")
    assert r2.json()["data"] == []


def test_grounding_endpoint_empty_when_no_verdicts(client):
    r = client.get("/api/platform/fde/grounding")
    assert r.status_code == 200
    assert r.json()["data"] == []
```

**Step 2: Run test to verify it fails**

Run: `cd phase3/backend && python -m pytest tests/test_fde_grounding.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'api.fde_grounding'`

**Step 3: Write minimal implementation**

`phase3/backend/api/fde_grounding.py`:
```python
"""W6 RSI soul 半边 · grounding 暴露 API · GET /api/platform/fde/grounding.

只读暴露 fde_verdicts 打回项的避坑 reason feed,供 compass 摄入 bge-m3 语料库。
薄壳 = 查 FdeVerdict 行 → services.fde_grounding.extract_grounding → envelope。
**无语义检索/排序**(compass turf)·**无注入**(V5 turf)。镜像 fde_verdict.py 约定。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from utils.database import get_db
from models.fde_verdict import FdeVerdict
from services.fde_grounding import extract_grounding

router = APIRouter(prefix="/api/platform/fde", tags=["FDE Grounding (RSI)"])


@router.get("/grounding")
def get_grounding(
    source: str | None = None,
    veto_only: bool = False,
    since: str | None = None,
    limit: int | None = None,
    db=Depends(get_db),
):
    """跨题暴露打回项 grounding feed(只读派生)."""
    rows = (
        db.query(FdeVerdict)
        .order_by(FdeVerdict.created_at.desc(), FdeVerdict.id.desc())
        .all()
    )
    feed = extract_grounding(
        [r.to_dict() for r in rows],
        source=source, veto_only=veto_only, since=since, limit=limit,
    )
    return {"success": True, "data": feed, "error": None}
```

**Step 4: Run test to verify it passes**

Run: `cd phase3/backend && python -m pytest tests/test_fde_grounding.py -v`
Expected: PASS (8 tests total)

**Step 5: Commit**

```bash
git add phase3/backend/api/fde_grounding.py phase3/backend/tests/test_fde_grounding.py
git commit -m "feat(rsi): GET /api/platform/fde/grounding 薄路由 · 暴露打回项 feed(只读·未 wire main)"
```

> **NOTE(gated):** 不改 `phase3/backend/main.py` 挂载本 router —— live wire 进生产是 G-cloud gated 步骤,待首验假说通过 + 用户明示再做。

---

## Task 3: `grounding_probe` 度量 harness(复用 escape_noise_stats)

**Files:**
- Create: `phase3/agent-engine/benchmarks/grounding_probe.py`
- Test: `phase3/agent-engine/benchmarks/test_grounding_probe.py`

**Step 1: Write the failing test**

`phase3/agent-engine/benchmarks/test_grounding_probe.py`:
```python
"""W6 RSI soul 半边 · grounding probe 度量 harness(可证伪仪器).

control(无注入)vs grounded(有注入)同批两臂 → pass@k delta + 符号检验 → escapes_noise。
薄 adapter·复用 escape_noise_stats.aggregate_paired_multiseed + benchmark_verifier.pass_at_k。
诚实判据:escapes_noise=True 才认 grounding 有效;平/降 = 退回纯 FDE。
"""
from grounding_probe import build_seed_record, grounding_probe


def test_build_seed_record_computes_pass_at_1_per_arm():
    rec = build_seed_record(
        control_items={"taskA": False, "taskB": False},
        grounded_items={"taskA": True, "taskB": False},
    )
    assert rec["control"]["pass_at_1"] == 0.0
    assert rec["grounded"]["pass_at_1"] == 0.5
    assert rec["control"]["items"] == {"taskA": False, "taskB": False}


def test_grounding_probe_grounded_clean_win_escapes_noise():
    # 3 seeds · grounded 每题每 seed 都赢 control → 应 escapes_noise
    seeds = [
        build_seed_record({"t1": False, "t2": False}, {"t1": True, "t2": True}),
        build_seed_record({"t1": False, "t2": False}, {"t1": True, "t2": True}),
        build_seed_record({"t1": False, "t2": False}, {"t1": True, "t2": True}),
    ]
    report = grounding_probe(seeds)
    assert report["escapes_noise"] is True
    assert report["treatment"]["key"] == "grounded"
    assert report["item_level"]["treatment_wins"] == 6
    assert report["item_level"]["baseline_wins"] == 0


def test_grounding_probe_no_delta_does_not_escape():
    seeds = [
        build_seed_record({"t1": True, "t2": False}, {"t1": True, "t2": False}),
        build_seed_record({"t1": True, "t2": False}, {"t1": True, "t2": False}),
    ]
    report = grounding_probe(seeds)
    assert report["escapes_noise"] is False
    assert report["item_level"]["discordant"] == 0


def test_grounding_probe_grounded_worse_does_not_escape():
    seeds = [
        build_seed_record({"t1": True, "t2": True}, {"t1": False, "t2": False}),
        build_seed_record({"t1": True, "t2": True}, {"t1": False, "t2": False}),
    ]
    report = grounding_probe(seeds)
    assert report["escapes_noise"] is False          # grounded 更差·net 负
    assert report["treatment_net"]["mean"] < 0
```

**Step 2: Run test to verify it fails**

Run: `cd phase3/agent-engine/benchmarks && python -m pytest test_grounding_probe.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'grounding_probe'`

**Step 3: Write minimal implementation**

`phase3/agent-engine/benchmarks/grounding_probe.py`:
```python
"""W6 RSI soul 半边 · grounding probe 度量 harness.

control(无 grounding 注入)vs grounded(有注入)同批两臂逐次成败 → escapes_noise 判据。
**薄 adapter** —— 配对符号检验 + escapes_noise 逻辑全复用 escape_noise_stats(anchor#5),
pass@1 复用 benchmark_verifier。本模块只把 grounding control/grounded 结果整形成
aggregate_paired_multiseed 吃的 seed_record,再委托。

可证伪判据(诚实):escapes_noise=True(grounded net>0 且每 seed 正 且 sign_p<0.05)才认
RSI grounding 有效;平/降 → 退回纯 FDE,不自欺(design_20260605 红线)。
"""
from __future__ import annotations

from typing import Dict, List

from escape_noise_stats import aggregate_paired_multiseed
from benchmark_verifier import pass_at_k_from_results

CONTROL = "control"
GROUNDED = "grounded"


def build_seed_record(control_items: Dict[str, bool],
                      grounded_items: Dict[str, bool]) -> Dict:
    """构造一个 seed 的配对记录(control vs grounded).

    items = {task_uid(或 attempt_id): pass_bool}。pass_at_1 复用无偏估计量。
    """
    return {
        CONTROL: {"pass_at_1": pass_at_k_from_results(control_items.values(), 1),
                  "items": dict(control_items)},
        GROUNDED: {"pass_at_1": pass_at_k_from_results(grounded_items.values(), 1),
                   "items": dict(grounded_items)},
    }


def grounding_probe(seed_records: List[Dict]) -> Dict:
    """N seeds 的 control/grounded 两臂 → escape-the-noise verdict(委托复用层)."""
    return aggregate_paired_multiseed(seed_records, CONTROL, GROUNDED)
```

**Step 4: Run test to verify it passes**

Run: `cd phase3/agent-engine/benchmarks && python -m pytest test_grounding_probe.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add phase3/agent-engine/benchmarks/grounding_probe.py phase3/agent-engine/benchmarks/test_grounding_probe.py
git commit -m "feat(rsi): grounding_probe 度量 harness · 复用 escape_noise_stats 出 escapes_noise 判据"
```

---

## 完成验收(verification-before-completion)

- `cd phase3/backend && python -m pytest tests/test_fde_grounding.py -v` → 8 pass。
- `cd phase3/agent-engine/benchmarks && python -m pytest test_grounding_probe.py -v` → 4 pass。
- 全套不回退:`cd phase3/backend && python -m pytest tests/test_fde_verdict_api.py -v` → 仍 pass(未碰 fde_verdict)。
- 确认 `main.py` 未改(grep 无 fde_grounding) → 路由未 live wire(gated 守住)。

## follow-up(本 session 不做·gated)
- live wire 路由进 `main.py` + 部署(G-cloud·待首验通 + 用户明示)。
- 同步 compass:grounding feed 端点契约(摄入 bge-m3)+ 同步 V5:producer retrieve+inject 对接面。
- 真跑实验:data_003 同领域题 + V5 control-vs-grounded → grounding_probe 出 escapes_noise。
