#!/usr/bin/env python3
"""behavioral_drift_cron · Layer 5 of cheeky-swinging-snail
Compute 4 behavioral axes per active agent from agent_tool_calls (24h + 7d window),
write to platform_agents.metadata.behavioral_drift.

Axes (all in [0,1] unless noted):
  - action_diversity   = distinct(tool_name) / total_calls (24h) · higher = more varied
  - success_trend      = recent50_success_rate − hist7d_success_rate (in [-1,1]) · positive = improving
  - stagnation_score   = max(tool_share) over 24h · higher = more repetitive
  - self_modify_rate   = self_modify_calls / total_calls (24h)

Usage: python3 behavioral_drift_cron.py
Designed to run daily via systemd timer or cron.
"""
import json
import os
import sys
from datetime import datetime
from collections import Counter

import psycopg2
import psycopg2.extras

DSN = os.environ.get("DATABASE_URL") or \
    "postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production"

# Agents to score · only those with heartbeat in last 7d
AGENT_FILTER_SQL = """
SELECT agent_id FROM platform_agents
WHERE survival_tier <> 'dead'
  AND last_heartbeat > NOW() - INTERVAL '7 days'
ORDER BY agent_id
"""


def compute_axes(cu, agent_id: str) -> dict:
    # 24h window stats
    cu.execute(
        """SELECT tool_name, success FROM agent_tool_calls
           WHERE agent_id=%s AND ts > NOW() - INTERVAL '24 hours'""",
        (agent_id,),
    )
    rows_24h = cu.fetchall()
    total_24h = len(rows_24h)

    if total_24h == 0:
        return {
            "action_diversity": 0.0,
            "success_trend": 0.0,
            "stagnation_score": 0.0,
            "self_modify_rate": 0.0,
            "sample_size_24h": 0,
            "note": "no_calls_24h",
        }

    tool_counter = Counter(r["tool_name"] for r in rows_24h)
    distinct_tools = len(tool_counter)
    action_diversity = distinct_tools / total_24h
    most_common_share = tool_counter.most_common(1)[0][1] / total_24h
    self_modify_calls = sum(c for t, c in tool_counter.items() if "self_modify" in t.lower())
    self_modify_rate = self_modify_calls / total_24h

    # success trend = recent50 vs 7d historical (excluding the most-recent 50)
    cu.execute(
        """SELECT success FROM agent_tool_calls
           WHERE agent_id=%s AND ts > NOW() - INTERVAL '24 hours'
           ORDER BY ts DESC LIMIT 50""",
        (agent_id,),
    )
    recent = [r["success"] for r in cu.fetchall()]
    recent_rate = sum(1 for s in recent if s) / len(recent) if recent else 0.0

    cu.execute(
        """SELECT COUNT(*) FILTER (WHERE success) AS ok, COUNT(*) AS tot
           FROM agent_tool_calls
           WHERE agent_id=%s
             AND ts > NOW() - INTERVAL '7 days'
             AND ts < NOW() - INTERVAL '24 hours'""",
        (agent_id,),
    )
    h = cu.fetchone()
    hist_rate = (h["ok"] / h["tot"]) if h and h["tot"] else recent_rate
    success_trend = round(recent_rate - hist_rate, 4)

    return {
        "action_diversity": round(action_diversity, 4),
        "success_trend": success_trend,
        "stagnation_score": round(most_common_share, 4),
        "self_modify_rate": round(self_modify_rate, 4),
        "sample_size_24h": total_24h,
        "distinct_tools_24h": distinct_tools,
        "top_tool_24h": tool_counter.most_common(1)[0][0],
    }


def main() -> int:
    written = 0
    skipped = 0
    errs = 0
    with psycopg2.connect(DSN, connect_timeout=10) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cu:
            cu.execute(AGENT_FILTER_SQL)
            agents = [r["agent_id"] for r in cu.fetchall()]

            now_iso = datetime.now().isoformat()
            for agent_id in agents:
                try:
                    axes = compute_axes(cu, agent_id)
                    axes["updated_at"] = now_iso
                    cu.execute(
                        """UPDATE platform_agents
                           SET metadata = jsonb_set(
                                 COALESCE(metadata, '{}'::jsonb),
                                 '{behavioral_drift}', %s::jsonb, true)
                           WHERE agent_id=%s""",
                        (json.dumps(axes), agent_id),
                    )
                    if axes.get("sample_size_24h", 0) == 0:
                        skipped += 1
                    else:
                        written += 1
                    print(f"[bdrift] {agent_id} · "
                          f"div={axes.get('action_diversity')} "
                          f"trend={axes.get('success_trend')} "
                          f"stag={axes.get('stagnation_score')} "
                          f"selfmod={axes.get('self_modify_rate')} "
                          f"n={axes.get('sample_size_24h')}",
                          flush=True)
                except Exception as e:
                    errs += 1
                    print(f"[bdrift err] {agent_id}: {type(e).__name__}: {e}", flush=True)
            conn.commit()
    print(f"[bdrift] done · agents={len(agents)} written={written} "
          f"skipped_no_calls={skipped} errs={errs}", flush=True)
    return 0 if errs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
