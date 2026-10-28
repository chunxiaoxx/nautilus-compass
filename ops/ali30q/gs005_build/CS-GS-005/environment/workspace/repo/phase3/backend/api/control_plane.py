"""接地平台 · GET /api/platform/control-plane 聚合脊柱(Task 1).

ONE 只读端点把 soul / compass / dmas 三系统状态 + 两条 RSI+FDE 闭环回放 +
系统脉搏聚合成一个 JSON,供 agent(curl)+ 人(React 舰桥)消费。

复用 W-A `api/platform_rsi_fde.py` 的 section 积木(不重造):
  - _verdicts_section / _agents_section / _events_section / _poi_section
本文件只新增 3 个 section(rsi_deltas / recall / loops / pulse)+ 组装路由。

fail-soft 铁律:每个 section try/except,任一子系统挂(表缺/compass 断)只返
空结构或 offline 占位,绝不 500 整个端点 —— 同一端点要同时跑本地 sqlite 测试
夹具和生产 postgres(5433·可能空表)。
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
import logging
import math
import os
import threading
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Body

from utils.database import get_db
from api.platform_rsi_fde import (
    _verdicts_section,
    _agents_section,
    _events_section,
    _poi_section,
)

router = APIRouter(prefix="/api/platform", tags=["Control Plane (接地平台)"])
logger = logging.getLogger(__name__)

# 置换检验体量上界(HIGH·DoS guard)· 与 grounding_probe._PERM_EXACT_CAP 同值。
# grounding_probe_twosample 内部 combinations(range(nb+ng), ng) 全枚举置换,
# N 大时 C(nb+ng, ng) 爆炸(C(40,20)≈1.4e11)→ 网络可达调度入口挂死 = 计算型
# DoS。dispatch 必须在调用前对输入体量设上界,超限直接拒绝。
_PERM_EXACT_CAP = 200_000
_GENERALIZATION_TASK_LIMIT = 200
_GENERALIZATION_MIN_TASKS = 3
_GENERALIZATION_ESCAPE_MAJORITY = 0.6
_PROVENANCE_AGENTS = (
    ("nautilus-prime-001", "code_evolve"),
    ("kairos", "reflective"),
    ("v7-telegram", "aggregator"),
)
_PROVENANCE_TIMEOUT = 2.2
_PROVENANCE_TOTAL_TIMEOUT = 6.0
_PROVENANCE_CACHE_TTL = 20
_PROVENANCE_EVENTS_CAP = 20

_provenance_cache: dict[str, tuple[float, dict]] = {}
_provenance_cache_lock = threading.Lock()


def _safe(fn, fallback):
    """Run a section · return fallback on ANY error (fail-soft · never 500)."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 — fail-soft per section
        logger.debug("control-plane section skipped: %s", str(exc)[:120])
        return fallback


def _rsi_deltas_section(db) -> dict:
    """最近的 grounded-vs-bare ΔReward 测量(RSI 外部 fitness 信号)。

    空表 / 表缺 fail-soft → {rows:[], count:0}。
    """
    from models.fde_rsi_delta import FdeRsiDelta

    try:
        rows = (
            db.query(FdeRsiDelta)
            .order_by(FdeRsiDelta.created_at.desc(), FdeRsiDelta.id.desc())
            .limit(20)
            .all()
        )
        return {"rows": [r.to_dict() for r in rows], "count": len(rows)}
    except Exception as exc:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("rsi_deltas section skipped: %s", str(exc)[:120])
        return {"rows": [], "count": 0}


def _latest_external_verdict_at(db):
    """返回最近 FdeVerdict.created_at（包括未 external_verified）."""
    try:
        from models.fde_verdict import FdeVerdict
        from sqlalchemy import func

        row = db.query(func.max(FdeVerdict.created_at)).first()
        if row is None:
            return None
        return _parse_ts(row[0])
    except Exception as exc:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("latest_external_verdict_at failed: %s", str(exc)[:120])
        return None


