"""a2a review wiring · v5agent cycle 8 (HANDOFF Gap 2 + 4).

Sends engine-generated diff to V5 / V7 / Kairos via platform_agent_messages
table · polls for reply messages · aggregates approve/reject/abstain verdicts.

Sync impl (CLI subprocess context · no asyncio overhead) · accepts an injected
SQLAlchemy engine for testability. The receiving agents use their existing
a2a inbox machinery · no V5/V7/Kairos prompt changes required (anchor #7).

Wiring contract with platform_agent_messages (prod schema verified 2026-05-25):
- Outbound msg: message_id = 'engine_rev_<task_id>_<rand>' · msg_type='review_request' ·
  thread_id = 'thr-engine-review-<task_id>' (top-level column · NOT metadata)
- Reply detection: messages from target agent where in_reply_to = our message_id
  OR thread_id matches our thread (covers agents that reply without in_reply_to)
- Verdict parsing: case-insensitive substring match for 'approve' / 'reject' /
  'abstain' in reply.content · 'abstain' is the safe default

History · 2026-05-25 ship: original code used `msg_id` column name (per the SQL
migration `add_a2a_sla_enforcement.sql` line 33 comment "msg_id (not message_id)"
which was wrong about prod). Real cloud E2E caught the bug · UndefinedColumn ·
fixed to `message_id`. Schema split-brain memory cross-confirmed (the cheatsheet).
"""
from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

DEFAULT_TARGETS = ("nautilus-prime-001", "v7-telegram", "kairos")
DEFAULT_TIMEOUT_S = 30
DEFAULT_POLL_INTERVAL_S = 2


@dataclass
class ReviewOpinion:
    agent: str
    verdict: str  # "approve" | "reject" | "abstain"
    text: str = ""
    received_at: float = 0.0


@dataclass
class ReviewResult:
    task_id: str
    thread_id: str
    approve_count: int = 0
    reject_count: int = 0
    abstain_count: int = 0
    timeouts: list[str] = field(default_factory=list)
    opinions: dict[str, dict] = field(default_factory=dict)


def request_review(
    task_id: str,
    code_diff: str,
    repo_map_snippet: str = "",
    target_agents=DEFAULT_TARGETS,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    poll_interval_s: int = DEFAULT_POLL_INTERVAL_S,
    db_engine: Any = None,
) -> ReviewResult:
    """Send review request to N agents · poll for replies · aggregate verdicts.

    db_engine: SQLAlchemy Engine · if None, built from DATABASE_URL env.
    Returns ReviewResult with counts + per-agent opinions + timeout list.

    Review fix Important #1 · single-transaction batch send so N targets are
    all-or-nothing (no partial fan-out if one INSERT trips a deadlock).
    Review fix Important #2 · pass `since` timestamp into _poll_reply to bound
    stale reply pickup at 1h window.
    """
    thread_id = f"thr-engine-review-{task_id}"
    msg_template = _build_review_msg(code_diff, repo_map_snippet)

    if db_engine is None:
        db_engine = _default_engine()

    # 1. Send requests · atomic batch (one transaction, N inserts)
    send_started_at = time.time()
    msg_ids = _send_requests_batch(
        db_engine, list(target_agents), thread_id, msg_template, task_id
    )

    # 2. Poll for replies until timeout or all answered
    replies: dict[str, ReviewOpinion] = {}
    deadline = time.time() + timeout_s
    while time.time() < deadline and len(replies) < len(target_agents):
        for agent, our_mid in msg_ids.items():
            if agent in replies:
                continue
            opinion = _poll_reply(
                db_engine, agent, our_mid, thread_id, since_epoch=send_started_at
            )
            if opinion is not None:
                replies[agent] = opinion
        if len(replies) >= len(target_agents):
            break
        if poll_interval_s > 0:
            time.sleep(poll_interval_s)

    # 3. Aggregate
    timeouts = [a for a in target_agents if a not in replies]
    return ReviewResult(
        task_id=task_id,
        thread_id=thread_id,
        approve_count=sum(1 for r in replies.values() if r.verdict == "approve"),
        reject_count=sum(1 for r in replies.values() if r.verdict == "reject"),
        abstain_count=sum(1 for r in replies.values() if r.verdict == "abstain"),
        timeouts=timeouts,
        opinions={a: asdict(o) for a, o in replies.items()},
    )


