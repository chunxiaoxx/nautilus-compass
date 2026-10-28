"""Append /api/agents/unified endpoints to phase3 agents.py."""
from __future__ import annotations
import ast
import pathlib
import sys

P = pathlib.Path("/home/ubuntu/nautilus-mvp/phase3/backend/api/agents.py")

APPEND = '''


# ---------------------------------------------------------------------
# 2026-05-06 schema fusion · /api/agents/unified · returns 326 agents
# (phase3 316 + v5 platform_agents 10) via unified_agents view.
# Loose dict response · no AgentResponse strict schema (varchar agent_id ok).
# ---------------------------------------------------------------------

from sqlalchemy import text as _sql_text


@router.get("/unified")
async def list_agents_unified(
    skip: int = Query(0, ge=0),
    limit: int = Query(326, ge=1, le=500),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    where = ""
    params = {"limit": limit, "offset": skip}
    if source in ("phase3", "v5"):
        where = "WHERE source = :src"
        params["src"] = source
    sql = (
        "SELECT source, agent_id, name, reputation, last_heartbeat, earnings, tier "
        "FROM unified_agents "
        + where +
        " ORDER BY reputation DESC NULLS LAST, last_heartbeat DESC NULLS LAST "
        "LIMIT :limit OFFSET :offset"
    )
    rows = db.execute(_sql_text(sql), params).fetchall()
    return [
        {
            "source": r[0],
            "agent_id": r[1],
            "name": r[2],
            "reputation": int(r[3] or 0),
            "last_heartbeat": r[4].isoformat() if r[4] else None,
            "earnings": int(r[5] or 0),
            "tier": r[6] or "unknown",
        }
        for r in rows
    ]


@router.get("/unified/stats")
async def unified_agents_stats(db: Session = Depends(get_db)):
    rows = db.execute(
        _sql_text("SELECT source, count(*) FROM unified_agents GROUP BY source")
    ).fetchall()
    return {
        "by_source": {r[0]: int(r[1]) for r in rows},
        "total": sum(int(r[1]) for r in rows),
    }
'''


def main():
    src = P.read_text()
    if "unified_agents" in src:
        print("already patched · skip")
        return
    new_src = src + APPEND
    try:
        ast.parse(new_src)
    except SyntaxError as e:
        print(f"FAIL ast: {e}", file=sys.stderr)
        sys.exit(2)
    P.write_text(new_src)
    print(f"ok · agents.py · {len(new_src)} bytes")


if __name__ == "__main__":
    main()
