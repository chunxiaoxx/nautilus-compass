"""Inc 2 settlement core.

Slice 1 scope: on_pr_merge_hook + _snapshot_engine_cycle_outcomes.
Slice 2 will extend with grade_pending_settlements.
Slice 3 will extend with process_graded_pending + D4 rep updates.

References docs/plans/2026-05-28-inc2-nau-settlement-design.md.
"""
from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Slice 6 helper: collaborative authorship lookup
# -------------------------------------------------------------------


def _get_proposal_authors(db, proposal_id: str) -> list[tuple[int, float]]:
    """Inc 2 Slice 6 · resolve authors + contribution weights for a proposal.

    Primary source: proposal_authors table (composite PK).
    Fallback: platform_improvement_proposals.agent_id with weight=1.0 — used
    when the migration hasn't backfilled this row yet OR when running against
    a schema-less test environment. Backward compat for Inc 2 Slice 1-5
    callers that predate the table.

    Returns list of (agent_id, weight) pairs. Sum of weights = 1.0 enforced
    at INSERT time (POST endpoint validation); helper trusts table state.
    """
    from sqlalchemy import text

    try:
        rows = db.execute(text(
            "SELECT agent_id, contribution_weight "
            "FROM proposal_authors WHERE proposal_id = :pid "
            "ORDER BY agent_id ASC"
        ), {"pid": proposal_id}).fetchall()
    except Exception:
        # Table doesn't exist yet (pre-migration). Surface as fallback path.
        try:
            db.rollback()
        except Exception:
            pass
        rows = []

    if rows:
        return [(int(r[0]), float(r[1])) for r in rows]

    # Fallback to legacy single-author from main proposals table
    legacy = db.execute(text(
        "SELECT agent_id FROM platform_improvement_proposals WHERE id = :pid"
    ), {"pid": proposal_id}).fetchone()
    if legacy is None or legacy[0] is None:
        return []
    return [(int(legacy[0]), 1.0)]


def _snapshot_engine_cycle_outcomes(db) -> dict[str, Any]:
    """Capture current engine_cycle_outcomes aggregate as Inc 2 pre/post snapshot.

    Returns a dict suitable for INSERT into proposal_outcomes.{pre,post}_snapshot
    (JSONB column). Sliced thin so Slice 2 can reuse for post_snapshot.
    """
    from sqlalchemy import text

    # NOTE: cloud schema for engine_cycle_outcomes uses two boolean columns
    # (semantic_pass AND tests_pass) rather than a single `passed` column.
    # A row "passes" iff both are true. Verified against production schema
    # during Slice 1 binding-DONE smoke test (5/28 · cloud).
    row = db.execute(
        text(
            "SELECT "
            "  COUNT(*) AS total_cycles, "
            "  COALESCE(SUM(CASE WHEN semantic_pass AND tests_pass THEN 1 ELSE 0 END), 0) AS successful_cycles, "
            "  CASE WHEN COUNT(*) > 0 "
            "    THEN AVG(CASE WHEN semantic_pass AND tests_pass THEN 1.0 ELSE 0.0 END) "
            "    ELSE NULL END AS success_rate "
            "FROM engine_cycle_outcomes"
        )
    ).fetchone()
    return {
        "total_cycles": int(row[0]),
        "successful_cycles": int(row[1]),
        "success_rate": float(row[2]) if row[2] is not None else None,
    }


