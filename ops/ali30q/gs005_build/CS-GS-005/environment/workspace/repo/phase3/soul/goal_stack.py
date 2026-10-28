"""Soul goal stack · 3-source priority queue (P1 governance > P2 agent dispatch > P3 self-reflection).

Per docs/plans/2026-05-29-soul-recursive-self-improvement-engine-design.md Section 2.

Each _next_pX_*() returns either a goal dict (id + task spec fields) or None.
next_goal() returns (goal, source) tuple; both None when stack is fully empty.

Implementation notes:
  - P1 inlines a read-only SELECT against platform_improvement_proposals because
    services.soul_executor has no peek-only function (only execute_accepted_proposals
    which is side-effecting). DOUBLE-SHIP COORDINATION is Slice A Task A3's
    responsibility · this module is a peek only.
  - P3 delegates to soul.goal_selector.select_goal() (3-tier fallback already
    implemented · yaml > reflection > docs scrape).
"""
from __future__ import annotations
from enum import Enum
from typing import Optional


class GoalSource(str, Enum):
    P1_GOVERNANCE = "p1_governance"
    P2_AGENT_DISPATCH = "p2_agent_dispatch"
    P3_SELF_REFLECTION = "p3_self_reflection"


def _next_p1_governance() -> Optional[dict]:
    """P1 · peek the oldest accepted code-type proposal from governance queue.

    Read-only SELECT against platform_improvement_proposals. Returns None when:
      - DATABASE_URL unset (test env)
      - psycopg2 import fails
      - no rows with status='accepted'
      - any DB error (fail-open · daemon must not crash)

    DOUBLE-SHIP RISK · documented for Slice A Task A3 wiring: services.soul_executor
    runs as a separate cron (nautilus-soul-executor.timer · 10min) and also picks
    status='accepted' rows. If the L1 daemon ships this peeked proposal via its
    own engine.ship path, both processes may race on the same row. A3 must add
    coordination (e.g. mark status='executed_in_progress' on peek-and-claim).
    """
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        import psycopg2
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, proposed_change FROM platform_improvement_proposals "
                    "WHERE status = 'accepted' "
                    "ORDER BY created_at ASC LIMIT 1"
                )
                row = cur.fetchone()
    except Exception:
        return None
    if not row:
        return None
    return {
        "id": f"gov-{row[0]}",
        "proposal_id": row[0],
        "proposed_change": row[1],
    }


def _next_p2_agent_dispatch() -> Optional[dict]:
    """P2 · agent-dispatched task spec from agent_dispatch_log.

    Returns the oldest log row with ship_outcome IS NULL (i.e. pending).
    Returns None when no pending dispatch OR table missing (pre-Slice-A apply).

    Slice B followup · selects task_spec (full text) so the daemon can use it
    as the engine.ship() goal description. Pre-followup rows may have an empty
    task_spec (the column default is '') — those still surface but the daemon
    no-ops them out via ship's own empty-goal handling.
    """
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        import psycopg2
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, agent_id, task_spec, task_spec_hash, task_type "
                    "FROM agent_dispatch_log "
                    "WHERE ship_outcome IS NULL "
                    "ORDER BY created_at ASC LIMIT 1"
                )
                row = cur.fetchone()
    except Exception:
        return None
    if not row:
        return _next_p2_org_mailbox()
    return {
        "id": f"dispatch-{row[0]}",
        "agent_id": row[1],
        "task_spec": row[2] or "",
        "task_spec_hash": row[3],
        "task_type": row[4] or "code",
    }


def _next_p2_org_mailbox() -> Optional[dict]:
    """P2b · org mailbox bridge(9/19:soul 接入组织信箱,平台代管失职整改)。

    旧表 agent_dispatch_log 空/缺失时,回落读 org_mailbox 里发给 soul 的
    未读任务函(to_agent='soul', ack_at 为空),按最旧优先。
    2026-10-03 根修:撤 task_meta IS NOT NULL 门槛——平台判断类函(任命/终裁/
    征议)发函不写 task_meta,23 封实测全 NULL → soul 选择器结构性失明,每轮
    落 P3 selfimprove 且 PR 已开即 skip = 恒空轮("待答 37"五小时不动根因)。
    2026-10-05 死锁根治:task_type 默认反转 'org_task'→'discussion'——NULL meta
    函默认走回函保活路径(_run_letter_reply 不受 breaker 拦截);需 ship(动代码)
    的函必须由发函方显式标 task_meta.task_type='org_task'。旧默认下 NULL 函全进
    ship 路径,breaker 期逐封被拦 return 0,最旧优先下轮再选同一封=队列死锁
    (mailbox-2794 自指闭环实证:索要熔断根因报告的函被该熔断本身锁死)。
    返回的 goal 以 trace 前缀记来源;执行方(daemon/engine)回函时在 ack
    信箱行后由平台哨兵正常流转。"""
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        import psycopg2
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, trace_id, title, body, "
                    "COALESCE(task_meta->>'task_type', 'discussion') FROM org_mailbox "
                    "WHERE to_agent = 'soul' AND ack_at IS NULL "
                    "AND trace_id NOT LIKE 'worker-audit%%' "
                    "ORDER BY created_at ASC LIMIT 1"
                )
                row = cur.fetchone()
    except Exception:
        return None
    if not row:
        return None
    # task_type 透传原函 meta(9/20:治理裁定/征意类是回函任务,塞 patch 路径
    # 必挂 checks——524 两连败实证);2026-10-05 默认反转:NULL=回函类,daemon 按此分流
    return {
        "id": f"mailbox-{row[0]}",
        "agent_id": "platform",
        "task_spec": f"[{row[1]}] {row[2]}\n\n{row[3]}",
        "task_spec_hash": row[1],
        "task_type": row[4] or "discussion",
    }


def _next_p3_self_reflection() -> Optional[dict]:
    """P3 · existing 3-tier fallback (yaml > reflection > docs scrape).

    Delegates to soul.goal_selector.select_goal() which already implements the
    P3 sub-priority. Returns None only when all three P3 sub-sources empty.
    """
    try:
        from soul.goal_selector import select_goal
        return select_goal()
    except Exception:
        return None


def next_goal() -> tuple[Optional[dict], Optional[GoalSource]]:
    """Resolve the highest-priority goal across the 3-source stack.

    Returns (goal_dict, source_enum). Both None when no goal available
    at any priority (daemon then runs SELF-IMPROVE fallback cycle).
    """
    goal = _next_p1_governance()
    if goal is not None:
        return goal, GoalSource.P1_GOVERNANCE
    goal = _next_p2_agent_dispatch()
    if goal is not None:
        return goal, GoalSource.P2_AGENT_DISPATCH
    goal = _next_p3_self_reflection()
    if goal is not None:
        return goal, GoalSource.P3_SELF_REFLECTION
    return None, None