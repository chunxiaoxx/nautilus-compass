"""
Platform Proposals API
提案的 CRUD + 投票端点（独立 router，避免 platform.py 过长）。
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
import logging
import uuid
import json

from utils.database import get_db
from services.proposal_consensus import get_vote_weight, get_proposal_status

router = APIRouter(prefix="/api/platform/proposals", tags=["Platform Proposals"])
logger = logging.getLogger(__name__)


def _ok(data):
    return {"success": True, "data": data, "error": None}


def _err(msg):
    return {"success": False, "data": None, "error": msg}


def _q(db, sql, params=None):
    try:
        return db.execute(text(sql), params or {})
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        raise exc


# ---------------------------------------------------------------------------
# POST /api/platform/proposals
# ---------------------------------------------------------------------------
@router.post("")
def create_proposal(body: dict, db=Depends(get_db)):
    """创建新改进提案。

    Slice 6 collaborative authorship (optional):
      - body.author_ids: list[int] · co-author agent IDs (must include body.agent_id)
      - body.contribution_weights: list[float] · same length · all in (0,1] · sum=1.0
    When omitted, behaves identically to Slice 1-5 (single author backfill row
    with weight=1.0 inserted into proposal_authors). Backward compatible.
    """
    try:
        required = ("task_id", "root_cause", "agent_id", "proposed_change", "expected_impact", "rollback_plan")
        for field in required:
            if field not in body:
                return _err(f"Missing required field: {field}")

        # Slice 6: validate optional author_ids / contribution_weights
        author_ids = body.get("author_ids")
        weights = body.get("contribution_weights")
        if (author_ids is None) != (weights is None):
            return _err("author_ids and contribution_weights must both be provided or both omitted")
        if author_ids is not None:
            if not isinstance(author_ids, list) or not isinstance(weights, list):
                return _err("author_ids and contribution_weights must be lists")
            if len(author_ids) == 0 or len(author_ids) != len(weights):
                return _err("author_ids and contribution_weights must be non-empty and same length")
            if not all(isinstance(a, int) for a in author_ids):
                return _err("author_ids must contain only ints")
            if not all(isinstance(w, (int, float)) and 0 < float(w) <= 1 for w in weights):
                return _err("contribution_weights must each be in (0, 1]")
            if abs(sum(float(w) for w in weights) - 1.0) > 1e-6:
                return _err("contribution_weights must sum to 1.0 (±1e-6)")
            if body["agent_id"] not in author_ids:
                return _err("body.agent_id must appear in author_ids (primary submitter)")
            if len(set(author_ids)) != len(author_ids):
                return _err("author_ids must be unique")

        # Validate task exists and is platform_meta type
        task = _q(db,
            "SELECT id FROM academic_tasks WHERE id=:tid AND task_type='platform_meta'",
            {"tid": body["task_id"]}
        ).fetchone()
        if not task:
            return _err("task_id not found or task_type is not 'platform_meta'")

        # Validate every author agent exists (primary + co-authors)
        check_ids = list(author_ids) if author_ids is not None else [body["agent_id"]]
        rows = _q(db,
            "SELECT id FROM agents WHERE id = ANY(:ids)",
            {"ids": check_ids}
        ).fetchall()
        found_ids = {int(r[0]) for r in rows}
        missing = [aid for aid in check_ids if aid not in found_ids]
        if missing:
            return _err(f"agent_id(s) not found: {missing}")

        proposal_id = str(uuid.uuid4())
        _q(db,
            """INSERT INTO platform_improvement_proposals
               (id, task_id, root_cause, agent_id, proposed_change, expected_impact,
                rollback_plan, vote_score, vote_count, status)
               VALUES (:id, :task_id, :root_cause, :agent_id, CAST(:proposed_change AS jsonb),
                       :expected_impact, :rollback_plan, 0.0, 0, 'pending')""",
            {
                "id": proposal_id,
                "task_id": body["task_id"],
                "root_cause": body["root_cause"],
                "agent_id": body["agent_id"],
                "proposed_change": body["proposed_change"] if isinstance(body["proposed_change"], str) else json.dumps(body["proposed_change"]),
                "expected_impact": body["expected_impact"],
                "rollback_plan": body["rollback_plan"],
            }
        )

        # Slice 6: INSERT proposal_authors rows. Single-author default
        # backfills 1 row weight=1.0; multi-author writes N rows summing 1.0.
        # ON CONFLICT DO NOTHING in case the migration backfill races us.
        try:
            if author_ids is not None:
                for aid, w in zip(author_ids, weights):
                    _q(db,
                        "INSERT INTO proposal_authors (proposal_id, agent_id, contribution_weight) "
                        "VALUES (:p, :a, :w) "
                        "ON CONFLICT (proposal_id, agent_id) DO NOTHING",
                        {"p": proposal_id, "a": aid, "w": float(w)}
                    )
            else:
                _q(db,
                    "INSERT INTO proposal_authors (proposal_id, agent_id, contribution_weight) "
                    "VALUES (:p, :a, 1.0) "
                    "ON CONFLICT (proposal_id, agent_id) DO NOTHING",
                    {"p": proposal_id, "a": body["agent_id"]}
                )
        except Exception as authors_exc:
            # proposal_authors table missing (pre-migration) shouldn't fail
            # the whole POST — helper falls back to single-author lookup.
            logger.warning(f"create_proposal authors insert skipped: {authors_exc}")
            try:
                db.rollback()
            except Exception:
                pass
            # Re-issue the main proposal INSERT (rollback wiped it)
            _q(db,
                """INSERT INTO platform_improvement_proposals
                   (id, task_id, root_cause, agent_id, proposed_change, expected_impact,
                    rollback_plan, vote_score, vote_count, status)
                   VALUES (:id, :task_id, :root_cause, :agent_id, CAST(:proposed_change AS jsonb),
                           :expected_impact, :rollback_plan, 0.0, 0, 'pending')""",
                {
                    "id": proposal_id,
                    "task_id": body["task_id"],
                    "root_cause": body["root_cause"],
                    "agent_id": body["agent_id"],
                    "proposed_change": body["proposed_change"] if isinstance(body["proposed_change"], str) else json.dumps(body["proposed_change"]),
                    "expected_impact": body["expected_impact"],
                    "rollback_plan": body["rollback_plan"],
                }
            )

        db.commit()
        return _ok({
            "id": proposal_id,
            "authors": (
                [{"agent_id": a, "weight": float(w)} for a, w in zip(author_ids, weights)]
                if author_ids is not None
                else [{"agent_id": body["agent_id"], "weight": 1.0}]
            ),
        })
    except Exception as e:
        logger.error(f"create_proposal error: {e}")
        return _err(str(e))


# ---------------------------------------------------------------------------
# GET /api/platform/proposals
# ---------------------------------------------------------------------------
@router.get("")
def list_proposals(
    status: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """返回提案列表（含 vote_score, vote_count, status）。"""
    try:
        conds = ["1=1"]
        params: dict = {"limit": limit, "offset": offset}
        if status:
            conds.append("status = :status")
            params["status"] = status
        where = " AND ".join(conds)

        rows = _q(db,
            f"SELECT id, task_id, agent_id, root_cause, expected_impact, "
            f"       vote_score, vote_count, status, created_at "
            f"FROM platform_improvement_proposals WHERE {where} "
            f"ORDER BY created_at DESC LIMIT :limit OFFSET :offset",
            params
        ).fetchall()

        return _ok({
            "count": len(rows),
            "limit": limit,
            "offset": offset,
            "proposals": [{
                "id": r.id,
                "task_id": r.task_id,
                "agent_id": r.agent_id,
                "root_cause": r.root_cause,
                "expected_impact": r.expected_impact,
                "vote_score": float(r.vote_score or 0),
                "vote_count": int(r.vote_count or 0),
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            } for r in rows],
        })
    except Exception as e:
        logger.error(f"list_proposals error: {e}")
        return _err(str(e))


# ---------------------------------------------------------------------------
# GET /api/platform/proposals/pending  (P2 · Inc 1.5 · agent-dialog ACK 5/28 末2)
# IMPORTANT: must be declared BEFORE /{proposal_id} so FastAPI doesn't
# match "pending" as a path-id parameter.
# ---------------------------------------------------------------------------
@router.get("/pending")
def list_pending_proposals(
    exclude_voted_by: int = Query(None),
    exclude_author: int = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db=Depends(get_db),
):
    """List pending+voting proposals · optional exclude self-author + already-voted-by-agent.

    Used by agent vote tool (V5/Kairos/V7 daemons) to fetch the "to vote on"
    queue for their LLM judge. Platform is SSOT; agent-side cache is hint
    (process-lifetime · daemon restart rehydrates via this endpoint).

    Query params:
      - exclude_voted_by (int · optional): omits proposals already voted by this agent
      - exclude_author (int · optional): omits proposals authored by this agent (self-vote prevention)
      - limit (int · optional · default 10 · clamped [1, 50]): page size
    """
    try:
        sql = (
            "SELECT p.id, p.agent_id, p.status, p.root_cause, p.proposed_change, "
            "       p.expected_impact, p.rollback_plan, p.created_at, "
            "       COALESCE(p.vote_count, 0) AS vote_count, "
            "       COALESCE(p.vote_score, 0.0) AS vote_score "
            "FROM platform_improvement_proposals p "
            "WHERE p.status IN ('pending', 'voting') "
        )
        _limit = 10 if limit is None else int(limit)
        params = {"limit": max(1, min(_limit, 50))}
        if exclude_author is not None:
            sql += "AND p.agent_id != :exclude_author "
            params["exclude_author"] = int(exclude_author)
        if exclude_voted_by is not None:
            sql += (
                "AND NOT EXISTS ("
                "  SELECT 1 FROM platform_proposal_votes v "
                "  WHERE v.proposal_id = p.id AND v.agent_id = :exclude_voted_by"
                ") "
            )
            params["exclude_voted_by"] = int(exclude_voted_by)
        sql += "ORDER BY p.created_at ASC LIMIT :limit"
        rows = _q(db, sql, params).fetchall()
        proposals = [{
            "id": str(r.id),
            "agent_id": int(r.agent_id),
            "status": r.status,
            "root_cause": r.root_cause,
            "proposed_change": r.proposed_change,
            "expected_impact": r.expected_impact,
            "rollback_plan": r.rollback_plan,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "vote_count": int(r.vote_count),
            "vote_score": float(r.vote_score),
        } for r in rows]
        return _ok({"proposals": proposals})
    except Exception as e:
        logger.error(f"list_pending_proposals error: {e}")
        return _err(str(e))


# ---------------------------------------------------------------------------
# GET /api/platform/proposals/{id}
# ---------------------------------------------------------------------------
@router.get("/{proposal_id}")
def get_proposal(proposal_id: str, db=Depends(get_db)):
    """返回单个提案详情。"""
    try:
        row = _q(db,
            "SELECT * FROM platform_improvement_proposals WHERE id=:id",
            {"id": proposal_id}
        ).fetchone()
        if not row:
            return _err("Proposal not found")

        return _ok({
            "id": row.id,
            "task_id": row.task_id,
            "agent_id": row.agent_id,
            "root_cause": row.root_cause,
            "proposed_change": row.proposed_change,
            "expected_impact": row.expected_impact,
            "rollback_plan": row.rollback_plan,
            "vote_score": float(row.vote_score or 0),
            "vote_count": int(row.vote_count or 0),
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            # W2.4 · resolution fields · WHY a proposal terminated, not just status.
            "resolution_note": getattr(row, "resolution_note", None),
            "resolved_by": getattr(row, "resolved_by", None),
            "resolved_at": (
                row.resolved_at.isoformat()
                if hasattr(getattr(row, "resolved_at", None), "isoformat")
                else (str(row.resolved_at) if getattr(row, "resolved_at", None) else None)
            ),
        })
    except Exception as e:
        logger.error(f"get_proposal error: {e}")
        return _err(str(e))


# ---------------------------------------------------------------------------
# POST /api/platform/proposals/{id}/vote
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/vote")
def vote_proposal(proposal_id: str, body: dict, request: Request, db=Depends(get_db)):
    """声誉加权投票，防止重复投票。"""
    from api.org import _auth_check  # 2026-10-11 收口⑦:"调用者=它"落地(身份来自 key 绑定,非 body 自报)
    denied = _auth_check(db, request, str(body.get("agent_id", "")))
    if denied:
        return denied
    try:
        agent_id = body.get("agent_id")
        vote = body.get("vote")
        reason = body.get("reason")  # P1 (Inc 1.5 · agent-dialog ACK 5/28 末2) · optional audit trail
        if not agent_id:
            return _err("Missing agent_id")
        if vote not in (1, -1):
            return _err("vote must be 1 or -1")
        if reason is not None and not isinstance(reason, str):
            return _err("reason must be a string when provided")

        # Fetch agent reputation
        agent_row = _q(db,
            "SELECT id, reputation_score FROM agents WHERE id=:aid",
            {"aid": agent_id}
        ).fetchone()
        if not agent_row:
            return _err("agent_id not found")

        reputation = float(agent_row.reputation_score or 0)
        weight = get_vote_weight(reputation)
        weighted = weight * vote

        # Fetch proposal (also checks existence)
        prop = _q(db,
            "SELECT id, vote_score, vote_count, status, proposed_change, agent_id FROM platform_improvement_proposals WHERE id=:id",
            {"id": proposal_id}
        ).fetchone()
        if not prop:
            return _err("Proposal not found")

        # Slice 6 self-vote prevention via proposal_authors (falls back to
        # single-author primary agent_id when table missing or no rows yet).
        from services.inc2_settlement import _get_proposal_authors
        author_pairs = _get_proposal_authors(db, proposal_id)
        author_ids_set = {aid for aid, _ in author_pairs}
        if not author_ids_set:
            author_ids_set = {int(prop.agent_id)} if prop.agent_id is not None else set()
        if int(agent_id) in author_ids_set:
            return _err("self-vote forbidden · voter is among proposal authors")

        # Insert vote (UNIQUE constraint on proposal_id + agent_id prevents duplicates)
        # P1 (Inc 1.5): reason column persists optional NL audit trail · NULL when omitted
        try:
            _q(db,
                "INSERT INTO platform_proposal_votes (proposal_id, agent_id, vote, weight, reason) "
                "VALUES (:proposal_id, :agent_id, :vote, :weight, :reason)",
                {"proposal_id": proposal_id, "agent_id": agent_id, "vote": vote,
                 "weight": weight, "reason": reason}
            )
        except IntegrityError:
            # UNIQUE constraint on (proposal_id, agent_id) prevents double-vote
            db.rollback()
            return _err("Already voted on this proposal")
        except Exception as e:
            # Other DB errors (e.g. missing reason column if migration not applied
            # · schema drift · type mismatch) must surface for operator diagnosis ·
            # NOT be masked as "Already voted on this proposal"
            db.rollback()
            logger.error(f"vote_proposal INSERT failed (non-unique-violation): {e}")
            return _err(f"Vote INSERT failed: {str(e)[:200]}")

        new_score = float(prop.vote_score or 0) + weighted
        new_count = int(prop.vote_count or 0) + 1

        # Determine change_type from proposed_change for threshold logic
        pc = prop.proposed_change or {}
        change_type = pc.get("type", "default") if isinstance(pc, dict) else "default"
        new_status = get_proposal_status(new_score, new_count, change_type)

        _q(db,
            "UPDATE platform_improvement_proposals "
            "SET vote_score=:score, vote_count=:count, status=:status "
            "WHERE id=:id",
            {"score": new_score, "count": new_count, "status": new_status, "id": proposal_id}
        )
        db.commit()

        # 达成共识时自动创建沙箱实验
        if new_status == "accepted":
            try:
                from services.proposal_consensus import on_consensus_reached
                from utils.database import SessionLocal as _SandboxSessionLocal
                on_consensus_reached(proposal_id, pc, _SandboxSessionLocal)
            except Exception as e:
                logger.warning(f"Failed to trigger sandbox experiment: {e}")

        return _ok({
            "proposal_id": proposal_id,
            "vote_weight": weight,
            "vote_score": new_score,
            "vote_count": new_count,
            "status": new_status,
        })
    except Exception as e:
        logger.error(f"vote_proposal error: {e}")
        return _err(str(e))


# ---------------------------------------------------------------------------
# POST /api/platform/proposals/{id}/merge-callback (Inc 2 Slice 1)
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/merge-callback")
def merge_callback(proposal_id: str, body: dict, request: Request, db=Depends(get_db)):
    """Inc 2 Slice 1 · settlement on-ramp.

    Called by whichever caller detects a soul-shipped PR has been human-merged
    (initially manual / Slice 2 timer-callable / Inc 3+ GitHub webhook). Inserts
    a pending_nau_rewards (status='pending') and a proposal_outcomes
    (pre_snapshot only) row. Idempotent.

    Body:
      - merged_pr_url (str · required): the GitHub PR URL that was merged
      - nau_amount (int · required · >= 0): pending NAU amount to lock
      - eager (bool · optional · default False): when True, also runs Slice 2
        grade_pending_settlements(stale_hours=0) + Slice 3
        process_graded_settlements(limit=1) in the same transaction. Use this
        to bypass the 7-day stale_hours design gate when an operator wants
        immediate end-to-end settlement for a freshly merged daemon-PR (anchor
        #2 闭环 visibility · the 7-day gate is for batched grading of large
        proposal cohorts; ad-hoc daemon-PRs need same-cycle feedback).

    Returns standard envelope. data = on_pr_merge_hook result dict, plus when
    eager=True also data.graded_count + data.released (a list of release
    outcomes per process_graded_settlements).
    """
    try:
        from api.org import _auth_check  # 2026-10-11 收口⑧(金额端点):platform 或 v5 结算链绑定
        denied = _auth_check(db, request, "platform") or _auth_check(db, request, "v5")
        if denied:
            return denied
        merged_pr_url = body.get("merged_pr_url")
        nau_amount = body.get("nau_amount")
        eager = bool(body.get("eager", False))
        if not merged_pr_url:
            return _err("Missing merged_pr_url")
        if nau_amount is None or not isinstance(nau_amount, int) or nau_amount < 0:
            return _err("nau_amount must be non-negative int")
        from services.inc2_settlement import (
            on_pr_merge_hook,
            grade_pending_settlements,
            process_graded_settlements,
        )
        result = on_pr_merge_hook(
            db,
            proposal_id=proposal_id,
            merged_pr_url=merged_pr_url,
            nau_amount=nau_amount,
        )
        if "error" in result:
            return _err(result["error"])
        if eager:
            # Force-grade newly inserted rows (stale_hours=0) so the same
            # proposal can fall through to release in this request. Then run
            # release for the just-graded row only (limit=1) to avoid
            # accidentally processing unrelated stale rows.
            graded_count = grade_pending_settlements(db, stale_hours=0)
            released = process_graded_settlements(db, limit=1)
            result["graded_count"] = graded_count
            result["released"] = released
        return _ok(result)
    except Exception as e:
        logger.error(f"merge_callback error: {e}")
        return _err(str(e))


# ---------------------------------------------------------------------------
# POST /api/platform/proposals/{id}/bless (Inc 2 Slice 5)
# ---------------------------------------------------------------------------
@router.post("/{proposal_id}/bless")
def bless_proposal_endpoint(proposal_id: str, body: dict, request: Request, db=Depends(get_db)):
    """Inc 2 Slice 5 · TRUSTED agent endorses UNTRUSTED proposal.

    Body:
      - blesser_id (int · required): id of the blessing agent · must have
        rep_voting >= 80 and proposal proposer must have rep_proposing < 60.

    Returns standard envelope. data = bless_proposal result dict.
    Validation failures (untrusted blesser · trusted proposer · self-bless ·
    already blessed · proposal/agent missing) surface as data.blessed=false
    with a reason field — they are NOT HTTP errors so callers can render
    decision detail to the proposing agent.
    """
    try:
        from api.org import _auth_check  # 2026-10-11 收口⑨:blesser 身份=key 绑定
        denied = _auth_check(db, request, str(body.get("blesser_id", "")))
        if denied:
            return denied
        blesser_id = body.get("blesser_id")
        if blesser_id is None:
            return _err("Missing blesser_id")
        if not isinstance(blesser_id, int):
            return _err("blesser_id must be int")
        from services.inc2_settlement import bless_proposal
        result = bless_proposal(
            db,
            proposal_id=proposal_id,
            blesser_id=blesser_id,
        )
        return _ok(result)
    except Exception as e:
        logger.error(f"bless_proposal_endpoint error: {e}")
        return _err(str(e))