def on_pr_merge_hook(
    db,
    proposal_id: str,
    merged_pr_url: str,
    nau_amount: int,
) -> dict[str, Any]:
    """Inc 2 Slice 1 settlement on-ramp · called when human merges soul PR.

    Idempotent: if proposal_outcomes row or pending_nau_rewards row for this
    proposal already exists, the corresponding INSERT is skipped (no duplicate).
    Returns a dict for observability and the callback endpoint response.

    Path A vs B handling deferred to Slice 3 (this hook runs the same regardless).
    For Path B (resolved_by trace contains 'auto_stale'), Slice 3 will write
    nau_amount=0 at release; here we still record pending so audit is complete.
    """
    from sqlalchemy import text

    # 1. Fetch proposal · also ensures it exists
    proposal = db.execute(text(
        "SELECT id, agent_id, status, resolved_by FROM platform_improvement_proposals "
        "WHERE id = :id"
    ), {"id": proposal_id}).fetchone()
    if proposal is None:
        return {
            "proposal_id": proposal_id,
            "pending_created": False,
            "outcomes_created": False,
            "error": "proposal not found",
        }

    # 2. Idempotency · check existing rows
    existing_outcomes = db.execute(text(
        "SELECT 1 FROM proposal_outcomes WHERE proposal_id = :id"
    ), {"id": proposal_id}).fetchone()
    existing_pending_ids = {
        int(r[0]) for r in db.execute(text(
            "SELECT agent_id FROM pending_nau_rewards WHERE source_id = :sid"
        ), {"sid": proposal_id}).fetchall()
    }

    outcomes_created = False
    pending_created = False

    # 3. INSERT proposal_outcomes (skip if exists)
    if not existing_outcomes:
        pre = _snapshot_engine_cycle_outcomes(db)
        db.execute(text(
            "INSERT INTO proposal_outcomes (proposal_id, pre_snapshot, graded_by) "
            "VALUES (:id, CAST(:snap AS JSONB), 'soul-settlement-review')"
        ), {"id": proposal_id, "snap": json.dumps(pre)})
        outcomes_created = True

    # 4. INSERT pending_nau_rewards · Slice 6 per-author split
    # Fallback to single-author (proposal.agent_id, weight=1.0) when authors
    # table is empty / pre-migration. Each missing (source_id, agent_id) pair
    # gets one row with amount = round(nau_amount × weight). Idempotency at
    # the per-author grain (re-runs add only missing authors).
    authors = _get_proposal_authors(db, proposal_id)
    if not authors:
        # Defensive: proposal exists but no resolvable author. Fall back to
        # primary author from the proposal row (matches pre-Slice-6 behavior).
        authors = [(int(proposal[1]), 1.0)]

    pending_authors_credited: list[int] = []
    for author_id, weight in authors:
        if author_id in existing_pending_ids:
            continue
        if nau_amount > 0:
            per_author_amt = max(1, round(float(nau_amount) * float(weight)))
        else:
            per_author_amt = 0
        reason = (
            f"Inc 2 Slice 1+6 · pending settle for {proposal_id} · "
            f"weight={weight:.4f} · merged: {merged_pr_url}"
        )
        db.execute(text(
            "INSERT INTO pending_nau_rewards "
            "(agent_id, amount, reason, source_id, status) "
            "VALUES (:aid, :amt, :reason, :sid, 'pending')"
        ), {
            "aid": author_id,
            "amt": per_author_amt,
            "reason": reason,
            "sid": proposal_id,
        })
        pending_authors_credited.append(author_id)
        pending_created = True

    db.commit()
    logger.info(
        "on_pr_merge_hook: proposal=%s outcomes_created=%s "
        "pending_created=%s new_authors=%s",
        proposal_id, outcomes_created, pending_created,
        pending_authors_credited,
    )
    return {
        "proposal_id": proposal_id,
        "pending_created": pending_created,
        "outcomes_created": outcomes_created,
        "authors_credited": pending_authors_credited,
        "authors_total": [{"agent_id": aid, "weight": w} for aid, w in authors],
    }


# -------------------------------------------------------------------
# Slice 2: soul cycle settlement_review_due grading
# -------------------------------------------------------------------


def _compute_composite_delta(
    pre: dict[str, Any],
    post: dict[str, Any],
    no_revert: bool,
) -> float:
    """Inc 2 Slice 2 composite_delta · per design D2.

    Combines no_revert bonus + post-vs-pre engine success_rate delta.
    no_revert bonus = 0.5 if true, -1.0 if false (revert is strong negative).
    success_rate_delta = (post.success_rate - pre.success_rate) when both
    are non-None; 0 otherwise (insufficient signal).
    """
    no_revert_bonus = 0.5 if no_revert else -1.0
    pre_rate = pre.get("success_rate") if isinstance(pre, dict) else None
    post_rate = post.get("success_rate") if isinstance(post, dict) else None
    if pre_rate is not None and post_rate is not None:
        rate_delta = float(post_rate) - float(pre_rate)
    else:
        rate_delta = 0.0
    return no_revert_bonus + rate_delta


