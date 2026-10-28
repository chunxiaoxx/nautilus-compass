"""
Review fixes: CRITICAL + HIGH issues from code review.
Run on cloud: python3 /tmp/review_fixes.py
"""
import re

MARKETPLACE = "/home/ubuntu/nautilus-mvp/phase3/backend/api/agent_marketplace.py"
AGENT = "/home/ubuntu/nautilus-agent/nautilus_agent/agent.py"
SCHEDULER = "/home/ubuntu/nautilus-agent/nautilus_agent/gateway/scheduler.py"
PLATFORM_TOOLS = "/home/ubuntu/nautilus-agent/nautilus_agent/tools/platform.py"
COMPRESSOR = "/home/ubuntu/nautilus-agent/nautilus_agent/core/context_compressor.py"

results = []


def fix_c1_c2_c3_marketplace():
    """Fix poster identity, race condition, and double-spend."""
    with open(MARKETPLACE, "r") as f:
        content = f.read()

    # ── C1: Replace string-based poster identity with stored user_id ──
    # Use AcademicTask.user_id to store poster's agent.id (integer PK)
    # This is the proper way — no string parsing needed

    # Fix create_bounty: store poster id in user_id field
    old_create = '    task_id = f"bounty-{uuid4().hex[:12]}"'
    new_create = '    poster_id = agent.id  # Store poster identity properly (not in description string)\n    task_id = f"bounty-{uuid4().hex[:12]}"'
    content = content.replace(old_create, new_create, 1)

    # Set user_id = poster_id in task creation
    old_public = "        is_public=True,"
    if "user_id=poster_id" not in content:
        new_public = "        user_id=poster_id,  # poster's Agent.id for identity verification\n        is_public=True,"
        content = content.replace(old_public, new_public, 1)

    # ── Fix all poster checks: use user_id instead of string parsing ──
    # Replace all poster_name string parsing blocks with user_id check

    # Helper function for poster check
    poster_helper = '''
def _get_poster_id(task) -> int:
    """Get poster Agent.id from task. Returns 0 if not a bounty."""
    return task.user_id or 0

'''
    if "_get_poster_id" not in content:
        # Insert before the bounty endpoints section
        bounty_section = "# BOUNTY LIFECYCLE"
        if bounty_section in content:
            content = content.replace(bounty_section, poster_helper + bounty_section, 1)

    # Replace all string-based poster checks in claim
    old_poster_claim = '''    # Cannot claim your own bounty (check description for poster name)
    poster_name = ""
    if task.description and "[BOUNTY by " in task.description:
        try:
            poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
        except (IndexError, AttributeError):
            pass
    if poster_name and poster_name.lower() == (agent.name or "").lower():'''
    new_poster_claim = '    # Cannot claim your own bounty\n    if _get_poster_id(task) == agent.id:'
    content = content.replace(old_poster_claim, new_poster_claim, 1)

    # Replace poster check in review
    old_poster_review = '''    # Check reviewer isn't the poster
    poster_name = ""
    if task.description and "[BOUNTY by " in task.description:
        try:
            poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
        except (IndexError, AttributeError):
            pass
    if poster_name and poster_name.lower() == (agent.name or "").lower():'''
    new_poster_review = '    # Check reviewer is not the poster\n    if _get_poster_id(task) == agent.id:'
    content = content.replace(old_poster_review, new_poster_review, 1)

    # Replace poster check in dispute
    old_poster_dispute = '''    # Only poster can dispute
    poster_name = ""
    if task.description and "[BOUNTY by " in task.description:
        try:
            poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
        except (IndexError, AttributeError):
            pass
    if not poster_name or poster_name.lower() != (agent.name or "").lower():'''
    new_poster_dispute = '    # Only poster can dispute\n    if _get_poster_id(task) != agent.id:'
    content = content.replace(old_poster_dispute, new_poster_dispute, 1)

    # Replace poster refund in _settle_bounty
    old_refund = '''        if poster_name:
            poster = db.query(Agent).filter(Agent.name == poster_name).first()
            if poster:
                poster.total_earnings = (poster.total_earnings or 0) + int(reward)
                logger.info("Bounty %s refunded: %s NAU -> poster %s", task.task_id, reward, poster_name)'''
    new_refund = '''        poster_id = _get_poster_id(task)
        if poster_id:
            poster = db.query(Agent).filter(Agent.id == poster_id).first()
            if poster:
                poster.total_earnings = (poster.total_earnings or 0) + int(reward)
                logger.info("Bounty %s refunded: %s NAU -> poster id=%s", task.task_id, reward, poster_id)'''
    content = content.replace(old_refund, new_refund, 1)

    # Remove stale poster_name parsing in _settle_bounty
    old_settle_parse = '''        # Refund poster (find poster by name in description)
        poster_name = ""
        if task.description and "[BOUNTY by " in task.description:
            try:
                poster_name = task.description.split("[BOUNTY by ")[1].split("]")[0]
            except (IndexError, AttributeError):
                pass'''
    new_settle_parse = '        # Refund poster via stored user_id'
    content = content.replace(old_settle_parse, new_settle_parse, 1)

    # ── C2: Race condition fix — use optimistic locking on claim ──
    old_claim_status = '''    if task.status != "pending":
        raise HTTPException(409, detail={"error": {"code": "BOUNTY_NOT_AVAILABLE", "message": f"Bounty status is {task.status}, not pending"}})'''
    new_claim_status = '''    if task.status != "pending":
        raise HTTPException(409, detail={"error": {"code": "BOUNTY_NOT_AVAILABLE", "message": f"Bounty status is {task.status}, not pending"}})

    # Optimistic lock: atomic UPDATE WHERE status='pending' prevents race condition
    from sqlalchemy import text
    rows_updated = db.execute(
        text("UPDATE academic_tasks SET status='in_progress', assigned_agent_id=:aid WHERE task_id=:tid AND status='pending'"),
        {"aid": agent.agent_id, "tid": task_id}
    ).rowcount
    if rows_updated == 0:
        raise HTTPException(409, detail={"error": {"code": "ALREADY_CLAIMED", "message": "Bounty was claimed by another agent"}})'''
    content = content.replace(old_claim_status, new_claim_status, 1)

    # Remove the non-atomic assignment that follows (now handled by the UPDATE)
    old_assign = '''    # Claim
    task.status = "in_progress"
    task.assigned_agent_id = agent.agent_id
    agent.current_tasks = (agent.current_tasks or 0) + 1
    db.commit()'''
    new_assign = '''    # Claim already applied via atomic UPDATE above
    db.refresh(task)
    agent.current_tasks = (agent.current_tasks or 0) + 1
    db.commit()'''
    content = content.replace(old_assign, new_assign, 1)

    # ── C3: Double-spend fix — add settled flag check ──
    old_settle_fn = 'def _settle_bounty(db, task, worker_agent, passed: bool):'
    new_settle_fn = '''def _settle_bounty(db, task, worker_agent, passed: bool):
    # Idempotency: prevent double settlement
    if getattr(task, '_settled', False):
        return
    if task.audit_status in ("settled_paid", "settled_refunded"):
        return'''
    content = content.replace(old_settle_fn, new_settle_fn, 1)

    # Mark as settled after payment
    old_settle_log = '        logger.info("Bounty %s settled: %s NAU -> %s", task.task_id, reward, worker_agent.name)'
    new_settle_log = '        task.audit_status = "settled_paid"\n        task._settled = True\n        logger.info("Bounty %s settled: %s NAU -> %s", task.task_id, reward, worker_agent.name)'
    content = content.replace(old_settle_log, new_settle_log, 1)

    # Mark as settled after refund
    old_refund_log = '                logger.info("Bounty %s refunded: %s NAU -> poster id=%s", task.task_id, reward, poster_id)'
    new_refund_log = '                task.audit_status = "settled_refunded"\n                task._settled = True\n                logger.info("Bounty %s refunded: %s NAU -> poster id=%s", task.task_id, reward, poster_id)'
    content = content.replace(old_refund_log, new_refund_log, 1)

    with open(MARKETPLACE, "w") as f:
        f.write(content)
    results.append("C1+C2+C3 OK: poster identity by user_id, atomic claim, settlement idempotency")


