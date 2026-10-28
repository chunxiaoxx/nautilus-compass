#!/usr/bin/env python3
"""drift_threshold_alert · Layer 5 patch
Read platform_agents.metadata.behavioral_drift · for any agent breaching thresholds,
write a one-shot inbox message (dedup 24h via metadata.last_alert_at).

Thresholds (any one trigger):
  - stagnation_score > 0.6     (top tool >60% of 24h calls)
  - success_trend < -0.05      (recent success rate dropping >5pp)
  - action_diversity < 0.02 AND sample_size_24h >= 50 (high call volume but tiny tool variety)

Skip if behavioral_drift.last_alert_at is within 24h (dedup).
Designed to run every 6h via systemd timer.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import psycopg2
import psycopg2.extras

DSN = os.environ.get("DATABASE_URL") or \
    "postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production"

ALERT_FROM = "compass-bdrift-watcher"
DEDUP_HOURS = 24

THRESH_STAG = 0.6
THRESH_TREND = -0.05
THRESH_DIV = 0.02
DIV_MIN_N = 50


def reasons(bd: dict) -> list[str]:
    out = []
    if bd.get("stagnation_score", 0) > THRESH_STAG:
        out.append(
            f"stagnation_score={bd.get('stagnation_score')} "
            f"(top_tool={bd.get('top_tool_24h')!r} dominates >60% of 24h calls)"
        )
    if bd.get("success_trend", 0) < THRESH_TREND:
        out.append(
            f"success_trend={bd.get('success_trend')} "
            f"(recent50 success rate dropping vs 7d historical)"
        )
    if (
        bd.get("action_diversity", 1) < THRESH_DIV
        and bd.get("sample_size_24h", 0) >= DIV_MIN_N
    ):
        out.append(
            f"action_diversity={bd.get('action_diversity')} "
            f"with n={bd.get('sample_size_24h')} (tiny tool variety despite high volume)"
        )
    return out


def build_message(agent_id: str, bd: dict, why: list[str]) -> str:
    lines = [
        f"behavioral_drift alert · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Your recent action pattern is showing stuck/declining signals:",
    ]
    for r in why:
        lines.append(f"  - {r}")
    lines += [
        "",
        f"raw axes: {json.dumps({k: v for k, v in bd.items() if k != 'updated_at'})}",
        "",
        "Suggestion: try varying tools, reading recent task results, or asking for a /goal",
        "decomposition. Stuck patterns can indicate a stale prompt or tool-routing bug.",
    ]
    return "\n".join(lines)


def main() -> int:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=DEDUP_HOURS)
    sent = 0
    skipped_dedup = 0
    no_alert = 0
    errs = 0

    with psycopg2.connect(DSN, connect_timeout=10) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cu:
            cu.execute(
                """SELECT agent_id,
                          metadata->'behavioral_drift' AS bd
                   FROM platform_agents
                   WHERE metadata ? 'behavioral_drift'
                     AND survival_tier <> 'dead'"""
            )
            rows = cu.fetchall()

            for r in rows:
                agent_id = r["agent_id"]
                bd = r["bd"] or {}
                if not bd or bd.get("sample_size_24h", 0) == 0:
                    no_alert += 1
                    continue
                why = reasons(bd)
                if not why:
                    no_alert += 1
                    continue
                # dedup check
                last_alert_iso = bd.get("last_alert_at")
                if last_alert_iso:
                    try:
                        last_dt = datetime.fromisoformat(last_alert_iso)
                        if last_dt.tzinfo is None:
                            last_dt = last_dt.replace(tzinfo=timezone.utc)
                        if last_dt > cutoff:
                            skipped_dedup += 1
                            print(f"[bdrift-alert] dedup skip · {agent_id} · last={last_alert_iso}",
                                  flush=True)
                            continue
                    except Exception:
                        pass

                try:
                    msg_id = f"bdrift-{uuid.uuid4().hex[:16]}"
                    content = build_message(agent_id, bd, why)
                    cu.execute(
                        """INSERT INTO platform_agent_messages
                             (message_id, from_agent, to_agent, content, msg_type, status, metadata)
                           VALUES (%s, %s, %s, %s, 'alert', 'unread', %s::jsonb)""",
                        (msg_id, ALERT_FROM, agent_id, content,
                         json.dumps({"source": "behavioral_drift_cron",
                                     "axes": bd,
                                     "reasons": why})),
                    )
                    # update last_alert_at in agent metadata
                    bd_new = dict(bd)
                    bd_new["last_alert_at"] = now.isoformat()
                    cu.execute(
                        """UPDATE platform_agents
                           SET metadata = jsonb_set(metadata, '{behavioral_drift}', %s::jsonb, true)
                           WHERE agent_id=%s""",
                        (json.dumps(bd_new), agent_id),
                    )
                    sent += 1
                    print(f"[bdrift-alert] sent {msg_id} → {agent_id} · reasons={len(why)}",
                          flush=True)
                except Exception as e:
                    errs += 1
                    print(f"[bdrift-alert err] {agent_id}: {type(e).__name__}: {e}",
                          flush=True)
            conn.commit()
    print(f"[bdrift-alert] done · scanned={len(rows)} sent={sent} dedup={skipped_dedup} "
          f"no_alert={no_alert} errs={errs}", flush=True)
    return 0 if errs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