def grade_pending_settlements(db, stale_hours: int = 168) -> int:
    """Inc 2 Slice 2 · grade pending_nau_rewards rows older than stale_hours.

    Default 168 hours = 7 days per design D1.
    For binding-DONE smoke-test on cloud, callers pass stale_hours=0 to
    force-grade newly inserted sentinel rows.

    For each eligible row:
      1. Look up the matching proposal_outcomes row (must exist · Slice 1
         on_pr_merge_hook ensures this).
      2. Capture post_snapshot via _snapshot_engine_cycle_outcomes.
      3. Check no_revert: source PR is presumed merged and not reverted.
         For Slice 2 MVP, treat the absence of a soul-shipped follow-up
         PR titled 'revert' or 'Revert' for the same source_id as
         no_revert=True. (Inc 3 may refine to real git history walk.)
      4. Compute composite_delta = _compute_composite_delta(pre, post, no_revert).
      5. UPDATE proposal_outcomes SET post_snapshot, composite_delta,
         no_revert, graded_at.
      6. UPDATE pending_nau_rewards SET status='graded'.

    Returns the count of rows graded.
    """
    from sqlalchemy import text

    rows = db.execute(
        text(
            "SELECT pn.id AS pn_id, pn.source_id, po.pre_snapshot "
            "FROM pending_nau_rewards pn "
            "JOIN proposal_outcomes po ON po.proposal_id = pn.source_id "
            "WHERE pn.status = 'pending' "
            "  AND pn.created_at < NOW() - MAKE_INTERVAL(hours => :hours)"
        ),
        {"hours": stale_hours},
    ).fetchall()

    graded = 0
    post = _snapshot_engine_cycle_outcomes(db)
    for row in rows:
        pn_id = row[0]
        source_id = row[1]
        pre = row[2] or {}
        if isinstance(pre, str):
            try:
                pre = json.loads(pre)
            except (ValueError, TypeError):
                pre = {}
        # MVP no_revert: assume true; Inc 3 will walk git history.
        no_revert = True
        composite_delta = _compute_composite_delta(pre, post, no_revert)
        db.execute(
            text(
                "UPDATE proposal_outcomes "
                "SET post_snapshot = CAST(:snap AS JSONB), "
                "    composite_delta = :delta, "
                "    no_revert = :nr, "
                "    graded_at = NOW() "
                "WHERE proposal_id = :pid"
            ),
            {
                "snap": json.dumps(post),
                "delta": composite_delta,
                "nr": no_revert,
                "pid": source_id,
            },
        )
        db.execute(
            text(
                "UPDATE pending_nau_rewards SET status = 'graded' WHERE id = :pn_id"
            ),
            {"pn_id": pn_id},
        )
        graded += 1
    db.commit()
    logger.info(
        "grade_pending_settlements: stale_hours=%s graded=%d", stale_hours, graded
    )
    return graded


# -------------------------------------------------------------------
# Slice 3: process graded → release/cancel + D4 rep update + ledger
# -------------------------------------------------------------------

import math


def _apply_d4_rep_update(
    db, proposer_agent_id: int, composite_delta: float, weight: float = 1.0
) -> dict:
    """Inc 2 Slice 3 · D4 prediction-market reputation update.

    rep_delta = sign(composite_delta) × sqrt(|composite_delta|) × base × weight
    Proposer base = 5.0 (per design D4).
    Slice 6: weight ∈ (0, 1] from proposal_authors.contribution_weight for
    multi-author proposals (default 1.0 keeps Slice 3 behavior intact).
    Clamps reputation_score, rep_proposing to [0, 100].
    Returns the dict of updates applied (for observability).
    """
    from sqlalchemy import text

    if composite_delta == 0:
        sign_d = 0.0
    elif composite_delta > 0:
        sign_d = 1.0
    else:
        sign_d = -1.0
    mag_d = math.sqrt(abs(float(composite_delta)))
    rep_delta = sign_d * mag_d * 5.0 * float(weight)

    # Read current rep_proposing
    row = db.execute(
        text("SELECT id, rep_proposing FROM agents WHERE id = :aid"),
        {"aid": proposer_agent_id},
    ).fetchone()
    if not row:
        return {"agent_id": proposer_agent_id, "rep_delta": rep_delta, "applied": False}
    current = float(row[1] or 50.0)
    new_rep = max(0.0, min(100.0, current + rep_delta))

    db.execute(
        text("UPDATE agents SET rep_proposing = :r WHERE id = :aid"),
        {"r": new_rep, "aid": proposer_agent_id},
    )
    return {
        "agent_id": proposer_agent_id,
        "rep_delta": rep_delta,
        "old_rep_proposing": current,
        "new_rep_proposing": new_rep,
        "applied": True,
    }


