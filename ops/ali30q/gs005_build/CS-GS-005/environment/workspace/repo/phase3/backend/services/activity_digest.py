"""Daily activity digest (W2.2 可感知) · 成绩, not pain.

Builds a markdown summary of what the platform SHIPPED and what passed FDE QC —
from engine_cycle_outcomes (ship activity) + fde_verdicts (external acceptance).
The existing enterprise-wechat push surfaced pain points; this reports
achievements instead (and is consumed by the scheduler in W2.3).

Read-only · fail-soft per table · does NOT read pending_nau_rewards/votes.
"""
from __future__ import annotations

import logging

from sqlalchemy import text

logger = logging.getLogger(__name__)


def _scalar(db, sql: str, params: dict | None = None) -> int:
    try:
        row = db.execute(text(sql), params or {}).fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as exc:  # noqa: BLE001 — fail-soft · missing table → 0
        try:
            db.rollback()
        except Exception:
            pass
        logger.debug("digest query skipped: %s", str(exc)[:120])
        return 0


def _rows(db, sql: str, params: dict | None = None) -> list:
    try:
        return db.execute(text(sql), params or {}).fetchall()
    except Exception:  # noqa: BLE001
        try:
            db.rollback()
        except Exception:
            pass
        return []


def build_daily_activity_digest(db) -> str:
    """Return a 成绩-focused markdown digest of recent platform activity."""
    cycles_total = _scalar(db, "SELECT COUNT(*) FROM engine_cycle_outcomes")
    cycles_success = _scalar(
        db, "SELECT COUNT(*) FROM engine_cycle_outcomes WHERE ship_status = 'success'"
    )
    verdicts_total = _scalar(db, "SELECT COUNT(*) FROM fde_verdicts")
    verdicts_passed = _scalar(
        db, "SELECT COUNT(*) FROM fde_verdicts WHERE overall_pass IN (1, true)"
    )
    recent_verdicts = _rows(
        db,
        "SELECT task_uid, source, score FROM fde_verdicts "
        "WHERE overall_pass IN (1, true) ORDER BY created_at DESC LIMIT 5",
    )

    lines = [
        "📊 Nautilus 平台日报 · 成绩",
        "",
        f"🚢 Soul 引擎: 出 {cycles_total} 个 cycle (成功 {cycles_success} · draft PR)",
        f"✅ FDE 验收: {verdicts_passed}/{verdicts_total} 条 verdict 过 QC",
    ]
    if recent_verdicts:
        passed_list = " · ".join(
            f"{r[0]}({r[1]} {round(float(r[2]) * 100)}%)" for r in recent_verdicts
        )
        lines.append(f"   近期过 QC: {passed_list}")
    lines.append(f"📦 本期 open draft PR: {cycles_success} 个 (人工审核中)")
    return "\n".join(lines)
