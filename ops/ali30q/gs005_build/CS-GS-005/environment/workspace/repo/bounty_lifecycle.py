"""
Bounty Lifecycle Patch — adds claim/submit/verify/dispute to agent_marketplace.py
and claim_bounty/submit_bounty tools to platform.py

Run on cloud: python3 /tmp/bounty_lifecycle.py
"""
import textwrap

# ─────────────────────────────────────────────────────────────────────
# PART 1: Add bounty lifecycle endpoints to agent_marketplace.py
# ─────────────────────────────────────────────────────────────────────

MARKETPLACE_FILE = "/home/ubuntu/nautilus-mvp/phase3/backend/api/agent_marketplace.py"

BOUNTY_ENDPOINTS = '''

# ═══════════════════════════════════════════════════════════════════
# BOUNTY LIFECYCLE — claim → submit → verify → settle
# ═══════════════════════════════════════════════════════════════════

class BountySubmission(PydanticBaseModel):
    result_summary: str
    result_code: str = ""
    result_output: str = ""
    evidence_url: str = ""

class DisputeRequest(PydanticBaseModel):
    reason: str


@router.post("/bounties/{task_id}/claim", tags=["bounty"])
@limiter.limit("10/minute")
async def claim_bounty(
    request: Request,
    task_id: str,
    agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """Agent claims an open bounty. One agent per bounty."""
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(404, detail={"error": {"code": "BOUNTY_NOT_FOUND", "message": f"Bounty {task_id} not found"}})
    if task.status != "pending":
        raise HTTPException(409, detail={"error": {"code": "BOUNTY_NOT_AVAILABLE", "message": f"Bounty status is {task.status}, not pending"}})
    if not task.marketplace_open:
        raise HTTPException(400, detail={"error": {"code": "NOT_A_BOUNTY", "message": "This task is not a marketplace bounty"}})

    # Cannot claim your own bounty (check description for poster name)
    poster_name = ""
    if task.description and "[BOUNTY by " in task.description:
        try:
            poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
        except (IndexError, AttributeError):
            pass
    if poster_name and poster_name.lower() == (agent.name or "").lower():
        raise HTTPException(400, detail={"error": {"code": "SELF_CLAIM_FORBIDDEN", "message": "Cannot claim your own bounty"}})

    # Check success rate (same as existing marketplace: >= 70%)
    completed = agent.completed_tasks or 0
    failed = agent.failed_tasks or 0
    total = completed + failed
    if total >= 5 and completed / total < 0.7:
        raise HTTPException(400, detail={"error": {"code": "LOW_SUCCESS_RATE", "message": f"Success rate {completed}/{total} below 70% threshold"}})

    # Claim
    task.status = "in_progress"
    task.assigned_agent_id = agent.agent_id
    agent.current_tasks = (agent.current_tasks or 0) + 1
    db.commit()

    logger.info("Bounty %s claimed by %s (agent_id=%s)", task_id, agent.name, agent.agent_id)

    return {
        "success": True,
        "data": {
            "task_id": task_id,
            "title": task.title,
            "reward_nau": task.token_reward or 0,
            "status": "in_progress",
            "claimed_by": agent.name,
        },
        "error": None,
    }


@router.post("/bounties/{task_id}/submit", tags=["bounty"])
@limiter.limit("5/minute")
async def submit_bounty(
    request: Request,
    task_id: str,
    body: BountySubmission,
    agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """Submit bounty result. Triggers three-layer verification."""
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(404, detail={"error": {"code": "BOUNTY_NOT_FOUND", "message": f"Bounty {task_id} not found"}})
    if task.status != "in_progress":
        raise HTTPException(409, detail={"error": {"code": "NOT_IN_PROGRESS", "message": f"Bounty status is {task.status}, expected in_progress"}})
    if task.assigned_agent_id != agent.agent_id:
        raise HTTPException(403, detail={"error": {"code": "NOT_ASSIGNED", "message": "You did not claim this bounty"}})

    # Store results
    task.result_code = body.result_code[:50000] if body.result_code else ""
    task.result_output = body.result_output[:50000] if body.result_output else body.result_summary[:5000]
    task.result_error = None

    # ── Layer 1: Deterministic check (if expected_output exists) ──
    if task.expected_output and task.expected_output.strip():
        if task.result_output and task.expected_output.strip().lower() in task.result_output.strip().lower():
            task.status = "completed"
            task.audit_status = "passed"
            task.audit_reason = "Layer 1: deterministic match with expected output"
            _settle_bounty(db, task, agent, passed=True)
            db.commit()
            logger.info("Bounty %s passed Layer 1 (deterministic)", task_id)
            return _bounty_result(task, agent, "passed", "Layer 1: deterministic match")

    # ── Layer 2: LLM Audit (Rehoboam) ──
    audit_score = 0.5
    audit_reason = "auto-pass (no auditor)"
    try:
        from services.task_quality_gate import score_task_output
        scores = await score_task_output(
            task_description=task.description or task.title or "",
            task_output=body.result_summary[:3000],
            task_code=body.result_code[:3000] if body.result_code else "",
        )
        audit_score = scores.get("overall", 0.5)
        audit_reason = f"Quality gate: completeness={scores.get('completeness', '?')}, coherence={scores.get('coherence', '?')}, usefulness={scores.get('usefulness', '?')}"
    except Exception as e:
        logger.warning("Quality gate failed for %s: %s", task_id, e)
        audit_score = 0.5
        audit_reason = f"Quality gate unavailable: {e}"

    task.quality_rating = int(audit_score * 100)
    task.rating_comment = audit_reason[:500]

    if audit_score >= 0.7:
        # Auto-approve
        task.status = "completed"
        task.audit_status = "passed"
        task.audit_reason = f"Layer 2: {audit_reason}"
        _settle_bounty(db, task, agent, passed=True)
        db.commit()
        logger.info("Bounty %s passed Layer 2 (score=%.2f)", task_id, audit_score)
        return _bounty_result(task, agent, "passed", f"Layer 2: score {audit_score:.2f}")

    elif audit_score < 0.4:
        # Auto-reject
        task.status = "failed"
        task.audit_status = "flagged"
        task.audit_reason = f"Layer 2 reject: {audit_reason}"
        _settle_bounty(db, task, agent, passed=False)
        db.commit()
        logger.info("Bounty %s rejected Layer 2 (score=%.2f)", task_id, audit_score)
        return _bounty_result(task, agent, "rejected", f"Layer 2: score {audit_score:.2f}")

    else:
        # Ambiguous -> needs peer review (Layer 3)
        task.status = "needs_review"
        task.audit_status = "pending"
        task.audit_reason = f"Layer 2 ambiguous (score={audit_score:.2f}): sent to peer review"
        db.commit()
        logger.info("Bounty %s needs peer review (score=%.2f)", task_id, audit_score)
        return _bounty_result(task, agent, "needs_review", f"Layer 2: ambiguous score {audit_score:.2f}, awaiting peer review")


@router.post("/bounties/{task_id}/review", tags=["bounty"])
@limiter.limit("10/minute")
async def review_bounty(
    request: Request,
    task_id: str,
    body: ReviewRequest,
    agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """Peer review a bounty submission (Layer 3). Reviewer must not be poster or worker."""
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(404, detail={"error": {"code": "BOUNTY_NOT_FOUND", "message": f"Bounty {task_id} not found"}})
    if task.status not in ("needs_review", "disputed"):
        raise HTTPException(409, detail={"error": {"code": "NOT_REVIEWABLE", "message": f"Bounty status {task.status} is not reviewable"}})
    if task.assigned_agent_id == agent.agent_id:
        raise HTTPException(400, detail={"error": {"code": "WORKER_CANNOT_REVIEW", "message": "Worker cannot review their own submission"}})

    # Check reviewer isn't the poster
    poster_name = ""
    if task.description and "[BOUNTY by " in task.description:
        try:
            poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
        except (IndexError, AttributeError):
            pass
    if poster_name and poster_name.lower() == (agent.name or "").lower():
        raise HTTPException(400, detail={"error": {"code": "POSTER_CANNOT_REVIEW", "message": "Bounty poster cannot review their own bounty"}})

    import json as _json
    passed = body.passed if hasattr(body, "passed") else True
    review_data = {
        "reviewer_agent_id": agent.agent_id,
        "reviewer_name": agent.name,
        "passed": passed,
        "reason": body.reason if hasattr(body, "reason") else "",
        "reviewed_at": datetime.utcnow().isoformat(),
    }

    # Settle based on review
    worker = db.query(Agent).filter(Agent.agent_id == task.assigned_agent_id).first()

    if passed:
        task.status = "completed"
        task.audit_status = "peer_reviewed"
        task.audit_reason = _json.dumps(review_data, ensure_ascii=False)
        if worker:
            _settle_bounty(db, task, worker, passed=True)
    else:
        task.status = "failed"
        task.audit_status = "peer_rejected"
        task.audit_reason = _json.dumps(review_data, ensure_ascii=False)
        if worker:
            _settle_bounty(db, task, worker, passed=False)

    # Reviewer gets 50 points for honest work
    agent.total_earnings = (agent.total_earnings or 0) + 50
    db.commit()

    logger.info("Bounty %s peer reviewed by %s: passed=%s", task_id, agent.name, passed)
    return {
        "success": True,
        "data": {"task_id": task_id, "review": review_data, "final_status": task.status},
        "error": None,
    }


@router.post("/bounties/{task_id}/dispute", tags=["bounty"])
@limiter.limit("3/minute")
async def dispute_bounty(
    request: Request,
    task_id: str,
    body: DisputeRequest,
    agent = Depends(_get_agent_by_key),
    db: Session = Depends(get_db),
):
    """Poster disputes an auto-approved bounty. Sends to peer review (Layer 3)."""
    task = db.query(AcademicTask).filter(AcademicTask.task_id == task_id).first()
    if not task:
        raise HTTPException(404, detail={"error": {"code": "BOUNTY_NOT_FOUND", "message": f"Bounty {task_id} not found"}})
    if task.status != "completed":
        raise HTTPException(409, detail={"error": {"code": "NOT_DISPUTABLE", "message": "Only completed bounties can be disputed"}})

    # Only poster can dispute
    poster_name = ""
    if task.description and "[BOUNTY by " in task.description:
        try:
            poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
        except (IndexError, AttributeError):
            pass
    if not poster_name or poster_name.lower() != (agent.name or "").lower():
        raise HTTPException(403, detail={"error": {"code": "NOT_POSTER", "message": "Only the bounty poster can dispute"}})

    # Revert to needs_review
    task.status = "disputed"
    task.audit_status = "disputed"
    task.audit_reason = f"Disputed by poster {agent.name}: {body.reason[:500]}"
    db.commit()

    logger.info("Bounty %s disputed by poster %s: %s", task_id, agent.name, body.reason[:100])
    return {
        "success": True,
        "data": {"task_id": task_id, "status": "disputed", "message": "Bounty sent to peer review"},
        "error": None,
    }


def _settle_bounty(db, task, worker_agent, passed: bool):
    """Settle NAU: transfer escrowed reward to worker on success, refund poster on failure."""
    reward = task.token_reward or 0
    if reward <= 0:
        return

    if passed:
        # Pay worker
        worker_agent.total_earnings = (worker_agent.total_earnings or 0) + int(reward)
        worker_agent.completed_tasks = (worker_agent.completed_tasks or 0) + 1
        if worker_agent.current_tasks and worker_agent.current_tasks > 0:
            worker_agent.current_tasks -= 1
        # Reputation boost
        worker_agent.reputation_score = min(100.0, (worker_agent.reputation_score or 50.0) + 1.0)

        # Update survival scores
        try:
            from services.survival_service import SurvivalService
            task_duration = (datetime.utcnow() - (task.created_at or datetime.utcnow())).total_seconds()
            SurvivalService.update_scores_on_task_completion(
                db=db,
                agent_id=worker_agent.agent_id,
                task_reward=float(reward),
                task_duration_seconds=task_duration,
                published_duration_seconds=3600.0,
                task_rating=task.quality_rating,
            )
            SurvivalService.record_income(
                db=db,
                agent_id=worker_agent.agent_id,
                amount=reward,
                category="bounty_reward",
                task_id=task.task_id,
            )
        except Exception as e:
            logger.warning("Survival update failed for bounty %s: %s", task.task_id, e)

        # Emit event
        try:
            from services.event_bus import emit, Events
            import asyncio
            asyncio.ensure_future(emit("task.completed", {
                "task_id": task.task_id,
                "agent_id": worker_agent.agent_id,
                "reward": reward,
                "task_type": task.task_type,
                "bounty": True,
            }))
        except Exception:
            pass

        logger.info("Bounty %s settled: %s NAU -> %s", task.task_id, reward, worker_agent.name)

    else:
        # Refund poster (find poster by name in description)
        poster_name = ""
        if task.description and "[BOUNTY by " in task.description:
            try:
                poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
            except (IndexError, AttributeError):
                pass
        if poster_name:
            poster = db.query(Agent).filter(Agent.name == poster_name).first()
            if poster:
                poster.total_earnings = (poster.total_earnings or 0) + int(reward)
                logger.info("Bounty %s refunded: %s NAU -> poster %s", task.task_id, reward, poster_name)

        # Worker penalty
        worker_agent.failed_tasks = (worker_agent.failed_tasks or 0) + 1
        if worker_agent.current_tasks and worker_agent.current_tasks > 0:
            worker_agent.current_tasks -= 1
        worker_agent.reputation_score = max(0.0, (worker_agent.reputation_score or 50.0) - 2.0)


def _bounty_result(task, agent, verdict: str, reason: str) -> dict:
    """Standard bounty result response."""
    return {
        "success": True,
        "data": {
            "task_id": task.task_id,
            "title": task.title,
            "verdict": verdict,
            "reason": reason,
            "reward_nau": task.token_reward or 0,
            "quality_score": task.quality_rating,
            "worker": agent.name,
            "status": task.status,
        },
        "error": None,
    }
'''


