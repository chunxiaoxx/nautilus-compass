"""W-A VIEW 看板 · GET /api/platform/rsi-fde (read-only RSI+FDE control-plane view).

The "可感知" headline for the perceivable control plane: ONE read that answers
"is the living system alive?" — FDE verdicts flowing (external buyer acceptance =
the only fitness that escapes the self-referential internal economy), agents
present (by survival status), platform_external_events streaming, plus a
PoI-eligibility summary DERIVED from passed verdicts.

Boundaries honored:
  - G-turf · the PoI summary is derived platform-side from fde_verdicts. It does
    NOT read compass PoI internals — it reports what FEEDS PoI (passed verdicts),
    not compass's ledger.
  - anchor #3 · deliberately does NOT touch pending_nau_rewards / votes (the
    self-referential signals the benchmark pivot moved away from).

Fail-soft per section: a missing table yields an empty section, never a 500, so
the same endpoint renders against the sqlite test fixture and the postgres
production target. Mirrors api/soul_activity.py raw-SQL conventions.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from utils.database import get_db

router = APIRouter(prefix="/api/platform/rsi-fde", tags=["RSI+FDE Control Plane"])
logger = logging.getLogger(__name__)

# agent_status values that count as "活跃" (heartbeat is dead across the fleet,
# so survival status — not last_heartbeat — is the honest liveness signal).
_ACTIVE_STATUSES = ("alive", "active")

# The RSI flywheel's deterministic track: 第3类 verdicts judged by compass's
# bench_eval (机器可判 reward 1.0/0.0·非 LLM judge), distinct from 第1/2类 soul QC.
_RSI_DETERMINISTIC_SOURCE = "compass/bench_eval"


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _safe_rows(db, sql: str, params: dict | None = None) -> list:
    """Run a read-only SELECT · return [] on any error (e.g. table absent)."""
    try:
        return db.execute(text(sql), params or {}).fetchall()
    except Exception as exc:  # noqa: BLE001 — fail-soft · never 500 the dashboard
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("rsi-fde query skipped: %s", str(exc)[:120])
        return []


def _verdicts_section(db, limit: int) -> dict:
    rows = _safe_rows(
        db,
        "SELECT verdict_id, task_uid, source, overall_pass, veto_failed, score, created_at "
        "FROM fde_verdicts ORDER BY created_at DESC, id DESC LIMIT :lim",
        {"lim": limit},
    )
    recent = [
        {
            "verdict_id": r[0],
            "task_uid": r[1],
            "source": r[2],
            "overall_pass": bool(r[3]),
            "veto_failed": bool(r[4]),
            "score": float(r[5]) if r[5] is not None else None,
            "created_at": str(r[6]) if r[6] is not None else None,
        }
        for r in rows
    ]
    # summary counts the WHOLE table (not just the page).
    tot = _safe_rows(
        db,
        "SELECT COUNT(*) AS t, SUM(CASE WHEN overall_pass THEN 1 ELSE 0 END) AS p "
        "FROM fde_verdicts",
    )
    total = int(tot[0][0]) if tot else 0
    passed = int(tot[0][1] or 0) if tot else 0
    return {
        "summary": {
            "total": total,
            "passed": passed,
            "pass_rate": round(passed / total, 4) if total else 0.0,
        },
        "recent": recent,
    }


def _agents_section(db) -> dict:
    dist = _safe_rows(
        db,
        "SELECT agent_status, COUNT(*) AS c FROM agents GROUP BY agent_status ORDER BY c DESC",
    )
    by_status = [{"status": r[0], "count": int(r[1])} for r in dist]
    total = sum(x["count"] for x in by_status)
    active = sum(x["count"] for x in by_status if (x["status"] or "") in _ACTIVE_STATUSES)
    return {"total": total, "active": active, "by_status": by_status}


def _events_section(db, limit: int) -> dict:
    rows = _safe_rows(
        db,
        "SELECT target, event_type, processed_at, created_at "
        "FROM platform_external_events ORDER BY created_at DESC, id DESC LIMIT :lim",
        {"lim": limit},
    )
    recent = [
        {
            "target": r[0],
            "event_type": r[1],
            "processed": r[2] is not None,
            "created_at": str(r[3]) if r[3] is not None else None,
        }
        for r in rows
    ]
    tot = _safe_rows(
        db,
        "SELECT COUNT(*) AS t, SUM(CASE WHEN processed_at IS NOT NULL THEN 1 ELSE 0 END) AS p "
        "FROM platform_external_events",
    )
    total = int(tot[0][0]) if tot else 0
    processed = int(tot[0][1] or 0) if tot else 0
    by_type_rows = _safe_rows(
        db,
        "SELECT event_type, COUNT(*) AS c FROM platform_external_events "
        "GROUP BY event_type ORDER BY c DESC LIMIT 10",
    )
    by_type = [{"event_type": r[0], "count": int(r[1])} for r in by_type_rows]
    return {
        "summary": {"total": total, "processed": processed},
        "by_type": by_type,
        "recent": recent,
    }


def _poi_section(db) -> dict:
    """PoI-eligible tasks = distinct task_uid of PASSED verdicts. Platform-side
    derivation of what FEEDS compass PoI — NOT a read of compass's ledger (G-turf)."""
    rows = _safe_rows(
        db,
        "SELECT DISTINCT task_uid FROM fde_verdicts WHERE overall_pass ORDER BY task_uid",
    )
    tasks = [r[0] for r in rows]
    return {"poi_eligible": len(tasks), "eligible_tasks": tasks}


