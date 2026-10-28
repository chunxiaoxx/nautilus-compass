"""Thin wrapper → services.pairs.identity (自↔他 Pair 6)"""
from services.pairs.identity import (  # noqa: F401
    GOVERNANCE_TIERS, get_governance_tier, get_vote_weight_by_tier,
    submit_external_proposal, submit_peer_review, get_parliament_summary,
)