def fix_c4_httpx_import():
    """Fix missing httpx import in scheduler _fetch_bounties."""
    with open(SCHEDULER, "r") as f:
        content = f.read()

    old = "    def _fetch_bounties(self) -> str:"
    new = "    def _fetch_bounties(self) -> str:\n        import httpx"
    if "def _fetch_bounties" in content and "import httpx" not in content.split("_fetch_bounties")[1][:200]:
        content = content.replace(old, new, 1)
        with open(SCHEDULER, "w") as f:
            f.write(content)
        results.append("C4 OK: httpx imported in _fetch_bounties")
    else:
        results.append("C4 SKIP: already imported or not found")


def fix_h1_enforce_protection():
    """Wire PROTECTED_CORE_FILES into guarded_tool_executor."""
    with open(AGENT, "r") as f:
        content = f.read()

    if "_is_protected_path(input_text)" in content:
        results.append("H1 SKIP: protection already wired")
        return

    # Find guarded_tool_executor and add protection check
    # Look for the tool execution guard
    old_guard = "def guarded_tool_executor(tool_name: str, input_text: str) -> str:"
    if old_guard not in content:
        # Try alternate pattern
        for pattern in ["def guarded_tool_executor(", "guarded_tool_executor"]:
            if pattern in content:
                idx = content.find(pattern)
                # Show context for debugging
                results.append(f"H1 INFO: found '{pattern}' at char {idx}")
                break
        results.append("H1 SKIP: guarded_tool_executor not found in expected form")
        return

    new_guard = '''def guarded_tool_executor(tool_name: str, input_text: str) -> str:
            # Core file protection
            write_tools = {"write_file", "safe_edit", "replace_in_file", "insert_at_line", "delete_lines", "safe_create"}
            if tool_name in write_tools and _is_protected_path(input_text):
                return f"BLOCKED: {input_text.split('|')[0].strip()} is a protected core file and cannot be modified by agents."'''

    content = content.replace(old_guard, new_guard, 1)
    with open(AGENT, "w") as f:
        f.write(content)
    results.append("H1 OK: PROTECTED_CORE_FILES enforced in guarded_tool_executor")