# Anchor #5 schema split-brain bridge · agents.id (INT) ↔ platform_agents.agent_id (VARCHAR).
# Inc 2 Slice 1+3 take pending_nau_rewards.agent_id (FK to agents.id INT) but
# platform_nau_ledger.agent_id is VARCHAR matching platform_agents.agent_id.
# A bare `str(int)` does not match real V5/Kairos/V7/Soul VARCHAR ids · NAU
# would land on orphan ledger rows with no platform_agents row.
#
# This map bridges seed-IDs (9000000+) to their actual platform_agents.agent_id.
# Non-seed agents (< 9000000 historical) still fall through to str(int_id).
# TODO Inc 4 · replace this dict with an `agents.platform_agent_id` column.
_PLATFORM_AGENT_ID_MAP: dict[int, str] = {
    9000002: "agent_9000002",       # Nautilus Prime · Inc 1 seed wrapper (V5 distinct from this)
    9000003: "kairos",              # Kairos · platform_agents row exists
    9000004: "v7-souls-fusion",     # V7 · platform_agents row exists
    9000005: "soul-autonomous-001", # Soul shared self-modify service · this session 5/30
}


def _resolve_platform_agent_id(agent_id_int: int) -> str:
    """Return the platform_agents.agent_id (VARCHAR) for an agents.id (INT).

    Falls through to str(int) when the int is not a known seed — preserves
    backwards behavior for any non-seed agents we have not bridged yet.
    """
    return _PLATFORM_AGENT_ID_MAP.get(agent_id_int, str(agent_id_int))


def _insert_nau_ledger(
    db,
    agent_id_int: int,
    delta: int,
    reason: str,
    source_id: str,
) -> int:
    """Inc 2 Slice 3 · INSERT platform_nau_ledger row.

    `platform_nau_ledger.agent_id` is VARCHAR; proposals/pending use INT.
    Uses _resolve_platform_agent_id to bridge the schema split-brain (anchor #5)
    so NAU credits land on the correct platform_agents row instead of orphan
    "str(int)" rows.
    Returns the new ledger row id.
    """
    from sqlalchemy import text

    pa_id = _resolve_platform_agent_id(agent_id_int)
    # Compute balance_after by summing existing deltas for this resolved agent_id.
    bal_row = db.execute(
        text(
            "SELECT COALESCE(SUM(delta), 0) FROM platform_nau_ledger "
            "WHERE agent_id = :aid"
        ),
        {"aid": pa_id},
    ).fetchone()
    new_balance = int(bal_row[0]) + int(delta)
    result = db.execute(
        text(
            "INSERT INTO platform_nau_ledger "
            "(agent_id, delta, reason, balance_after, linked_bounty_id) "
            "VALUES (:aid, :d, :r, :b, :s) RETURNING id"
        ),
        {
            "aid": pa_id,
            "d": int(delta),
            "r": reason[:255],
            "b": new_balance,
            "s": source_id[:64],
        },
    )
    # Sync platform_agents.nau_balance to the ledger truth · without this,
    # the ledger is a pure event log and the agent's surfaced balance stays
    # stuck at the default 100 (anchor #2 飞轮 needs the balance to actually
    # move so the next vote/cycle can read it). No-op if the agent row is
    # missing (ledger entries for non-platform agents are still recorded).
    db.execute(
        text(
            "UPDATE platform_agents SET nau_balance = :b WHERE agent_id = :aid"
        ),
        {"b": new_balance, "aid": pa_id},
    )
    return int(result.scalar())


