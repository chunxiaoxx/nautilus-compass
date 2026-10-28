# -*- coding: utf-8 -*-
"""组织订单生命周期编排器 v0——闭环兑现的载体。

把散通的零件(mailbox 任务/回函/验收/capability)串成一条可审计链:
  DISPATCHED → CLAIMED → DELIVERED → ACCEPTED → CLOSED (+OVERDUE 叠加)
单一数据源=org_mailbox(task_meta 非空=任务单);阶段从信号推导,零新表。

跑法(云): cd backend && python3 ops/order_lifecycle.py
输出: docs/evidence/org-os/pilot/order_ledger_YYYYMMDD.md(在途/逾期/已闭三节)
"""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

_COMMIT = re.compile(r"\b[0-9a-f]{7,40}\b")


def _has_commit(text: str) -> bool:
    return bool(_COMMIT.search(text or ""))


def derive_stage(task: dict, replies: list[dict], accepted: bool,
                 cap_after: bool = False, acceptance_letters: list | None = None,
                 void_letters: list | None = None) -> str:
    """纯函数:由任务行+回函链+验收/记账/销案信号推阶段。

    replies   : 收件框发回、trace 同根且晚于任务单的函
    accepted  : 存在验收函(平台发出,标题含"验收")
    cap_after : 该 agent 在投单后有 capability 记账(交付被验收记账)
    void_letters : 销案函(标题含"销案/作废")
    """
    if void_letters:
        return "CLOSED"
    if cap_after:
        return "CLOSED"
    if accepted or acceptance_letters:
        return "ACCEPTED"
    if any(_has_commit(r.get("title", "") + (r.get("body") or "")[:300]) for r in replies):
        return "DELIVERED"
    if task.get("ack_at") or replies:
        return "CLAIMED"
    return "DISPATCHED"


def is_overdue(task: dict, now: str, stage: str) -> bool:
    return stage not in ("CLOSED",) and str(now) > str(task["deadline"])


def build_ledger(rows: list[dict], caps: list[dict], now: str) -> dict:
    """rows=mailbox 全函(含 task);caps=[{agent,at}]。返回三节台账。"""
    by_agent_time = {}
    for c in caps:
        by_agent_time.setdefault(c["agent"], []).append(c["at"])
    tasks = [r for r in rows if r.get("task_meta")]
    letters = [r for r in rows]
    out = {"open": [], "overdue": [], "closed": [], "pending_accept": []}
    for t in tasks:
        root = t["trace_id"].rsplit("-", 1)[0] if "-reply" in t["trace_id"] else t["trace_id"]
        replies = [r for r in letters
                   if r["from_agent"] == t["to_agent"] and r["id"] > t["id"]
                   and (r["trace_id"].startswith(t["trace_id"])
                        or t["trace_id"].startswith(r["trace_id"].rsplit("-reply", 1)[0])
                        or root in r["trace_id"])]
        acc = [r for r in letters if r["from_agent"] == "platform" and r["id"] > t["id"]
               and "验收" in r["title"] and t["trace_id"].split("-")[0] in r["trace_id"]]
        void = [r for r in letters if r["id"] > t["id"] and ("销案" in r["title"] or "作废" in r["title"])
                and t["trace_id"][:8] in r.get("body", "")]
        cap_after = any(str(at) > str(t["created_at"] or "") for at in by_agent_time.get(t["to_agent"], []))
        stage = derive_stage(t, replies, bool(acc), cap_after, acc, void)
        rec = dict(id=t["id"], trace=t["trace_id"], to=t["to_agent"],
                   title=t["title"][:60], deadline=str(t["deadline"]), stage=stage)
        (out["closed"] if stage == "CLOSED" else
         out["open"] if not is_overdue(t, now, stage) else out["overdue"]).append(rec)
    return out


def main() -> int:
    sys.path.insert(0, ".")
    import models.agent_survival  # noqa: F401
    from models.org_mailbox import OrgMailbox
    from utils.database import SessionLocal

    s = SessionLocal()
    rows = []
    for r in s.query(OrgMailbox).order_by(OrgMailbox.id).all():
        rows.append(dict(id=r.id, from_agent=r.from_agent, to_agent=r.to_agent,
                         trace_id=r.trace_id or "", title=r.title or "", body=r.body or "",
                         deadline=r.deadline, ack_at=r.ack_at, task_meta=r.task_meta,
                         created_at=r.created_at))
    caps = []
    try:
        from sqlalchemy import text
        for a, at in s.execute(text(
                "SELECT agent_id,last_at FROM platform_agent_capability_stats")):
            caps.append(dict(agent=a, at=str(at)))
    except Exception:
        pass
    # DMAS task ledger (2026-09-10 revival): verdict-sourced production.tasks rows.
    task_rows = []
    try:
        from sqlalchemy import text
        for r in s.execute(text(
                "SELECT task_id, publisher, status, agent, reward, created_at "
                "FROM tasks WHERE task_id LIKE 'verdict-%' "
                "ORDER BY id DESC LIMIT 20")):
            task_rows.append(dict(task_id=r[0], publisher=r[1], status=r[2],
                                  agent=r[3], reward=r[4], created_at=str(r[5])))
    except Exception:
        pass
    s.close()

    now = f"{datetime.utcnow():%Y-%m-%d %H:%M:%S}"
    led = build_ledger(rows, caps, now)
    L = [f"# 组织订单台账 {now} (order_lifecycle v0)", ""]
    for sec, key in (("在途", "open"), ("逾期", "overdue"), ("已闭", "closed")):
        L.append(f"## {sec} ({len(led[key])})")
        for r in led[key]:
            L.append(f"- #{r['id']} [{r['stage']}] →{r['to']} {r['title']} · dl {r['deadline'][:16]}")
        L.append("")
    L += ["## 兑现链口诀",
          "- 每单五件套(类型/验收判据/交付格式/SLA/消费者)强制,缺一不发;",
          "- 交付回函必带 commit hash(编排器据此判 DELIVERED);",
          "- 验收=平台独立复算(不信自报);兑现=capability 记账(读回验证);",
          "- 销案必留函(VOID 也要有据)。"]
    L += ["", f"## tasks 台账 · verdict 来源 ({len(task_rows)} 行 · 9/10 DMAS 复活)", ""]
    if not task_rows:
        L.append("- (暂无 verdict 来源行)")
    for r in task_rows:
        L.append(f"- {r['task_id']} | {r['publisher']} | {r['status']} | "
                 f"agent={r['agent']} | reward={r['reward']} | {r['created_at'][:16]}")
    out = Path("docs/evidence/org-os/pilot") / f"order_ledger_{datetime.utcnow():%Y%m%d}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"written {out}")
    print("\n".join(L[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