# ─────────────────────────────────────────────────────────────────────
# PART 2: Add claim_bounty / submit_bounty tools to platform.py
# ─────────────────────────────────────────────────────────────────────

PLATFORM_FILE = "/home/ubuntu/nautilus-agent/nautilus_agent/tools/platform.py"

BOUNTY_TOOLS = '''

class ClaimBountyTool(Tool):
    name = "claim_bounty"
    description = "Claim an open bounty to work on it. Input: bounty task_id (e.g. bounty-seed-arc01)"
    params = {"input": "bounty task_id"}
    required_params = ["input"]

    def run(self, input_text: str) -> str:
        import httpx
        task_id = input_text.strip()
        if not task_id:
            return "Error: provide bounty task_id"
        agent_token = self._get_agent_key()
        try:
            resp = httpx.post(
                f"{NAUTILUS_API}/api/agent-market/bounties/{task_id}/claim",
                headers={"X-Agent-Key": agent_token},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", resp.json())
                return "Claimed: %s (%s NAU) - now work on it and submit results" % (
                    data.get("title", task_id), data.get("reward_nau", "?"))
            return "Error %s: %s" % (resp.status_code, resp.text[:300])
        except Exception as e:
            return "Error: %s" % e

    @staticmethod
    def _get_agent_key():
        import os
        key = os.getenv("AGENT_TOKEN", os.getenv("NAUTILUS_AGENT_TOKEN", ""))
        if not key:
            data_dir = os.getenv("NAUTILUS_DATA_DIR", os.path.expanduser("~/.nautilus-agent"))
            agent_name = os.getenv("AGENT_NAME", "nautilus")
            for path in [os.path.join(data_dir, agent_name, "agent_key.txt"),
                         os.path.join(data_dir, "agent_key.txt")]:
                try:
                    key = open(path).read().strip()
                    if key:
                        break
                except FileNotFoundError:
                    pass
        return key


class SubmitBountyTool(Tool):
    name = "submit_bounty"
    description = "Submit your work for a claimed bounty. Format: task_id|result_summary|result_code|evidence_url"
    params = {"input": "task_id|result_summary[|result_code][|evidence_url]"}
    required_params = ["input"]

    def run(self, input_text: str) -> str:
        import httpx
        parts = input_text.split("|")
        if len(parts) < 2:
            return "Error: format is task_id|result_summary[|result_code][|evidence_url]"
        task_id = parts[0].strip()
        summary = parts[1].strip()
        code = parts[2].strip() if len(parts) > 2 else ""
        evidence = parts[3].strip() if len(parts) > 3 else ""

        agent_token = ClaimBountyTool._get_agent_key()
        try:
            resp = httpx.post(
                f"{NAUTILUS_API}/api/agent-market/bounties/{task_id}/submit",
                json={
                    "result_summary": summary,
                    "result_code": code,
                    "result_output": summary,
                    "evidence_url": evidence,
                },
                headers={"X-Agent-Key": agent_token},
                timeout=30,
            )
            if resp.status_code == 200:
                data = resp.json().get("data", resp.json())
                return "Submitted: %s - verdict=%s, quality=%s, reward=%s NAU" % (
                    task_id, data.get("verdict", "?"), data.get("quality_score", "?"),
                    data.get("reward_nau", "?"))
            return "Error %s: %s" % (resp.status_code, resp.text[:300])
        except Exception as e:
            return "Error: %s" % e
'''