def _latest_rsi_delta_at(db):
    """返回最近 FdeRsiDelta.created_at."""
    try:
        from models.fde_rsi_delta import FdeRsiDelta
        from sqlalchemy import func

        row = db.query(func.max(FdeRsiDelta.created_at)).first()
        if row is None:
            return None
        return _parse_ts(row[0])
    except Exception as exc:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("latest_rsi_delta_at failed: %s", str(exc)[:120])
        return None


def _generalization_section(db) -> dict:
    """RSI 泛化记分板: DB 聚合 + 有界任务窗口，防止公开端点 O(N) 放大。"""
    from models.fde_rsi_delta import FdeRsiDelta
    from sqlalchemy import case, func

    try:
        top_tasks = (
            db.query(
                FdeRsiDelta.task_uid.label("task_uid"),
                func.max(FdeRsiDelta.created_at).label("latest_at"),
            )
            .group_by(FdeRsiDelta.task_uid)
            .order_by(func.max(FdeRsiDelta.created_at).desc())
            .limit(_GENERALIZATION_TASK_LIMIT)
            .subquery()
        )

        rows = (
            db.query(
                FdeRsiDelta.task_uid.label("task_uid"),
                func.count(FdeRsiDelta.id).label("n_runs"),
                func.sum(case((FdeRsiDelta.escapes_noise.is_(True), 1), else_=0)).label("n_escaped"),
                func.max(FdeRsiDelta.delta_reward).label("best_delta"),
                func.max(FdeRsiDelta.created_at).label("latest_at"),
            )
            .join(top_tasks, FdeRsiDelta.task_uid == top_tasks.c.task_uid)
            .group_by(FdeRsiDelta.task_uid)
            .order_by(func.max(FdeRsiDelta.created_at).desc())
            .all()
        )
    except Exception as exc:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("generalization section failed: %s", str(exc)[:120])
        return {"verdict": "no_data", "per_task": []}

    per_task = []
    for r in rows:
        n_runs = int(r.n_runs or 0)
        n_escaped = int(r.n_escaped or 0)
        per_task.append({
            "task_uid": r.task_uid,
            "task_runs": n_runs,
            "escapes_noise_count": n_escaped,
            "escaped": n_escaped > 0,
            "best_delta": float(r.best_delta or 0.0),
            "latest_at": _parse_ts(r.latest_at).isoformat() if _parse_ts(r.latest_at) else None,
        })

    tested = len(per_task)
    escaped_tasks = sum(1 for item in per_task if item["escaped"])
    escape_rate = (escaped_tasks / tested) if tested else 0.0

    if tested == 0:
        verdict = "no_data"
        label = "无数据"
        reason = "尚无 RSI ΔReward 记录"
        next_action = "跑首个两臂实验"
    elif tested < _GENERALIZATION_MIN_TASKS:
        verdict = "insufficient_evidence"
        label = "证据不足"
        reason = f"{escaped_tasks}/{tested} 题 escape · 需 ≥{_GENERALIZATION_MIN_TASKS} 道任务后下结论"
        next_action = f"再跑 {_GENERALIZATION_MIN_TASKS - tested} 道跨任务两臂实验"
    elif escape_rate >= _GENERALIZATION_ESCAPE_MAJORITY:
        verdict = "generalizing"
        label = "疑似泛化"
        reason = f"{escaped_tasks}/{tested} 题 escape(多数) · grounding 有跨题迹象"
        next_action = "继续扩题验证并观察是否稳定"
    else:
        verdict = "task_specific"
        label = "题特异"
        reason = f"{escaped_tasks}/{tested} 题 escape(少数) · grounding 更像题特异"
        next_action = "标注哪类任务 escape，避免提前外推"

    return {
        "verdict": verdict,
        "label": label,
        "reason": reason,
        "next_action": next_action,
        "tasks_tested": tested,
        "tasks_escaped": escaped_tasks,
        "escape_rate": round(escape_rate, 4),
        "min_tasks": _GENERALIZATION_MIN_TASKS,
        "per_task": per_task,
    }


