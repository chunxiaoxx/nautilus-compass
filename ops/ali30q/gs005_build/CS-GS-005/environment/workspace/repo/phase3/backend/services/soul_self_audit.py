"""Soul self-audit · synchronous fidelity check + signed cert for a Soul output.

Increment 1 (platform-run fidelity · NOT the real V5/Kairos council · that is
Increment 2). Creates a finalized audit-subject bounty + raid_execution +
raid_vote so the existing generate_certificate() can sign a JSON-LD cert.
"""
from __future__ import annotations
from typing import Callable, Optional


def run_self_audit(
    db,
    task_spec: str,
    output: str,
    bounty_id: str,
    quality_score: float = 0.8,
    _check_fidelity: Optional[Callable] = None,
    _generate_certificate: Optional[Callable] = None,
    _verify_certificate: Optional[Callable] = None,
    _persist: Optional[Callable] = None,
) -> dict:
    """Synchronous self-audit: fidelity -> persist rows -> sign cert -> verify.

    Returns {success, bounty_id, fidelity_score, cert, cert_valid} or
    {success: False, stage, detail, bounty_id} on cert error.
    """
    if _check_fidelity is None:
        from services.raid_fidelity_checker import check_fidelity as _check_fidelity
    if _generate_certificate is None:
        from services.audit_cert_generator import generate_certificate as _generate_certificate
    if _verify_certificate is None:
        from services.audit_cert_generator import verify_certificate as _verify_certificate
    if _persist is None:
        from services.soul_self_audit import persist_self_audit_rows as _persist

    fid = float(_check_fidelity(task_spec, output).get("fidelity_score") or 0.0)
    _persist(db, bounty_id, task_spec, output, fidelity_score=fid, quality_score=quality_score)
    cert = _generate_certificate(db, bounty_id)
    if isinstance(cert, dict) and cert.get("error"):
        return {"success": False, "stage": "cert", "detail": cert, "bounty_id": bounty_id}
    valid = bool(_verify_certificate(cert).get("valid"))
    return {
        "success": valid, "bounty_id": bounty_id,
        "fidelity_score": fid, "cert": cert, "cert_valid": valid,
    }


def persist_self_audit_rows(db, bounty_id, task_spec, output, fidelity_score, quality_score=0.8):
    """Create finalized audit-subject bounty + raid_execution + raid_vote so
    generate_certificate() can sign a cert. Increment 1 · platform-run fidelity.
    Returns execution_id.
    """
    from sqlalchemy import text
    import uuid
    db.execute(text(
        "INSERT INTO platform_bounties "
        "(bounty_id, title, description, reward_nau, task_type, status, posted_by, "
        " channel, source, posted_at, result, score, metadata) "
        "VALUES (:b, :title, :desc, 0, 'platform_meta', 'completed', 'soul', "
        " 'soul-self-audit', 'api.soul.self_audit', now(), :result, :score, "
        " '{\"self_audit\": true}'::jsonb) ON CONFLICT (bounty_id) DO NOTHING"
    ), {"b": bounty_id, "title": f"soul self-audit · {task_spec[:80]}",
        "desc": task_spec[:2000], "result": output[:8000], "score": quality_score})
    exec_id = f"selfaudit-{uuid.uuid4().hex[:12]}"
    db.execute(text(
        "INSERT INTO raid_executions (execution_id, task_id, raid_level, status, consensus_score, created_at) "
        "VALUES (:e, :t, 1, 'completed', :c, now()) ON CONFLICT (execution_id) DO NOTHING"
    ), {"e": exec_id, "t": bounty_id, "c": round(quality_score * fidelity_score, 3)})
    db.execute(text(
        "INSERT INTO raid_votes (execution_id, agent_role, fidelity_score, quality_score) "
        "VALUES (:e, 'platform-self-audit', :f, :q)"
    ), {"e": exec_id, "f": fidelity_score, "q": quality_score})
    db.commit()
    return exec_id


def attach_cert_to_pr(pr_url, cert, base_dir, _runner=None):
    """Post the signed cert as a comment on the draft PR. Returns True on success."""
    import json, subprocess
    if _runner is None:
        _runner = subprocess.run
    body = (
        "## Nautilus Audit Certificate\n\n"
        "- audit_id: " + str(cert.get("audit_id")) + "\n"
        "- verify: GET /api/v1/audit/" + str(cert.get("audit_id")) + "/verify\n\n"
        "```json\n" + json.dumps(cert, ensure_ascii=False, indent=2)[:6000] + "\n```"
    )
    r = _runner(["gh", "pr", "comment", pr_url, "--body", body],
                cwd=base_dir, capture_output=True, text=True)
    return getattr(r, "returncode", 1) == 0


def _commit_diff(base_dir, sha, _runner=None):
    """Return the diff of a commit as text (real generated output for fidelity)."""
    import subprocess
    if _runner is None:
        _runner = subprocess.run
    if not sha:
        return ""
    r = _runner(["git", "-C", base_dir, "show", "--format=", "--no-color", sha],
                capture_output=True, text=True)
    return (getattr(r, "stdout", "") or "")[:8000]


def ship_with_self_audit(task, base_dir, branch, commit_msg, db, cycle_id=None,
                         _ship_to_draft_pr=None, _run_self_audit=None,
                         _attach=None, _diff=None):
    """Ship a Soul draft PR, then self-audit the real diff + attach a signed cert.

    Returns ship_to_draft_pr result augmented with fidelity_score, cert,
    cert_valid, cert_attached. Increment 1 · platform-run fidelity.
    """
    if _ship_to_draft_pr is None:
        from services.soul_service import ship_to_draft_pr as _ship_to_draft_pr
    if _run_self_audit is None:
        _run_self_audit = run_self_audit
    if _attach is None:
        _attach = attach_cert_to_pr
    if _diff is None:
        _diff = _commit_diff

    shipped = _ship_to_draft_pr(task, base_dir, branch, commit_msg, cycle_id=cycle_id)
    if not shipped.get("success"):
        return shipped
    cid = cycle_id or shipped.get("cycle_id") or "cycle"
    output = _diff(base_dir, shipped.get("commit")) or task
    sa = _run_self_audit(db, task, output, bounty_id=f"soul-audit-{cid}")
    shipped["fidelity_score"] = sa.get("fidelity_score")
    shipped["cert"] = sa.get("cert")
    shipped["cert_valid"] = sa.get("cert_valid")
    if sa.get("cert_valid") and shipped.get("pr_url"):
        shipped["cert_attached"] = _attach(shipped["pr_url"], sa["cert"], base_dir)
    return shipped