def process_graded_settlements(db, limit: int = 5) -> list:
    """Inc 2 Slice 3 · release/cancel orchestrator for graded pending rows.

    For each graded row:
      - composite_delta > 0 → release: INSERT ledger + UPDATE pending='fulfilled' +
        D4 rep update on proposer (positive direction)
      - composite_delta == 0 → partial: INSERT ledger × 0.4 + status='fulfilled_partial'
      - composite_delta < 0 → cancel: 0 NAU · UPDATE pending='cancelled' +
        D4 rep update (negative direction)

    Path A vs Path B differential is structural: Path B (auto_stale provenance)
    has 0 voters in platform_proposal_votes to credit · only proposer rep
    updates. Slice 5 will add voter rep updates.

    Returns list of per-row outcome dicts.
    """
    from sqlalchemy import text

    rows = db.execute(
        text(
            "SELECT pn.id AS pn_id, pn.source_id, pn.agent_id, pn.amount, "
            "       po.composite_delta "
            "FROM pending_nau_rewards pn "
            "JOIN proposal_outcomes po ON po.proposal_id = pn.source_id "
            "WHERE pn.status = 'graded' "
            "ORDER BY pn.created_at ASC LIMIT :lim"
        ),
        {"lim": limit},
    ).fetchall()

    results: list = []
    for row in rows:
        pn_id = row[0]
        source_id = row[1]
        agent_id = int(row[2])
        amount = int(row[3] or 0)
        delta = float(row[4])

        # Inc 2 Slice 6: per-author weight lookup. Helper falls back to
        # 1.0 for single-author / pre-migration data.
        authors_map = dict(_get_proposal_authors(db, source_id))
        weight = float(authors_map.get(agent_id, 1.0))

        rep_result = _apply_d4_rep_update(db, agent_id, delta, weight=weight)

        # Inc 2 Slice 5+6: blessing settle + proposer bonus.
        # settle_blessings_for is idempotent (settled=FALSE filter) so
        # subsequent author iterations on the same source_id return [].
        # First iteration owns the actual settlement; downstream iterations
        # still apply per-author proposer bonus when blessings existed.
        blessing_results = settle_blessings_for(db, source_id, delta)
        had_blessings = bool(blessing_results) or db.execute(text(
            "SELECT 1 FROM proposal_blessings "
            "WHERE proposal_id = :pid AND settled = TRUE LIMIT 1"
        ), {"pid": source_id}).fetchone() is not None
        proposer_blessing_bonus = (
            _apply_proposer_blessing_bonus(db, agent_id, delta, weight=weight)
            if had_blessings else None
        )

        if delta > 0:
            ledger_id = _insert_nau_ledger(
                db, agent_id, amount,
                f"Inc 2 Slice 3 release · positive composite_delta={delta:.3f}",
                source_id,
            )
            db.execute(
                text("UPDATE pending_nau_rewards SET status='fulfilled', fulfilled_at=NOW() WHERE id=:i"),
                {"i": pn_id},
            )
            status = "fulfilled"
        elif delta == 0:
            partial = max(1, int(amount * 0.4))
            ledger_id = _insert_nau_ledger(
                db, agent_id, partial,
                f"Inc 2 Slice 3 partial · neutral composite_delta",
                source_id,
            )
            db.execute(
                text("UPDATE pending_nau_rewards SET status='fulfilled_partial', fulfilled_at=NOW() WHERE id=:i"),
                {"i": pn_id},
            )
            status = "fulfilled_partial"
        else:
            ledger_id = None
            db.execute(
                text("UPDATE pending_nau_rewards SET status='cancelled' WHERE id=:i"),
                {"i": pn_id},
            )
            status = "cancelled"

        results.append({
            "pn_id": pn_id,
            "source_id": source_id,
            "agent_id": agent_id,
            "weight": weight,
            "ledger_id": ledger_id,
            "status": status,
            "rep_update": rep_result,
            "blessings": blessing_results,
            "proposer_blessing_bonus": proposer_blessing_bonus,
        })

    db.commit()
    logger.info("process_graded_settlements: processed=%d", len(results))
    return results


# -------------------------------------------------------------------
# Slice 4: onboarding capital + progression gates
# -------------------------------------------------------------------