def _provenance_fetch_one(base: str, agent_id: str, agent_kind: str) -> dict:
    url = f"{base.rstrip('/')}/api/provenance?{urllib.parse.urlencode({'agent': agent_id, 'since': '2026-06-01'})}"
    try:
        resp = urllib.request.urlopen(url, timeout=_PROVENANCE_TIMEOUT)  # noqa: S310
        raw = resp.read()
        data = json.loads(raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw)
        events = data.get("events", [])
        if not isinstance(events, list):
            events = []
        return {
            "agent_id": data.get("agent_id", agent_id),
            "agent_kind": data.get("agent_kind", agent_kind),
            "count": data.get("count", len(events)),
            "fitness_ref_hit_rate": data.get("fitness_ref_hit_rate"),
            "events": events[:_PROVENANCE_EVENTS_CAP],
            "status": "online",
        }
    except Exception as exc:  # noqa: BLE001
        logger.debug("provenance fetch failed (%s): %s", agent_id, str(exc)[:120])
        return {"agent_id": agent_id, "agent_kind": agent_kind, "status": "offline"}


def _provenance_section() -> dict:
    base = os.environ.get("FDE_V5_PROVENANCE_URL", "").strip()
    note = "V5 provenance GET pull (fail-soft)"
    if not base:
        return {
            "status": "offline",
            "source": "v5_provenance_get",
            "agents": [{"agent_id": aid, "agent_kind": kind, "status": "offline"}
                       for aid, kind in _PROVENANCE_AGENTS],
            "note": note,
        }

    now = time.time()
    with _provenance_cache_lock:
        cached = _provenance_cache.get(base)
        if cached and now - cached[0] < _PROVENANCE_CACHE_TTL:
            return cached[1]

    payload = {"status": "offline", "source": "v5_provenance_get", "agents": [], "note": note}
    futures = {}
    deadline = now + _PROVENANCE_TOTAL_TIMEOUT
    try:
        with ThreadPoolExecutor(max_workers=len(_PROVENANCE_AGENTS)) as ex:
            for agent_id, agent_kind in _PROVENANCE_AGENTS:
                futures[ex.submit(_provenance_fetch_one, base, agent_id, agent_kind)] = (agent_id, agent_kind)

            for future in as_completed(futures):
                remaining = max(0.0, deadline - time.time())
                if remaining <= 0.0:
                    raise TimeoutError
                agent_id, agent_kind = futures[future]
                try:
                    payload["agents"].append(future.result(timeout=remaining))
                except Exception as exc:  # noqa: BLE001
                    logger.debug("provenance agent failed (%s): %s", agent_id, str(exc)[:120])
                    payload["agents"].append({
                        "agent_id": agent_id,
                        "agent_kind": agent_kind,
                        "status": "offline",
                    })
    except TimeoutError:
        payload["status"] = "offline"
        for future, (agent_id, agent_kind) in list(futures.items()):
            if future.done():
                try:
                    payload["agents"].append(future.result(timeout=0))
                except Exception:
                    payload["agents"].append({
                        "agent_id": agent_id,
                        "agent_kind": agent_kind,
                        "status": "offline",
                    })
            else:
                payload["agents"].append({
                    "agent_id": agent_id,
                    "agent_kind": agent_kind,
                    "status": "offline",
                })
    if any(a.get("status") == "online" for a in payload["agents"]):
        payload["status"] = "online"

    with _provenance_cache_lock:
        _provenance_cache[base] = (time.time(), payload)
    return payload


def _recall_section() -> dict:
    """compass 检索接地 feed · 诚实 offline。

    compass recall 是 compass 的 MCP 工具面(G-turf),平台后端不可经 HTTP 直达
    (实测平台侧无 compass recall 接口),且 MCP 通道时断。融合闭环里 recall 的
    真接线归 compass 暴露 HTTP / 经 a2a · 平台只诚实标 offline,绝不伪造 feed。
    """
    return {"status": "offline",
            "note": "compass recall = MCP G-turf · 平台 HTTP 不可达 · 待 compass 暴露 HTTP/a2a"}