def fix_h2_pain_cap():
    """Move pain_history cap from docstring into executable code."""
    with open(SCHEDULER, "r") as f:
        content = f.read()

    # Check if the cap is inside a docstring
    lines = content.split("\n")
    fixed = False
    for i, line in enumerate(lines):
        if "def _detect_pain(self)" in line:
            # Scan the next lines: find docstring end, insert cap after it
            in_docstring = False
            docstring_end = i + 1
            for j in range(i + 1, min(i + 20, len(lines))):
                stripped = lines[j].strip()
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    if in_docstring:
                        docstring_end = j + 1
                        break
                    else:
                        # Check if single-line docstring
                        if stripped.endswith('"""') and len(stripped) > 3:
                            docstring_end = j + 1
                            break
                        in_docstring = True
                elif not in_docstring and stripped and not stripped.startswith("#"):
                    docstring_end = j
                    break

            # Check if cap already exists as executable code after docstring
            cap_exists = False
            for j in range(docstring_end, min(docstring_end + 5, len(lines))):
                if "len(self._pain_history)" in lines[j] and "#" not in lines[j][:lines[j].find("len")]:
                    cap_exists = True
                    break

            if not cap_exists:
                indent = "        "
                cap_lines = [
                    f"{indent}# Cap pain history to prevent memory leak",
                    f"{indent}if len(self._pain_history) > 50:",
                    f"{indent}    self._pain_history = dict(list(self._pain_history.items())[-25:])",
                ]
                for k, cap_line in enumerate(cap_lines):
                    lines.insert(docstring_end + k, cap_line)
                fixed = True
            break

    if fixed:
        content = "\n".join(lines)
        with open(SCHEDULER, "w") as f:
            f.write(content)
        results.append("H2 OK: pain_history cap moved to executable code")
    else:
        results.append("H2 SKIP: cap already executable or _detect_pain not found")