def _flywheel_section(db, limit: int) -> dict:
    """RSI 飞轮 · 第3类确定性闭环 track.

    把 verdict 按 source 分轨并单列**确定性 RSI track**(source='compass/bench_eval'·
    consumer produce → compass bench_eval 机器判 reward → settle → PoI). 与第1/2类
    soul QC(人工亲写题的 checklist judge)区分: 第3类是飞轮自转的燃料轨, 口径不同.
    """
    by_src = _safe_rows(
        db,
        "SELECT source, COUNT(*) AS c, SUM(CASE WHEN overall_pass THEN 1 ELSE 0 END) AS p "
        "FROM fde_verdicts GROUP BY source ORDER BY c DESC",
    )
    by_source = [{"source": r[0], "total": int(r[1]), "passed": int(r[2] or 0)} for r in by_src]
    det = next((s for s in by_source if s["source"] == _RSI_DETERMINISTIC_SOURCE),
               {"total": 0, "passed": 0})
    recent_rows = _safe_rows(
        db,
        "SELECT task_uid, overall_pass, score, created_at FROM fde_verdicts "
        "WHERE source = :s ORDER BY created_at DESC, id DESC LIMIT :lim",
        {"s": _RSI_DETERMINISTIC_SOURCE, "lim": limit},
    )
    recent = [
        {"task_uid": r[0], "overall_pass": bool(r[1]),
         "score": float(r[2]) if r[2] is not None else None,
         "created_at": str(r[3]) if r[3] is not None else None}
        for r in recent_rows
    ]
    return {
        "deterministic": {"total": det.get("total", 0), "passed": det.get("passed", 0),
                          "recent": recent},
        "by_source": by_source,
    }


def _fde_business_section(db, limit: int) -> dict:
    """FDE 人工业务环 track · 第1/2类专家题+教案(派活→QC→交付→结算).

    与飞轮自动轨(source=compass/bench_eval·机器判)区分:这是人类专家亲写、
    soul/feishu-expert 人工 QC 的业务环(charter §1 第1/2类)。交付+结算(应付=
    单价×工时)落飞书 RGDK 派活表 + Dx2qb 结算表(DB 不存金额·只存 QC verdict)。
    """
    rows = _safe_rows(
        db,
        "SELECT task_uid, source, overall_pass, score, created_at FROM fde_verdicts "
        "WHERE source IN ('soul','feishu-expert') "
        "AND task_uid NOT LIKE 'my_test%' AND task_uid NOT LIKE 'test_%' "
        "ORDER BY created_at DESC, id DESC LIMIT :lim",
        {"lim": limit},
    )
    recent = [
        {"task_uid": r[0], "source": r[1], "overall_pass": bool(r[2]),
         "score": float(r[3]) if r[3] is not None else None,
         "created_at": str(r[4]) if r[4] is not None else None}
        for r in rows
    ]
    tot = _safe_rows(
        db,
        "SELECT COUNT(*) AS t, SUM(CASE WHEN overall_pass THEN 1 ELSE 0 END) AS p "
        "FROM fde_verdicts WHERE source IN ('soul','feishu-expert') "
        "AND task_uid NOT LIKE 'my_test%' AND task_uid NOT LIKE 'test_%'",
    )
    total = int(tot[0][0]) if tot else 0
    passed = int(tot[0][1] or 0) if tot else 0
    return {"total": total, "passed": passed, "recent": recent}