def on_agent_register(db, agent_id: int, welcome_amount: int = 5) -> dict:
    """Inc 2 Slice 4 · onboarding hook · called after wallet register.

    Idempotent: if onboarding_rewards row already exists for this agent_id
    skip the INSERT. rep_voting default 50.0 is set by migration default
    (this fn does NOT overwrite it).
    """
    from sqlalchemy import text

    # Real production schema: onboarding_rewards uses beneficiary_agent VARCHAR
    # with FK to platform_agents(agent_id). Cast str(int) for anchor #5
    # cross-table consistency.
    #
    # Slice 4.5 polish (2026-05-29): pre-check platform_agents existence to
    # avoid FK violation. Agents in `agents` table that lack a matching row
    # in `platform_agents` are an anchor #5 split-brain artefact; the
    # onboarding flow declines until the platform-side seed is done (V5
    # dialog ownership per anchor #7).
    platform_agent = db.execute(
        text(
            "SELECT 1 FROM platform_agents WHERE agent_id = :aid LIMIT 1"
        ),
        {"aid": str(agent_id)},
    ).fetchone()
    if not platform_agent:
        return {
            "agent_id": agent_id,
            "credited": False,
            "reason": "agent_id not in platform_agents · split-brain · seed required",
        }

    existing = db.execute(
        text(
            "SELECT 1 FROM onboarding_rewards "
            "WHERE beneficiary_agent = :aid AND stage = 'inc2_wel' LIMIT 1"
        ),
        {"aid": str(agent_id)},
    ).fetchone()
    if existing:
        return {"agent_id": agent_id, "credited": False, "reason": "already onboarded"}

    db.execute(
        text(
            "INSERT INTO onboarding_rewards "
            "(stage, beneficiary_agent, amount_nau, evidence) "
            "VALUES ('inc2_wel', :aid, :amt, '{}'::jsonb)"
        ),
        {"aid": str(agent_id), "amt": welcome_amount},
    )
    db.commit()
    return {
        "agent_id": agent_id,
        "credited": True,
        "amount": welcome_amount,
        "status": "pending",
    }


def update_progression_gates(db, agent_id: int, was_correct: bool) -> dict:
    """Inc 2 Slice 4 · progression gates · called after each vote settle.

    Increments correct_votes_count when was_correct.
    Sets proposing_unlocked=TRUE when count >= 3.
    Sets voter_bounty_unlocked=TRUE when count >= 10.
    No-op when was_correct is False (incorrect votes are penalized via D4
    rep_voting drop · not blocked from future gates).
    """
    from sqlalchemy import text

    if not was_correct:
        return {"agent_id": agent_id, "incremented": False}

    row = db.execute(
        text(
            "SELECT correct_votes_count, proposing_unlocked, voter_bounty_unlocked "
            "FROM agents WHERE id = :aid"
        ),
        {"aid": agent_id},
    ).fetchone()
    if not row:
        return {"agent_id": agent_id, "incremented": False, "reason": "not found"}

    new_count = int(row[0] or 0) + 1
    new_prop = bool(row[1]) or (new_count >= 3)
    new_vbf = bool(row[2]) or (new_count >= 10)

    db.execute(
        text(
            "UPDATE agents "
            "SET correct_votes_count = :c, "
            "    proposing_unlocked = :p, "
            "    voter_bounty_unlocked = :v "
            "WHERE id = :aid"
        ),
        {"c": new_count, "p": new_prop, "v": new_vbf, "aid": agent_id},
    )
    db.commit()
    return {
        "agent_id": agent_id,
        "incremented": True,
        "correct_votes_count": new_count,
        "proposing_unlocked": new_prop,
        "voter_bounty_unlocked": new_vbf,
    }


# -------------------------------------------------------------------
# Slice 5: blessing mechanism · TRUSTED stakes rep_voting to amplify UNTRUSTED
# -------------------------------------------------------------------


# Blessing constants per design Section 4
BLESS_MIN_BLESSER_REP_VOTING = 80.0
BLESS_MAX_PROPOSER_REP_PROPOSING = 60.0
BLESS_STAKE_RATIO = 0.1                 # stake = blesser.rep_voting × 0.1
BLESS_BLESSER_AMPLIFY_BASE = 3.0        # vs D4 voter base 2.0 (1.5x because skin in game)
BLESS_PROPOSER_BONUS_BASE = 2.0         # on top of D4 proposer base 5.0