def _loops_section(db) -> list:
    """两条 RSI+FDE 闭环回放 · Task 3 装配真实 steps(build_loop_replays)。

    fail-soft:装配模块 import 失败 → 返原最小 stub(舰桥永不因此崩)。
    """
    try:
        from services.control_plane_loops import build_loop_replays
        return build_loop_replays(db)  # db-backed 接真·缺行 fail-soft 回退 curated
    except Exception as exc:  # noqa: BLE001 — fail-soft 退回 stub
        logger.debug("loops replay assembly skipped: %s", str(exc)[:120])
        return [
            {"loop_id": "radix_rsi",
             "title": "radix RSI grounded-retrieval", "steps": []},
            {"loop_id": "data_001_fde",
             "title": "data_001 FDE 买方闭环", "steps": []},
        ]


def _parse_ts(raw):
    """容错解析 created_at(可能 'YYYY-MM-DD HH:MM:SS.ffffff' 或带 +08:00)→ aware dt 或 None。"""
    if not raw:
        return None
    try:
        s = str(raw).replace(" ", "T")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:  # noqa: BLE001
        return None


# 活性阈值:最新**外部验证**(external_verified_at)距今超过此小时数 = soul 不活。
# 不硬编码"永远活",内循环刷屏也不算活(破自循环 Step 2 · 2026-07-06)。
_LIVENESS_STALE_HOURS = 48


def _pulse_section(db) -> dict:
    """系统脉搏 · 🔴 真实活性(按最新 verdict 时间算·非硬编码 True)+ 新鲜度。

    旧版 soul_alive 硬编码 True = 死系统也显"活"(可观测剧场·anchor #3 违)。
    现按最新 verdict created_at 距今计算:< _LIVENESS_STALE_HOURS 才算活,
    否则 soul_alive=False + 暴露 stale_hours/last_activity_at,让看板说真话。
    """
    latest = None
    verdicts_total = 0
    today_count = 0
    try:
        v = _verdicts_section(db, 50)
        verdicts_total = int(v.get("summary", {}).get("total", 0) or 0)
        now_date = datetime.now(timezone.utc).date()
        for row in (v.get("recent") or []):
            ts = _parse_ts(row.get("created_at"))
            if ts is None:
                continue
            if latest is None or ts > latest:
                latest = ts
            if ts.astimezone(timezone.utc).date() == now_date:
                today_count += 1
    except Exception:  # noqa: BLE001
        pass

    try:
        latest_delta = _latest_rsi_delta_at(db)
        if latest is None and latest_delta is not None:
            latest = latest_delta
        elif latest_delta is not None:
            latest = max(latest, latest_delta)
    except Exception:  # noqa: BLE001
        pass
    dmas_throughput = 0
    try:
        e = _events_section(db, 1)
        dmas_throughput = int(e.get("summary", {}).get("total", 0) or 0)
    except Exception:  # noqa: BLE001
        dmas_throughput = 0

    # cycle 时间只作 metadata 暴露(不再参与 soul_alive 判定)。
    last_cycle = None
    try:
        from sqlalchemy import text
        row = db.execute(
            text("SELECT MAX(created_at) FROM engine_cycle_outcomes")
        ).fetchone()
        if row is not None:
            last_cycle = _parse_ts(row[0])
    except Exception:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass

    # 🔴 soul 活性 = 最新**外部验证**新鲜度(破自循环 Step 2 · 2026-07-06)。
    # 内循环(auto-mint / bench_eval cycle / 未验证 verdict)继续跑但不算活——
    # 只有独立于生产者的 canonical verify(external_verified=True)才续命。
    last_external = None
    external_total = 0
    try:
        from sqlalchemy import func
        from models.fde_verdict import FdeVerdict
        row = (db.query(func.max(FdeVerdict.external_verified_at),
                        func.count(FdeVerdict.id))
                 .filter(FdeVerdict.external_verified.is_(True))
                 .first())
        if row is not None:
            last_external, external_total = row[0], int(row[1] or 0)
    except Exception:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    ref = latest
    if ref is not None and ref.tzinfo is None:
        ref = ref.replace(tzinfo=timezone.utc)
    stale_hours = round((now - ref).total_seconds() / 3600, 1) if ref else None
    soul_alive = (stale_hours is not None and stale_hours < _LIVENESS_STALE_HOURS)
    return {
        "soul_alive": soul_alive,            # 真实·按外部验证新鲜度(非 cycle·非硬编码)
        "last_external_verified_at": (last_external.isoformat()
                                      if last_external else None),
        "external_verified_total": external_total,
        "last_cycle_at": last_cycle.isoformat() if last_cycle else None,
        "last_activity_at": latest.isoformat() if latest else None,  # 与 stale_hours 一致
        "stale_hours": stale_hours,          # 外部验证静默小时数(None=从未验证)
        "verdicts_today": today_count,       # 真·今日 verdict 数
        "today_verdicts": verdicts_total,    # 旧字段=全量(前端兼容)·勿当今日
        "verdicts_total": verdicts_total,
        "dmas_throughput": dmas_throughput,
    }


