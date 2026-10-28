# -*- coding: utf-8 -*-
"""验收→capability 自动记账(闭环兑现最后一环自动化)。

规则:platform 发出且 title 含"验收(部分)合格"的函 → 给 to_agent 记一笔;
幂等=已处理函 id 记 ops/capability_state.json;未注册映射的框跳过并警告。
挂云 timer 30min。跑法: cd backend && python3 ops/capability_settle.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

# 确认注册过的 框名→agent_id(新增框在此登记)
AGENT_MAP = {"flywheel": "9000014", "v5": "9000002"}
STATE_PATH = Path("ops/capability_state.json")


def score_of(title: str) -> float:
    if "验收" not in title or "合格" not in title:
        return 0.0
    return 0.6 if "部分" in title else 1.0


def agent_id_of(frame: str) -> str | None:
    return AGENT_MAP.get(frame)


def pick_new_acceptances(letters: list[dict], state: dict) -> list[dict]:
    done = set(state.get("done", []))
    return [l for l in letters
            if l["id"] not in done and l["from_agent"] == "platform"
            and score_of(l["title"] or "") > 0]


def main() -> int:
    sys.path.insert(0, ".")
    import models.agent_survival  # noqa: F401
    from models.org_mailbox import OrgMailbox
    from utils.database import SessionLocal
    from sqlalchemy import text

    state = json.loads(STATE_PATH.read_text()) if STATE_PATH.exists() else {"done": []}
    s = SessionLocal()
    rows = [dict(id=r.id, from_agent=r.from_agent, to_agent=r.to_agent,
                 title=r.title or "", trace_id=r.trace_id or "",
                 created_at=str(r.created_at))
            for r in s.query(OrgMailbox).order_by(OrgMailbox.id).all()]
    s.close()

    for l in pick_new_acceptances(rows, state):
        aid = agent_id_of(l["to_agent"])
        if not aid:
            print(f"WARN skip unmapped frame: #{l['id']} → {l['to_agent']}")
            state["done"].append(l["id"])
            continue
        sk = (l["trace_id"].split("-")[0] or "org")[:24]
        sc = score_of(l["title"])
        s = SessionLocal()
        cur = s.execute(text(
            "SELECT attempts FROM platform_agent_capability_stats "
            "WHERE agent_id=:a AND task_type='org_task' AND skill_tag=:k"),
            {"a": aid, "k": sk}).fetchone()
        if cur is None:
            s.execute(text(
                "INSERT INTO platform_agent_capability_stats "
                "(agent_id,task_type,skill_tag,attempts,succeeded,total_score,last_score,"
                " last_bounty_id,last_at) VALUES (:a,'org_task',:k,1,1,:sc,:sc,:mid,now())"),
                {"a": aid, "k": sk, "sc": sc, "mid": str(l["id"])})
        else:
            s.execute(text(
                "UPDATE platform_agent_capability_stats SET attempts=attempts+1,"
                "succeeded=succeeded+1,total_score=total_score+:sc,last_score=:sc,"
                "last_bounty_id=:mid,last_at=now() WHERE agent_id=:a AND skill_tag=:k"),
                {"a": aid, "k": sk, "sc": sc, "mid": str(l["id"])})
        s.commit()
        back = s.execute(text(
            "SELECT agent_id,attempts,last_bounty_id FROM platform_agent_capability_stats"
            " WHERE agent_id=:a AND skill_tag=:k"), {"a": aid, "k": sk}).fetchone()
        s.close()
        print(f"settled #{l['id']} → {aid}/{sk} score={sc} readback={back}")
        state["done"].append(l["id"])

    state["done"] = state["done"][-500:]
    STATE_PATH.write_text(json.dumps(state), encoding="utf-8")
    print(f"{datetime.utcnow():%Y-%m-%d %H:%M} settle done, processed total={len(state['done'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