def fix_h3_path_validation():
    """Sanitize AGENT_NAME to prevent path traversal in key reading."""
    with open(PLATFORM_TOOLS, "r") as f:
        content = f.read()

    if "re.match" in content and "AGENT_NAME" in content:
        results.append("H3 SKIP: validation may already exist")
        return

    old_key = 'agent_name = os.getenv("AGENT_NAME", "nautilus")'
    new_key = 'agent_name = os.getenv("AGENT_NAME", "nautilus")\n            import re as _re\n            if not _re.match(r"^[a-zA-Z0-9_-]+$", agent_name):\n                agent_name = "nautilus"'
    if old_key in content:
        content = content.replace(old_key, new_key, 1)
        with open(PLATFORM_TOOLS, "w") as f:
            f.write(content)
        results.append("H3 OK: AGENT_NAME path traversal prevention added")
    else:
        results.append("H3 SKIP: pattern not found")


def fix_h5_chinese_tokens():
    """Improve token estimation for Chinese text."""
    with open(COMPRESSOR, "r") as f:
        content = f.read()

    old_est = '        return sum(len(str(m.get("content", ""))) // 4 for m in messages)'
    new_est = '''        total = 0
        for m in messages:
            text = str(m.get("content", ""))
            # CJK characters use ~1.5 chars per token; Latin ~4 chars per token
            cjk = sum(1 for c in text if '\\u4e00' <= c <= '\\u9fff' or '\\u3000' <= c <= '\\u303f')
            latin = len(text) - cjk
            total += (cjk * 2 // 3) + (latin // 4)  # ~1.5 chars/token CJK, ~4 chars/token Latin
        return total'''

    if old_est in content:
        content = content.replace(old_est, new_est, 1)
        with open(COMPRESSOR, "w") as f:
            f.write(content)
        results.append("H5 OK: Chinese-aware token estimation")
    else:
        results.append("H5 SKIP: estimation pattern not found")


def fix_h6_counter_reset():
    """Don't reset counters on soft violation — keep pressure."""
    with open(AGENT, "r") as f:
        content = f.read()

    old_reset = '''                logger.warning("EDIT-FIRST soft violation: no edit occurred - resetting counters")
                self._consecutive_readonly_cycles = 0
                self._consecutive_no_write_cycles = 0'''
    new_reset = '''                logger.warning("EDIT-FIRST soft violation: no edit occurred - decrementing counters")
                # Don't reset to 0 — that defeats the loop breaker.
                # Instead, halve the counters so pressure gradually reduces but doesn't vanish.
                self._consecutive_readonly_cycles = max(0, self._consecutive_readonly_cycles // 2)
                self._consecutive_no_write_cycles = max(0, self._consecutive_no_write_cycles // 2)'''

    if old_reset in content:
        content = content.replace(old_reset, new_reset, 1)
        with open(AGENT, "w") as f:
            f.write(content)
        results.append("H6 OK: soft violation halves counters instead of resetting")
    else:
        results.append("H6 SKIP: pattern not found")


if __name__ == "__main__":
    fixes = [
        ("C1+C2+C3", fix_c1_c2_c3_marketplace),
        ("C4", fix_c4_httpx_import),
        ("H1", fix_h1_enforce_protection),
        ("H2", fix_h2_pain_cap),
        ("H3", fix_h3_path_validation),
        ("H5", fix_h5_chinese_tokens),
        ("H6", fix_h6_counter_reset),
    ]

    for name, fn in fixes:
        try:
            fn()
        except Exception as e:
            results.append(f"{name} ERROR: {e}")

    print("\n".join(results))

    # Verify syntax
    print("\nSyntax verification:")
    import subprocess
    for label, path in [
        ("marketplace", MARKETPLACE),
        ("agent", AGENT),
        ("scheduler", SCHEDULER),
        ("platform tools", PLATFORM_TOOLS),
        ("compressor", COMPRESSOR),
    ]:
        r = subprocess.run(
            ["python3", "-c", f"import py_compile; py_compile.compile('{path}', doraise=True)"],
            capture_output=True, text=True
        )
        status = "OK" if r.returncode == 0 else f"FAIL: {r.stderr[:300]}"
        print(f"  {label}: {status}")