@router.get("/convergence")
def convergence_scoreboard(db=Depends(get_db)):
    """收敛记分牌(方案④ · 2026-07-07):"有效收敛" = 5 个数字,不是叙事。

    协议:自治管道产的 verdict 必须带 artifacts.autonomous=true;
    手摇(对话框代产)不带 → producer_autonomy.ratio 造不了假。
    delivery_progress 是 feishu turf,平台读不到就诚实 null。
    """
    from datetime import timedelta
    from sqlalchemy import func, select
    from models.fde_verdict import FdeVerdict
    from models.fde_dispatch import FdeDispatch
    from models.agent_survival import AgentTransaction

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    week_ago_naive = week_ago.replace(tzinfo=None)  # naive-UTC 列(created_at)用

    def _aware(dt):
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    verified_rows = (db.query(FdeVerdict.external_verified_at, FdeVerdict.artifacts)
                       .filter(FdeVerdict.external_verified.is_(True)).all())
    verified_total = len(verified_rows)
    verified_7d = sum(1 for r in verified_rows
                      if r.external_verified_at
                      and _aware(r.external_verified_at) >= week_ago)
    autonomous = sum(1 for r in verified_rows
                     if (r.artifacts or {}).get("autonomous") is True)

    tx = db.query(func.coalesce(func.sum(AgentTransaction.amount), 0)).filter(
        AgentTransaction.type == "INCOME",
        AgentTransaction.category == "fde_external_verified")
    income_total = int(tx.scalar() or 0)
    income_7d = int(tx.filter(AgentTransaction.created_at >= week_ago_naive).scalar() or 0)

    settled_total = (db.query(func.count(FdeDispatch.id))
                       .filter(FdeDispatch.status == "settled").scalar() or 0)
    backed = (db.query(func.count(FdeDispatch.id))
                .filter(FdeDispatch.status == "settled",
                        FdeDispatch.task_uid.in_(
                            select(FdeVerdict.task_uid)
                            .where(FdeVerdict.external_verified.is_(True))))
                .scalar() or 0)

    return {
        "success": True,
        "data": {
            "external_verified": {"total": verified_total, "last_7d": verified_7d},
            "income": {"total": income_total, "delta_7d": income_7d},
            "producer_autonomy": {
                "autonomous_verified": autonomous,
                "verified_total": verified_total,
                "ratio": round(autonomous / verified_total, 4) if verified_total else 0.0,
                "note": "北极星指标 · 自治管道 verdict 须带 artifacts.autonomous=true",
            },
            "settle_integrity": {
                "settled_total": int(settled_total),
                "externally_backed": int(backed),
                "ratio": round(backed / settled_total, 4) if settled_total else 0.0,
            },
            "delivery_progress": {"delivered": None, "target": 11,
                                  "note": "feishu 派活表 turf · compass GET 回读后接入"},
            "generated_at": now.isoformat(),
        },
        "error": None,
    }