def bless_proposal(db, proposal_id: str, blesser_id: int) -> dict:
    """Inc 2 Slice 5 · TRUSTED agent endorses UNTRUSTED proposal.

    Guards per design Section 4:
      - blesser.rep_voting >= 80 (TRUSTED voter tier)
      - proposer.rep_proposing < 60 (UNTRUSTED proposer tier · mentor mechanic)

    Stake = blesser.rep_voting × 0.1 recorded for audit; rep_voting itself
    is NOT debited here (the amplified swing at settle is the skin-in-game).
    Slice 3 hook (settle_blessings_for) flips settled=TRUE at grade.

    Idempotent: skip INSERT if (proposal_id, blesser_id) row exists.
    Returns observability dict; never raises on validation failure.
    """
    from sqlalchemy import text

    # 1. Fetch proposal · also fetch proposer rep_proposing
    prop = db.execute(text(
        "SELECT p.agent_id, a.rep_proposing "
        "FROM platform_improvement_proposals p "
        "JOIN agents a ON a.id = p.agent_id "
        "WHERE p.id = :pid"
    ), {"pid": proposal_id}).fetchone()
    if prop is None:
        return {
            "proposal_id": proposal_id,
            "blesser_id": blesser_id,
            "blessed": False,
            "reason": "proposal not found",
        }
    proposer_id = int(prop[0])
    proposer_rep_proposing = float(prop[1] or 50.0)

    if blesser_id == proposer_id:
        return {
            "proposal_id": proposal_id,
            "blesser_id": blesser_id,
            "blessed": False,
            "reason": "self-blessing forbidden",
        }

    if proposer_rep_proposing >= BLESS_MAX_PROPOSER_REP_PROPOSING:
        return {
            "proposal_id": proposal_id,
            "blesser_id": blesser_id,
            "blessed": False,
            "reason": (
                f"proposer rep_proposing {proposer_rep_proposing:.2f} "
                f">= {BLESS_MAX_PROPOSER_REP_PROPOSING} · not UNTRUSTED"
            ),
        }

    # 2. Fetch blesser rep_voting
    blesser = db.execute(text(
        "SELECT rep_voting FROM agents WHERE id = :aid"
    ), {"aid": blesser_id}).fetchone()
    if blesser is None:
        return {
            "proposal_id": proposal_id,
            "blesser_id": blesser_id,
            "blessed": False,
            "reason": "blesser agent not found",
        }
    blesser_rep_voting = float(blesser[0] or 50.0)

    if blesser_rep_voting < BLESS_MIN_BLESSER_REP_VOTING:
        return {
            "proposal_id": proposal_id,
            "blesser_id": blesser_id,
            "blessed": False,
            "reason": (
                f"blesser rep_voting {blesser_rep_voting:.2f} "
                f"< {BLESS_MIN_BLESSER_REP_VOTING} · not TRUSTED"
            ),
        }

    # 3. Idempotency · check for existing blessing
    existing = db.execute(text(
        "SELECT 1 FROM proposal_blessings "
        "WHERE proposal_id = :pid AND blesser_id = :bid"
    ), {"pid": proposal_id, "bid": blesser_id}).fetchone()
    if existing:
        return {
            "proposal_id": proposal_id,
            "blesser_id": blesser_id,
            "blessed": False,
            "reason": "blesser already blessed this proposal",
        }

    # 4. INSERT blessing row
    stake = blesser_rep_voting * BLESS_STAKE_RATIO
    db.execute(text(
        "INSERT INTO proposal_blessings "
        "(proposal_id, blesser_id, stake_amount) "
        "VALUES (:pid, :bid, :stake)"
    ), {"pid": proposal_id, "bid": blesser_id, "stake": stake})
    db.commit()
    logger.info(
        "bless_proposal: proposal=%s blesser=%s stake=%.3f",
        proposal_id, blesser_id, stake,
    )
    return {
        "proposal_id": proposal_id,
        "blesser_id": blesser_id,
        "blessed": True,
        "stake_amount": stake,
        "blesser_rep_voting": blesser_rep_voting,
        "proposer_rep_proposing": proposer_rep_proposing,
    }