# ---------- internals ----------

def _build_review_msg(code_diff: str, repo_map_snippet: str) -> str:
    return (
        "=== ENGINE REVIEW REQUEST ===\n"
        f"diff:\n{code_diff[:2000]}\n\n"
        f"repo_map:\n{repo_map_snippet[:1000]}\n\n"
        "Your review (<= 200 words):\n"
        "  - 1 critical concern (or 'none')\n"
        "  - 1 improvement suggestion\n"
        "  - approve / reject / abstain"
    )


def _send_requests_batch(
    db_engine: Any,
    agents: list[str],
    thread_id: str,
    content: str,
    task_id: str,
) -> dict[str, str]:
    """INSERT review_request for N agents in ONE transaction · return agent -> message_id map.

    Review fix Important #1 · was per-agent transaction · partial-send risk on
    deadlock. Now all N inserts atomic OR all roll back.
    """
    from sqlalchemy import text as _text
    short_tid = task_id[:20]
    msg_ids: dict[str, str] = {}
    sql = _text(
        """
        INSERT INTO platform_agent_messages
          (message_id, thread_id, from_agent, to_agent, content, msg_type,
           status, sent_at, metadata)
        VALUES
          (:m, :tid, 'nautilus_engine', :to, :c, 'review_request',
           'unread', NOW(), CAST(:meta AS jsonb))
        ON CONFLICT (message_id) DO NOTHING
        """
    )
    meta = json.dumps({"task_id": task_id, "review_request": True})
    with db_engine.begin() as conn:
        for agent in agents:
            message_id = f"engine_rev_{short_tid}_{secrets.token_hex(4)}"
            conn.execute(sql, {
                "m": message_id, "tid": thread_id,
                "to": agent, "c": content, "meta": meta,
            })
            msg_ids[agent] = message_id
    return msg_ids


def _poll_reply(
    db_engine: Any,
    agent: str,
    our_msg_id: str,
    thread_id: str,
    since_epoch: Optional[float] = None,
) -> Optional[ReviewOpinion]:
    """Look for a reply message from `agent` referencing our message_id OR thread_id.

    Review fix Important #2 · bound stale reply pickup. If `since_epoch` provided,
    only consider messages with sent_at > since_epoch. Defaults to 1h window when
    omitted (defensive fallback for direct callers).
    """
    from sqlalchemy import text as _text
    # Convert epoch to ISO so Postgres can compare against TIMESTAMPTZ.
    if since_epoch is None:
        since_epoch = time.time() - 3600  # 1h fallback
    import datetime as _dt
    since_iso = _dt.datetime.utcfromtimestamp(since_epoch).isoformat() + "+00:00"
    with db_engine.begin() as conn:
        result = conn.execute(_text(
            """
            SELECT content, sent_at FROM platform_agent_messages
            WHERE from_agent = :a
              AND sent_at > CAST(:since AS TIMESTAMPTZ)
              AND (in_reply_to = :mid OR thread_id = :tid)
            ORDER BY sent_at ASC
            LIMIT 1
            """
        ), {"a": agent, "mid": our_msg_id, "tid": thread_id, "since": since_iso})
        row = result.fetchone()
    if row is None:
        return None
    raw = row.content or ""
    lower = raw.lower()
    if "approve" in lower:
        verdict = "approve"
    elif "reject" in lower:
        verdict = "reject"
    elif "abstain" in lower:
        verdict = "abstain"
    else:
        verdict = "abstain"
    return ReviewOpinion(
        agent=agent,
        verdict=verdict,
        text=raw[:500],
        received_at=time.time(),
    )


def _default_engine() -> Any:
    """Build a SQLAlchemy engine from DATABASE_URL env."""
    from sqlalchemy import create_engine
    url = os.getenv("DATABASE_URL") or "postgresql://localhost/nautilus"
    return create_engine(url)