@router.get("/control-plane")
def control_plane(limit: int = Query(20, ge=1, le=100), db=Depends(get_db)):
    """接地平台聚合脊柱 · 一次只读快照。每个 section fail-soft。"""
    return {
        "success": True,
        "data": {
            "soul": {
                "verdicts": _safe(lambda: _verdicts_section(db, limit),
                                  {"summary": {"total": 0, "passed": 0, "pass_rate": 0.0},
                                   "recent": []}),
                "rsi_deltas": _safe(lambda: _rsi_deltas_section(db),
                                    {"rows": [], "count": 0}),
                "generalization": _safe(lambda: _generalization_section(db),
                                        {"verdict": "no_data", "per_task": []}),
                "provenance": _safe(_provenance_section, {"status": "offline", "agents": []}),
            },
            "compass": {
                "poi": _safe(lambda: _poi_section(db),
                             {"poi_eligible": 0, "eligible_tasks": []}),
                "recall": _safe(_recall_section,
                                {"status": "offline", "note": "compass 未接"}),
            },
            "dmas": {
                "agents": _safe(lambda: _agents_section(db),
                                {"total": 0, "active": 0, "by_status": []}),
                "bids": _safe(lambda: _events_section(db, limit),
                              {"summary": {"total": 0, "processed": 0},
                               "by_type": [], "recent": []}),
            },
            "loops": _safe(lambda: _loops_section(db), []),
            "pulse": _safe(lambda: _pulse_section(db),
                           {"soul_alive": True, "today_verdicts": 0,
                            "dmas_throughput": 0}),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "error": None,
    }


def _run_grounding_probe(payload: dict) -> dict:
    """调 agent-engine 的 grounding_probe_twosample(sys.path 处理·fail-soft)。

    grounding_probe.py 在 phase3/agent-engine/benchmarks/(不在 backend 下),
    import 走 sys.path 注入。import / 调用任一失败 → fail-soft 返错误不崩。
    """
    probe_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..",
                     "agent-engine", "benchmarks")
    )
    if probe_dir not in sys.path:
        sys.path.insert(0, probe_dir)
    try:
        from grounding_probe import grounding_probe_twosample
    except Exception as exc:  # noqa: BLE001 — fail-soft import
        logger.warning("grounding_probe import failed: %s", str(exc)[:160])
        return {"success": False,
                "error": f"grounding_probe import failed: {str(exc)[:120]}",
                "data": None}

    bare = payload.get("bare")
    grounded = payload.get("grounded")
    if not isinstance(bare, list) or not isinstance(grounded, list):
        return {"success": False,
                "error": "payload 缺 bare/grounded 数组",
                "data": None}
    # HIGH·DoS guard:置换检验全枚举 C(nb+ng, k) 次。N 大时爆炸 → 端点挂死。
    # 调用前算体量,超上界直接拒绝(min(nb,ng) 防 k 取大值溢出·组合数对称)。
    nb, ng = len(bare), len(grounded)
    perms = math.comb(nb + ng, min(nb, ng))
    if perms > _PERM_EXACT_CAP:
        return {"success": False,
                "error": (f"payload too large: {nb}+{ng} 元素需 {perms} 次"
                          f"精确置换,超上限 {_PERM_EXACT_CAP};请减少样本数"),
                "data": None}
    try:
        result = grounding_probe_twosample(bare, grounded)
    except Exception as exc:  # noqa: BLE001 — fail-soft call
        logger.warning("grounding_probe_twosample failed: %s", str(exc)[:160])
        return {"success": False,
                "error": f"grounding_probe failed: {str(exc)[:120]}",
                "data": None}
    return {"success": True, "data": result, "error": None}


@router.post("/control-plane/rerun-probe")
def rerun_probe(body: dict = Body(...), db=Depends(get_db)):
    """只读统计重算:跑 grounding_probe_twosample(RSI ΔReward 度量)· fail-soft。

    🔴 融贯改造(原 POST /api/platform/dispatch 已删除):
    机器控制 dispatch(派 goal / a2a / governance · 有副作用 · 需鉴权)由既有
    `api/platform_dispatch.py` 的 {target, action, payload} 端点负责(anchor #5
    不重造)。本端点只承担 control-plane 独有的**只读、无副作用**统计重算,
    放在 control-plane 自己的命名空间,不再占用 /dispatch、不再遮蔽鉴权端点。

    入参:{bare:[...], grounded:[...]}。DoS guard(置换枚举上界)保留。
    """
    bare = (body or {}).get("bare")
    grounded = (body or {}).get("grounded")
    return _run_grounding_probe({"bare": bare, "grounded": grounded})
