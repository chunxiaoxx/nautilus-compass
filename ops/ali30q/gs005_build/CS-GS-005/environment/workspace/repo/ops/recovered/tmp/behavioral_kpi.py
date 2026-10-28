# -*- coding: utf-8 -*-
"""行为基准周报(L2/L3 探针落地·2026-10-01·用户定调"有活动无任务=没给真目标"的量化器)。
考生=六体生产 agent(按 plane 分组);考卷=生产 KPI(接率/拒率/结算/活性)——非 prompt 卷。
数据源=平台 PG(经 15432 隧道);判读:数值非审判,供周会一眼定位。
用法:python tools/org_lib/behavioral_kpi.py [--week 7]  → vtf/_behavioral_kpi_<date>.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import urllib.parse
import urllib.request

DSN_ENV = "V5_POSTGRES_DSN"
DEFAULT_DSN = "postgresql://nautilus_user@127.0.0.1:15432/nautilus_production"


def q(sql: str, params: list | None = None) -> list[dict]:
    """经 cloud psql(15432 隧道源头;本机无 psycopg 故走 ssh)。"""
    import csv
    import io
    import subprocess
    safe = sql  # 单引号在远端双引号包裹下为字面量(手动实测);%s 已由 render 替换
    cmd = ["ssh", "-o", "ConnectTimeout=15", "cloud",
           f'sudo -u postgres psql -d nautilus_production -A -F"|" --no-align -c "{safe}"']
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    lines = [l for l in out.splitlines() if l and not l.startswith("(")]
    if not lines:
        return []
    header = lines[0].split("|")
    return [dict(zip(header, l.split("|"))) for l in lines[1:]]


QUERIES = {
    "提案通道拒率(7d,按提出者)": """
        SELECT proposing_agent, count(*) AS n,
               count(*) FILTER (WHERE status='rejected') AS rejected,
               count(*) FILTER (WHERE status IN ('approved','auto_approved')) AS approved
        FROM platform_proposals
        WHERE created_at > NOW() - INTERVAL '%s days'
        GROUP BY 1 ORDER BY n DESC LIMIT 8""",
    "bounty 结算(7d,按状态)": """
        SELECT status, count(*) AS n FROM platform_bounties
        WHERE posted_at > NOW() - INTERVAL '%s days' GROUP BY 1 ORDER BY n DESC""",
    "verdict 增量(7d,按天)": """
        SELECT date_trunc('day', created_at)::date AS day, count(*) AS verdicts
        FROM fde_verdicts WHERE created_at > NOW() - INTERVAL '%s days'
        GROUP BY 1 ORDER BY 1""",
    "生产 agent 活性(plane!=lab/retired)": """
        SELECT a.name, a.plane,
               CASE WHEN a.last_heartbeat > NOW() - INTERVAL '1 hour' THEN 'fresh'
                    WHEN a.last_heartbeat > NOW() - INTERVAL '2 days' THEN 'stale-2d'
                    ELSE 'stale' END AS hb
        FROM platform_agents a
        WHERE a.plane IN ('prod','prod-observe','prod-starved','repairing')
        UNION
        SELECT a.name, a.plane,
               CASE WHEN a.last_heartbeat > NOW() - INTERVAL '1 hour' THEN 'fresh'
                    WHEN a.last_heartbeat > NOW() - INTERVAL '2 days' THEN 'stale-2d'
                    ELSE 'stale' END AS hb
        FROM agents a
        WHERE a.plane IN ('prod','prod-observe','prod-starved','repairing')
        ORDER BY hb, name LIMIT 12""",
}


def render(week_days: int) -> str:
    lines = [f"# 行为基准周报 · {dt.date.today().isoformat()}(近 {week_days} 天)", ""]
    for title, sql in QUERIES.items():
        rows = q(sql.replace("%s", str(week_days)))
        lines += [f"## {title}", ""]
        if not rows:
            lines += ["(无数据)", ""]
            continue
        keys = list(rows[0].keys())
        lines.append("| " + " | ".join(keys) + " |")
        lines.append("|" + "---|" * len(keys))
        for r in rows:
            lines.append("| " + " | ".join(str(r.get(k, "")) for k in keys) + " |")
        lines.append("")
    lines += ["---", "判读注:数值非审判——拒率突变/结算归零/活性 stale 三项是重点信号,定位到 agent 后转六体分诊流程。"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, default=7)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or f"vtf/_behavioral_kpi_{dt.date.today().isoformat()}.md"
    text = render(a.week)
    from pathlib import Path
    Path(out).write_text(text, encoding="utf-8")
    print(out)
    print(text[:600])


if __name__ == "__main__":
    main()
