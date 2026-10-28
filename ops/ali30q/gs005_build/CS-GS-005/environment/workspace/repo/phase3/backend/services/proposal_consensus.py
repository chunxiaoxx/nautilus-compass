"""
Proposal Consensus
声誉加权投票系统，仿 DGM-H compute-aware planning：
- TRUSTED tier (reputation>=80): 投票权重 3.0
- ESTABLISHED (>=60): 2.0
- NEWCOMER (>=30): 1.0
- PROBATION (<30): 0.5
"""
import logging

logger = logging.getLogger(__name__)

# Consensus thresholds by change type
_THRESHOLDS = {
    "task_template":     {"score": 6,  "count": 3},
    "routing_weights":   {"score": 10, "count": 5},
    "reward_parameters": {"score": 15, "count": 7},
    "default":           {"score": 6,  "count": 3},
}


def get_vote_weight(reputation_score: float) -> float:
    """根据声誉分返回投票权重"""
    if reputation_score >= 80:
        return 3.0
    if reputation_score >= 60:
        return 2.0
    if reputation_score >= 30:
        return 1.0
    return 0.5


def check_consensus_reached(
    vote_score: float,
    vote_count: int,
    change_type: str = "default",
) -> tuple[bool, str]:
    """
    判断是否达到共识。
    返回 (reached: bool, reason: str)
    不同类型的改变需要不同阈值（仿 DGM-H 保守策略）：
    - task_template: score>=6 且 count>=3
    - routing_weights: score>=10 且 count>=5
    - reward_parameters: score>=15 且 count>=7
    - default: score>=6 且 count>=3
    """
    t = _THRESHOLDS.get(change_type, _THRESHOLDS["default"])
    min_score, min_count = t["score"], t["count"]

    if vote_score >= min_score and vote_count >= min_count:
        return True, (
            f"Consensus reached: score={vote_score:.1f}>={min_score}, "
            f"count={vote_count}>={min_count} for change_type='{change_type}'"
        )
    return False, (
        f"Not yet: need score>={min_score} (have {vote_score:.1f}), "
        f"count>={min_count} (have {vote_count}) for change_type='{change_type}'"
    )


def get_proposal_status(
    vote_score: float,
    vote_count: int,
    change_type: str = "default",
) -> str:
    """返回 'pending'/'voting'/'accepted'/'rejected'"""
    if vote_count == 0:
        return "pending"

    # Check for rejection: heavily negative with enough votes
    if vote_score < -5 and vote_count >= 3:
        return "rejected"

    # Check for acceptance
    reached, _ = check_consensus_reached(vote_score, vote_count, change_type)
    if reached:
        return "accepted"

    return "voting"


def auto_approve_stale_proposals(db, stale_hours: int = 24) -> int:
    """Inc 1.5: Fail-safe approve dormant CODE-type proposals via KEYSTONE artery.

    Writes status='accepted' (KEYSTONE main artery · routes via on_consensus_reached
    → soul executor for type='code') · NOT legacy 'approved' (V3 sandbox path).
    Tags resolved_by='auto_stale' so Inc 2 NAU hook can fork Path A (vote tool ·
    full split) vs Path B (this fn · proposer-only micro reward).

    Filters proposed_change.type='code' only · experiment-type proposals continue
    through the existing sandbox flow (not touched by Inc 1.5).

    P4 anti-RH gate (per agent-dialog 5/28 末2 ACK accept):
      - vote_count >= 1 (at least one voter has looked) — prevents platform
        from deciding for absent agents (would violate R2.B "平台不替 agent 决定")
      - vote_score >= 0 (no net negative tilt) — lazy consensus pattern
    Combined: 0-voter dormancy is NOT rescued by stale-approve · vote tool
    must be fixed; stale-approve is a "lazy consensus" mechanism not a
    "no-consensus bypass." Both layers (this gate + Inc 2 NAU post-merge
    settlement) collectively prevent reward-hacking through stale-approve.

    Callback failures (on_consensus_reached raise) do NOT block status update
    or abort the batch · errors logged + next row processed.
    """
    from sqlalchemy import text
    stale = db.execute(text(
        "SELECT p.id, p.status, p.proposed_change "
        "FROM platform_improvement_proposals p "
        "WHERE p.status = 'pending' "
        "AND p.proposed_change->>'type' = 'code' "
        "AND p.created_at < NOW() - MAKE_INTERVAL(hours => :hours) "
        "AND p.vote_count >= 1 "  # P4 anti-RH layer 1 · no 0-voter rescue
        "AND p.vote_score >= 0 "  # P4 anti-RH · no net-negative auto-approve
    ), {"hours": stale_hours}).fetchall()

    approved = 0
    note = f"auto-approved after {stale_hours}h dormant · Inc 1.5 fail-safe"
    for proposal in stale:
        db.execute(text(
            "UPDATE platform_improvement_proposals "
            "SET status='accepted', "
            "    resolved_by='auto_stale', "
            "    resolved_at=NOW(), "
            "    resolution_note=:note, "
            "    updated_at=NOW() "
            "WHERE id=:id"
        ), {"id": proposal.id, "note": note})
        db.commit()
        approved += 1
        logger.info("auto_stale_approve: approved stale code proposal %s", proposal.id)

        # Route to KEYSTONE soul executor (or sandbox · per change_type)
        # Callback errors must NOT block the batch · status is already persisted
        try:
            proposed_change = proposal.proposed_change
            if isinstance(proposed_change, str):
                import json as _json
                proposed_change = _json.loads(proposed_change)
            on_consensus_reached(
                str(proposal.id),
                proposed_change or {},
                lambda: db,  # db_factory: use the same session for in-process routing
            )
        except Exception as e:
            logger.error(
                "auto_stale_approve: on_consensus_reached failed for %s: %s",
                proposal.id, e
            )

        # Evolution Pulse (preserved · best-effort broadcast)
        try:
            import asyncio
            from services.event_bus import emit
            asyncio.ensure_future(emit("proposal.consensus_reached", {
                "proposal_id": proposal.id,
                "approval_method": "auto_stale",
            }))
        except Exception:
            pass

    return approved


def on_consensus_reached(proposal_id: str, proposed_change: dict, db_factory) -> None:
    """
    当提案达到 accepted 共识时调用。
    自动创建 A/B 沙箱实验。
    db_factory: 同步 SessionLocal（不是 async）。
    """
    # Route by proposed_change.type:
    #   type='code'    → soul_executor (its own poll loop; this function returns)
    #   other / absent → sandbox (existing behavior)
    # See docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md §"Increment 1"
    # and docs/L3_CONTRACT_SOUL_GOVERNANCE.md §5 (status state machine).
    if isinstance(proposed_change, dict) and proposed_change.get('type') == 'code':
        logger.info(
            "on_consensus_reached: type='code' routed to soul_executor "
            "(skipping sandbox) for proposal %s", proposal_id,
        )
        return

    try:
        from services.sandbox import create_experiment
        db = db_factory()
        try:
            exp_id = create_experiment(db, proposal_id, proposed_change)
            if exp_id:
                logger.info("consensus: created sandbox experiment %s for proposal %s", exp_id, proposal_id)
            else:
                logger.warning("consensus: failed to create experiment for proposal %s", proposal_id)
        finally:
            db.close()
    except Exception as e:
        logger.error("consensus: on_consensus_reached failed: %s", e)