# ─────────────────────────────────────────────────────────────────────
# PART 3: Register new tools in agent.py
# ─────────────────────────────────────────────────────────────────────

AGENT_FILE = "/home/ubuntu/nautilus-agent/nautilus_agent/agent.py"


def apply():
    """Apply all patches."""
    import os

    # ── Patch 1: marketplace endpoints ──
    with open(MARKETPLACE_FILE, "r") as f:
        content = f.read()

    if "claim_bounty" not in content:
        # Ensure imports exist
        if "from datetime import datetime" not in content:
            content = "from datetime import datetime\n" + content
        content += BOUNTY_ENDPOINTS
        with open(MARKETPLACE_FILE, "w") as f:
            f.write(content)
        print("PATCH 1 OK: bounty lifecycle endpoints added")
    else:
        print("PATCH 1 SKIP: already present")

    # ── Patch 2: agent tools ──
    with open(PLATFORM_FILE, "r") as f:
        content = f.read()

    if "ClaimBountyTool" not in content:
        content += BOUNTY_TOOLS
        with open(PLATFORM_FILE, "w") as f:
            f.write(content)
        print("PATCH 2 OK: bounty tools added")
    else:
        print("PATCH 2 SKIP: already present")

    # ── Patch 3: register tools ──
    with open(AGENT_FILE, "r") as f:
        content = f.read()

    if "ClaimBountyTool" not in content:
        # Add to import
        old_import = "            CreateBountyTool, BrowseBountiesTool,"
        new_import = "            CreateBountyTool, BrowseBountiesTool,\n            ClaimBountyTool, SubmitBountyTool,"
        content = content.replace(old_import, new_import, 1)

        # Add to registration
        old_reg = "        registry.register(BrowseBountiesTool())"
        new_reg = "        registry.register(BrowseBountiesTool())\n        registry.register(ClaimBountyTool())\n        registry.register(SubmitBountyTool())"
        content = content.replace(old_reg, new_reg, 1)

        with open(AGENT_FILE, "w") as f:
            f.write(content)
        print("PATCH 3 OK: tools registered in agent.py")
    else:
        print("PATCH 3 SKIP: already present")

    # ── Verify syntax ──
    print("\nVerifying syntax...")
    import subprocess
    for label, path in [
        ("marketplace", MARKETPLACE_FILE),
        ("platform tools", PLATFORM_FILE),
        ("agent", AGENT_FILE),
    ]:
        result = subprocess.run(
            ["python3", "-c", f"import py_compile; py_compile.compile('{path}', doraise=True)"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  {label}: OK")
        else:
            print(f"  {label}: FAIL\n{result.stderr[:500]}")

    print("\nDone. Restart backend + agents to activate.")


if __name__ == "__main__":
    apply()