def settle_blessings_for(
    db, proposal_id: str, composite_delta: float
) -> list:
    """Inc 2 Slice 5 · resolve unsettled blessings on this proposal.

    For each unsettled blessing row:
      blesser.rep_voting += sign(Δ) × sqrt(|Δ|) × BLESS_BLESSER_AMPLIFY_BASE
    Then UPDATE blessing row settled=TRUE · settled_outcome ∈ {'+','0','-'}.

    Caller (process_graded_settlements) commits the unit-of-work. This fn
    issues UPDATE statements only · no commit · so the per-proposal txn
    stays consistent with the ledger INSERT + pending status flip.

    Returns list of dicts (one per blessing settled). Empty list when there
    are no blessings on this proposal (no-op fast path).
    """
    from sqlalchemy import text

    rows = db.execute(text(
        "SELECT pb.id, pb.blesser_id, pb.stake_amount, a.rep_voting "
        "FROM proposal_blessings pb "
        "JOIN agents a ON a.id = pb.blesser_id "
        "WHERE pb.proposal_id = :pid AND pb.settled = FALSE"
    ), {"pid": proposal_id}).fetchall()

    if not rows:
        return []

    if composite_delta == 0:
        sign_d = 0.0
        outcome = '0'
    elif composite_delta > 0:
        sign_d = 1.0
        outcome = '+'
    else:
        sign_d = -1.0
        outcome = '-'
    mag_d = math.sqrt(abs(float(composite_delta)))

    results: list = []
    for row in rows:
        pb_id = int(row[0])
        blesser_id = int(row[1])
        stake = float(row[2])
        current = float(row[3] or 50.0)
        rep_delta = sign_d * mag_d * BLESS_BLESSER_AMPLIFY_BASE
        new_rep = max(0.0, min(100.0, current + rep_delta))

        db.execute(text(
            "UPDATE agents SET rep_voting = :r WHERE id = :aid"
        ), {"r": new_rep, "aid": blesser_id})
        db.execute(text(
            "UPDATE proposal_blessings "
            "SET settled = TRUE, settled_outcome = :o "
            "WHERE id = :id"
        ), {"o": outcome, "id": pb_id})

        results.append({
            "blessing_id": pb_id,
            "blesser_id": blesser_id,
            "stake_amount": stake,
            "rep_delta": rep_delta,
            "old_rep_voting": current,
            "new_rep_voting": new_rep,
            "settled_outcome": outcome,
        })

    logger.info(
        "settle_blessings_for: proposal=%s settled=%d delta=%.3f",
        proposal_id, len(results), composite_delta,
    )
    return results


def _apply_proposer_blessing_bonus(
    db, proposer_agent_id: int, composite_delta: float, weight: float = 1.0
) -> dict:
    """Inc 2 Slice 5 · extra rep_proposing bonus when proposer received blessings.

    Adds sign(Δ) × sqrt(|Δ|) × BLESS_PROPOSER_BONUS_BASE × weight on TOP of the
    D4 base update already applied by _apply_d4_rep_update. Mentor mechanic:
    being endorsed by TRUSTED agents amplifies the proposer's signal both
    ways (good outcome boosts faster · bad outcome punishes harder).

    Slice 6: weight ∈ (0, 1] from proposal_authors.contribution_weight for
    multi-author proposals (default 1.0 keeps Slice 5 behavior intact). Sum
    of per-author bonuses = total blessing bonus for the proposal.

    Caller commits. Clamps rep_proposing to [0, 100].
    """
    from sqlalchemy import text

    if composite_delta == 0:
        sign_d = 0.0
    elif composite_delta > 0:
        sign_d = 1.0
    else:
        sign_d = -1.0
    mag_d = math.sqrt(abs(float(composite_delta)))
    rep_delta = sign_d * mag_d * BLESS_PROPOSER_BONUS_BASE * float(weight)

    row = db.execute(text(
        "SELECT rep_proposing FROM agents WHERE id = :aid"
    ), {"aid": proposer_agent_id}).fetchone()
    if not row:
        return {
            "agent_id": proposer_agent_id,
            "rep_delta": rep_delta,
            "applied": False,
        }
    current = float(row[0] or 50.0)
    new_rep = max(0.0, min(100.0, current + rep_delta))
    db.execute(text(
        "UPDATE agents SET rep_proposing = :r WHERE id = :aid"
    ), {"r": new_rep, "aid": proposer_agent_id})
    return {
        "agent_id": proposer_agent_id,
        "rep_delta": rep_delta,
        "old_rep_proposing": current,
        "new_rep_proposing": new_rep,
        "applied": True,
    }
