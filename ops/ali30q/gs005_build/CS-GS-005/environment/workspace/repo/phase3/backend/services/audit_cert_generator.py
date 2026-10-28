"""
P5 · Audit certificate generator (5/22).

Generates JSON-LD signed audit certificates for completed bounties.

MVP signing: HMAC-SHA256 with platform secret · zero new deps.
Upgrade path: Ed25519 (cryptography lib) for public verifiability · documented TODO.

Certificate structure:
  - audit_id (= bounty_id)
  - task_spec_hash (sha256 of original task)
  - output_hash (sha256 of final output)
  - fidelity_score (from raid_votes max)
  - quality_score (from raid_executions consensus)
  - cited_memory_refs (from compass_bounty_bridge.poi_cite_trail)
  - council_members (claimer + raid agent_roles)
  - timestamp + signature
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import text as sql_text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

PLATFORM_SIGNING_SECRET = os.getenv(
    "PLATFORM_AUDIT_SIGNING_SECRET",
    "nautilus_audit_v1_mvp_replace_with_strong_secret_in_prod",
)
SIGNING_ALGORITHM = "HMAC-SHA256-MVP"
CERTIFICATE_VERSION = "1.0"


def _sha256(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def _hmac_sign(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    sig = hmac.new(
        PLATFORM_SIGNING_SECRET.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return sig


def generate_certificate(db: Session, bounty_id: str) -> dict:
    """
    Build signed audit certificate for a bounty.

    Returns JSON-LD compatible dict · sign via _hmac_sign.
    Signature covers all fields except 'signature' itself.
    """
    row = db.execute(sql_text(
        """
        SELECT bounty_id, title, description, reward_nau, posted_by, claimed_by,
               status, result, score, metadata
        FROM platform_bounties
        WHERE bounty_id = :b
        """
    ), {"b": bounty_id}).fetchone()

    if not row:
        return {"error": "bounty_not_found", "bounty_id": bounty_id}

    if row.status not in ("settled", "rejected", "completed"):
        return {
            "error": "bounty_not_finalized",
            "bounty_id": bounty_id,
            "current_status": row.status,
            "note": "certificate only available for settled/rejected/completed bounties",
        }

    task_spec_text = f"{row.title}\n\n{row.description or ''}"
    output_text = row.result or ""

    # Pull RAID votes (max fidelity_score · count of council members) from latest execution
    exec_row = db.execute(sql_text(
        "SELECT execution_id, consensus_score FROM raid_executions WHERE task_id = :t "
        "ORDER BY created_at DESC LIMIT 1"
    ), {"t": bounty_id}).fetchone()

    raid_summary = None
    if exec_row:
        raid_summary = db.execute(sql_text(
            """
            SELECT MAX(fidelity_score) AS max_fidelity,
                   MAX(quality_score)  AS max_quality,
                   ARRAY_AGG(DISTINCT agent_role) AS roles
            FROM raid_votes WHERE execution_id = :e
            """
        ), {"e": exec_row.execution_id}).fetchone()

    fidelity = float(raid_summary.max_fidelity) if raid_summary and raid_summary.max_fidelity is not None else None
    quality = float(raid_summary.max_quality) if raid_summary and raid_summary.max_quality is not None else (
        float(row.score) if row.score is not None else None
    )
    council_roles = list(raid_summary.roles) if raid_summary and raid_summary.roles else []
    exec_id = exec_row.execution_id if exec_row else None
    exec_consensus = float(exec_row.consensus_score) if exec_row and exec_row.consensus_score is not None else None

    # PoI cite-trail (compass bridge · best-effort)
    poi_refs = []
    try:
        from services.compass_bounty_bridge import poi_cite_trail
        trail = poi_cite_trail(db, bounty_id, top_k=3)
        poi_refs = trail.get("cited_memory_refs", [])
    except Exception as e:
        logger.warning(f"poi_cite_trail failed for cert: {e}")

    # Customer verdict from metadata
    meta = row.metadata or {}
    customer_verdict = meta.get("customer_verdict")  # 'accept' or 'reject'
    customer_rating = meta.get("customer_rating")
    customer_reason = meta.get("customer_reason")

    payload = {
        "@context": "https://nautilus.social/audit/v1",
        "@type": "AuditCertificate",
        "certificate_version": CERTIFICATE_VERSION,
        "audit_id": bounty_id,
        "task": {
            "title": row.title,
            "spec_hash": _sha256(task_spec_text),
            "spec_chars": len(task_spec_text),
        },
        "output": {
            "hash": _sha256(output_text),
            "chars": len(output_text),
            "content_excerpt": (output_text or "")[:1500],
        },
        "parties": {
            "customer": row.posted_by,
            "agent": row.claimed_by,
        },
        "scores": {
            "fidelity_score": fidelity,
            "quality_score": quality,
            "final_score": (
                round(fidelity * quality, 3)
                if fidelity is not None and quality is not None
                else None
            ),
            "exec_consensus": exec_consensus,
        },
        "council": {
            "execution_id": exec_id,
            "roles": council_roles,
            "role_count": len(council_roles),
        },
        "customer_verdict": {
            "verdict": customer_verdict,
            "rating": customer_rating,
            "reason": customer_reason,
        },
        "proof_of_impact": {
            "cited_memory_count": len(poi_refs),
            "cited_memory_refs": poi_refs[:5],
        },
        "economics": {
            "reward_nau": row.reward_nau,
            "final_status": row.status,
        },
        "issued_at": datetime.utcnow().isoformat() + "Z",
        "issuer": "nautilus-platform",
        "signing_algorithm": SIGNING_ALGORITHM,
    }

    signature = _hmac_sign(payload)
    payload["signature"] = {
        "value": signature,
        "algorithm": SIGNING_ALGORITHM,
        "key_id": "platform_v1_mvp",
    }

    return payload


def verify_certificate(cert: dict) -> dict:
    """
    Verify signature on a certificate. Returns {valid: bool, error?: str}.
    """
    if not isinstance(cert, dict) or "signature" not in cert:
        return {"valid": False, "error": "no_signature"}

    sig_block = cert.pop("signature")
    expected_sig = sig_block.get("value") if isinstance(sig_block, dict) else None
    if not expected_sig:
        return {"valid": False, "error": "malformed_signature"}

    computed_sig = _hmac_sign(cert)
    cert["signature"] = sig_block  # restore for caller

    if hmac.compare_digest(expected_sig, computed_sig):
        return {"valid": True, "algorithm": SIGNING_ALGORITHM}
    return {"valid": False, "error": "signature_mismatch"}