@router.get("")
def rsi_fde_view(limit: int = Query(20, ge=1, le=100), db=Depends(get_db)):
    """One read-only snapshot of the RSI+FDE control plane. Fail-soft per section."""
    return _ok({
        "verdicts": _verdicts_section(db, limit),
        "flywheel": _flywheel_section(db, limit),
        "fde_business": _fde_business_section(db, limit),
        "agents": _agents_section(db),
        "events": _events_section(db, limit),
        "poi": _poi_section(db),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/dashboard", response_class=HTMLResponse)
def rsi_fde_dashboard():
    """Self-contained HTML 看板 — fetches the JSON view above and renders 3 panels
    (FDE verdicts / agents / events) so a user OPENS it and SEES the living system."""
    return HTMLResponse(content=_DASHBOARD_HTML)


_DASHBOARD_HTML = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Nautilus · RSI+FDE 控制面</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; font:15px/1.5 -apple-system,Segoe UI,Roboto,'Microsoft YaHei',sans-serif;
         background:#0d1117; color:#e6edf3; padding:24px; }
  h1 { font-size:22px; margin:0 0 4px; }
  .sub { color:#7d8590; font-size:13px; margin-bottom:20px; }
  .grid { display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); }
  .card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:16px; }
  .card h2 { font-size:14px; margin:0 0 12px; color:#7d8590; text-transform:uppercase; letter-spacing:.5px; }
  .stat { display:flex; align-items:baseline; gap:8px; margin-bottom:10px; }
  .stat .n { font-size:30px; font-weight:700; }
  .stat .l { color:#7d8590; font-size:13px; }
  .ok { color:#3fb950; } .bad { color:#f85149; } .dim { color:#7d8590; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  td,th { text-align:left; padding:5px 6px; border-bottom:1px solid #21262d; }
  th { color:#7d8590; font-weight:500; }
  .pill { display:inline-block; padding:1px 7px; border-radius:10px; font-size:11px; }
  .pill.pass { background:#1f3b25; color:#3fb950; } .pill.fail { background:#3b1f1f; color:#f85149; }
  .bar { height:6px; background:#21262d; border-radius:3px; overflow:hidden; margin-top:4px; }
  .bar>i { display:block; height:100%; background:#3fb950; }
  .err { color:#f85149; padding:12px; }
  footer { color:#7d8590; font-size:12px; margin-top:20px; }
</style>
</head>
<body>
<h1>🐚 Nautilus · RSI+FDE 控制面</h1>
<div class="sub" id="sub">加载中…</div>
<div class="grid" id="grid"></div>
<footer>VIEW 层 · 只读 · 数据源 <code>/api/platform/rsi-fde</code> · 外部 FDE verdict = 唯一逃离自指经济的 fitness</footer>
<script>
const esc = s => String(s==null?'':s).replace(/[&<>]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
async function load() {
  const grid = document.getElementById('grid'), sub = document.getElementById('sub');
  try {
    const res = await fetch('/api/platform/rsi-fde?limit=20');
    const body = await res.json();
    if (!body.success) throw new Error(body.error || 'view error');
    const d = body.data;
    sub.textContent = '快照 ' + (d.generated_at||'').replace('T',' ').slice(0,19) + ' UTC';

    // ── FDE Verdicts ──
    const v = d.verdicts, vs = v.summary;
    const vrows = v.recent.map(x =>
      `<tr><td>${esc(x.task_uid)}</td><td>${esc(x.source)}</td>`+
      `<td><span class="pill ${x.overall_pass?'pass':'fail'}">${x.overall_pass?'PASS':'FAIL'}</span></td>`+
      `<td class="dim">${x.score==null?'–':(x.score*100).toFixed(0)+'%'}</td></tr>`).join('');
    const fdeCard =
      `<div class="card"><h2>FDE Verdicts · 外部买方验收</h2>`+
      `<div class="stat"><span class="n ok">${vs.passed}</span><span class="l">/ ${vs.total} 通过</span>`+
      `<span class="l">· 通过率 ${(vs.pass_rate*100).toFixed(0)}%</span></div>`+
      `<div class="bar"><i style="width:${(vs.pass_rate*100).toFixed(0)}%"></i></div>`+
      `<table><thead><tr><th>任务</th><th>来源</th><th>判定</th><th>分</th></tr></thead><tbody>${vrows||'<tr><td colspan=4 class=dim>暂无</td></tr>'}</tbody></table></div>`;

    // ── Agents ──
    const a = d.agents;
    const arows = a.by_status.map(x =>
      `<tr><td>${esc(x.status)}</td><td class="dim">${x.count}</td></tr>`).join('');
    const agentCard =
      `<div class="card"><h2>Agents · 编队</h2>`+
      `<div class="stat"><span class="n ${a.active>0?'ok':'dim'}">${a.active}</span><span class="l">活跃 / ${a.total} 总</span></div>`+
      `<table><thead><tr><th>状态</th><th>数</th></tr></thead><tbody>${arows||'<tr><td colspan=2 class=dim>暂无</td></tr>'}</tbody></table></div>`;

    // ── Events ──
    const e = d.events, es = e.summary;
    const etrows = e.by_type.map(x =>
      `<tr><td>${esc(x.event_type)}</td><td class="dim">${x.count}</td></tr>`).join('');
    const eventCard =
      `<div class="card"><h2>事件流 · platform_external_events</h2>`+
      `<div class="stat"><span class="n">${es.total}</span><span class="l">事件 · ${es.processed} 已处理</span></div>`+
      `<table><thead><tr><th>类型</th><th>数</th></tr></thead><tbody>${etrows||'<tr><td colspan=2 class=dim>暂无</td></tr>'}</tbody></table></div>`;

    // ── RSI 飞轮 · 第3类确定性闭环 ──
    const fw = d.flywheel || {deterministic:{total:0,passed:0,recent:[]}, by_source:[]};
    const det = fw.deterministic;
    const fwRows = (det.recent||[]).map(x =>
      `<tr><td>${esc(x.task_uid)}</td>`+
      `<td><span class="pill ${x.overall_pass?'pass':'fail'}">${x.overall_pass?'reward 1.0':'reward 0'}</span></td>`+
      `<td class="dim">${x.score==null?'–':(x.score*100).toFixed(0)+'%'}</td></tr>`).join('');
    const srcRows = (fw.by_source||[]).map(x =>
      `<tr><td>${esc(x.source)}</td><td class="dim">${x.passed}/${x.total} 过</td></tr>`).join('');
    const flywheelCard =
      `<div class="card"><h2>🔁 RSI 飞轮 · 第3类确定性闭环</h2>`+
      `<div class="stat"><span class="n ok">${det.passed}</span><span class="l">/ ${det.total} 题确定性通过</span></div>`+
      `<div class="dim" style="font-size:11px;margin-bottom:8px">mint → claim → produce → <b>bench_eval 机器判(非 LLM)</b> → settle → PoI · source=compass/bench_eval</div>`+
      `<table><thead><tr><th>燃料题</th><th>reward</th><th>分</th></tr></thead><tbody>${fwRows||'<tr><td colspan=3 class=dim>暂无确定性 verdict</td></tr>'}</tbody></table>`+
      `<div class="dim" style="margin-top:10px;font-size:11px">分轨(source):</div>`+
      `<table><tbody>${srcRows||'<tr><td colspan=2 class=dim>暂无</td></tr>'}</tbody></table></div>`;

    // ── FDE 人工业务环 · 第1/2类专家题+教案 ──
    const fb = d.fde_business || {total:0, passed:0, recent:[]};
    const fbRows = (fb.recent||[]).map(x =>
      `<tr><td>${esc(x.task_uid)}</td><td class="dim">${esc(x.source)}</td>`+
      `<td><span class="pill ${x.overall_pass?'pass':'fail'}">${x.overall_pass?'QC过':'打回'}</span></td>`+
      `<td class="dim">${x.score==null?'–':(x.score*100).toFixed(0)+'%'}</td></tr>`).join('');
    const fdeBizCard =
      `<div class="card"><h2>🧑‍🔬 FDE 人工业务环 · 第1/2类专家题+教案</h2>`+
      `<div class="stat"><span class="n ok">${fb.passed}</span><span class="l">/ ${fb.total} 道人工 QC 通过</span></div>`+
      `<div class="dim" style="font-size:11px;margin-bottom:8px">专家亲写 → 派活 → <b>人工 QC(soul/feishu-expert)</b> → 交付 → 结算(应付=单价×工时)· 全流程在飞书 RGDK + Dx2qb</div>`+
      `<table><thead><tr><th>任务</th><th>QC 来源</th><th>判定</th><th>分</th></tr></thead><tbody>${fbRows||'<tr><td colspan=4 class=dim>暂无</td></tr>'}</tbody></table>`+
      `<div class="dim" style="margin-top:10px;font-size:11px">↔ 与飞轮自动轨(机器判·第3类)共享同一 verdict-bus · 结算应付真数字见 Dx2qb 结算表</div></div>`;

    // ── PoI ──
    const p = d.poi;
    const poiCard =
      `<div class="card"><h2>PoI 可计入 · 平台侧推导</h2>`+
      `<div class="stat"><span class="n ok">${p.poi_eligible}</span><span class="l">题通过 → 可计 PoI</span></div>`+
      `<div class="dim">${p.eligible_tasks.map(esc).join(' · ')||'暂无'}</div>`+
      `<div class="dim" style="margin-top:8px;font-size:11px">来源 = 通过的 FDE verdict(不读 compass 内部账本)</div></div>`;

    grid.innerHTML = flywheelCard + fdeBizCard + fdeCard + agentCard + eventCard + poiCard;
  } catch (err) {
    sub.innerHTML = '<span class="err">加载失败：'+esc(err.message)+'</span>';
  }
}
load();
</script>
</body>
</html>"""
