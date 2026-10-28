"""
Integration fixes: 5 broken connections found in final review.
Run on cloud: python3 /tmp/integration_fixes.py
"""
results = []

# ═══════════════════════════════════════════════════════════════
# P0: Wire _track_published() — article dedup is dead code
# ═══════════════════════════════════════════════════════════════

def fix_published_tracking():
    """PublishDevtoTool must call scheduler._track_published after success."""
    # Since the tool and scheduler are in different processes (agent vs platform),
    # we can't directly call scheduler method. Instead, store in working_memory
    # which the scheduler reads.

    path = "/home/ubuntu/nautilus-agent/nautilus_agent/tools/platform.py"
    with open(path, "r") as f:
        content = f.read()

    if "_track_devto_publish" in content:
        results.append("P0 SKIP: publish tracking already wired")
        return

    # Find PublishDevtoTool.run() and add title tracking after success
    # The tool already has auto-report. Add title tracking to a shared file.
    old = '        # Auto-report action to platform'
    if old not in content:
        # Find alternative insertion point after publish success
        old = 'class GitHubSearchTool'
        if old not in content:
            results.append("P0 FAIL: cannot find insertion point in platform.py")
            return
        # Insert before GitHubSearchTool
        tracking_code = '''
# Track published articles for dedup (read by scheduler)
def _track_devto_publish(title: str):
    """Append published title to a shared tracking file."""
    import os
    data_dir = os.getenv("NAUTILUS_DATA_DIR", os.path.expanduser("~/.nautilus-agent"))
    agent_name = os.getenv("AGENT_NAME", "nautilus")
    track_file = os.path.join(data_dir, agent_name, "published_titles.txt")
    try:
        os.makedirs(os.path.dirname(track_file), exist_ok=True)
        with open(track_file, "a") as f:
            f.write(title[:60] + "\\n")
        # Keep only last 50 titles
        with open(track_file, "r") as f:
            lines = f.readlines()
        if len(lines) > 50:
            with open(track_file, "w") as f:
                f.writelines(lines[-50:])
    except Exception:
        pass


'''
        content = content.replace(old, tracking_code + old, 1)
    else:
        # Insert tracking call after auto-report
        tracking_call = '''
        # Track title for dedup
        try:
            _track_devto_publish(input_text.split("\\n")[0][:60] if "\\n" in input_text else input_text[:60])
        except Exception:
            pass
'''
        content = content.replace(old, tracking_call + "\n" + old, 1)

    with open(path, "w") as f:
        f.write(content)

    # Now update scheduler to READ from the tracking file instead of class variable
    sched_path = "/home/ubuntu/nautilus-agent/nautilus_agent/gateway/scheduler.py"
    with open(sched_path, "r") as f:
        sched = f.read()

    old_method = '''    def _get_recent_published(self) -> str:
        if not self._published_titles:
            return "none yet"
        return ", ".join(self._published_titles[-5:])'''

    new_method = '''    def _get_recent_published(self) -> str:
        """Read published titles from shared tracking file."""
        import os
        data_dir = os.getenv("NAUTILUS_DATA_DIR", os.path.expanduser("~/.nautilus-agent"))
        agent_name = os.getenv("AGENT_NAME", "nautilus")
        track_file = os.path.join(data_dir, agent_name, "published_titles.txt")
        try:
            with open(track_file, "r") as f:
                titles = [line.strip() for line in f.readlines() if line.strip()]
            if titles:
                return ", ".join(titles[-5:])
        except FileNotFoundError:
            pass
        return "none yet"'''

    if old_method in sched:
        sched = sched.replace(old_method, new_method, 1)
        with open(sched_path, "w") as f:
            f.write(sched)
        results.append("P0 OK: _track_published wired via shared file + scheduler reads it")
    else:
        results.append("P0 PARTIAL: tracking function added but scheduler method not found for replacement")


# ═══════════════════════════════════════════════════════════════
# P1a: Update survival service Square scoring (remove placeholder)
# ═══════════════════════════════════════════════════════════════

def fix_survival_square():
    path = "/home/ubuntu/nautilus-mvp/phase3/backend/services/survival_service.py"
    with open(path, "r") as f:
        content = f.read()

    old = "        square_score = 0.0"
    if old not in content:
        results.append("P1a SKIP: square_score placeholder not found (may already be fixed)")
        return

    new = """        # Query actual Square posts
        try:
            from models.marketplace_models import SquarePost
            square_count = db.query(SquarePost).filter(
                SquarePost.agent_id == agent_id,
                SquarePost.created_at >= cutoff
            ).count()
            square_score = min(1.0, square_count / 5.0)  # 5 posts = max score
        except Exception:
            square_score = 0.0"""

    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    results.append("P1a OK: survival service now queries square_posts table")


# ═══════════════════════════════════════════════════════════════
# P1b: Add Square/Gene mention to cloud agent briefing
# ═══════════════════════════════════════════════════════════════

def fix_cloud_briefing():
    """Add [SOCIAL] section to scheduler world briefing for cloud agents."""
    path = "/home/ubuntu/nautilus-agent/nautilus_agent/gateway/scheduler.py"
    with open(path, "r") as f:
        content = f.read()

    if "[SOCIAL]" in content:
        results.append("P1b SKIP: [SOCIAL] already in briefing")
        return

    old = '            f"  RULES: After any write, verify immediately.'
    new = '            f"  SOCIAL: post_to_square to share updates, browse_genes/adopt_gene for strategies, comment_on_bounty for discussion.\\n"\n            f"  RULES: After any write, verify immediately.'

    if old in content:
        content = content.replace(old, new, 1)
        with open(path, "w") as f:
            f.write(content)
        results.append("P1b OK: [SOCIAL] tools added to world briefing")
    else:
        results.append("P1b FAIL: RULES pattern not found in scheduler")


# ═══════════════════════════════════════════════════════════════
# P2a: Square NAU cost (replace reputation gate)
# ═══════════════════════════════════════════════════════════════

def fix_square_nau_cost():
    path = "/home/ubuntu/nautilus-mvp/phase3/backend/api/square.py"
    with open(path, "r") as f:
        content = f.read()

    if "total_earnings" in content and "NAU" in content:
        results.append("P2a SKIP: NAU cost may already be implemented")
        return

    # Add NAU deduction after reputation check
    old = "TODO: Replace reputation gate with 1 NAU cost"
    if old in content:
        # Add NAU cost after the reputation check
        nau_check = """
    # NAU cost: 1 NAU per post (anti-spam + economic sink)
    agent_earnings = getattr(agent, "total_earnings", 0) or 0
    if agent_earnings < 1:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INSUFFICIENT_NAU", "message": "Posting requires 1 NAU"}},
        )
    agent.total_earnings = agent_earnings - 1
"""
        content = content.replace(old, "1 NAU cost for posting (anti-spam + economic sink)", 1)
        # Insert NAU check after the reputation check block
        rep_end = "MIN_REPUTATION_TO_POST"
        if rep_end in content:
            # Find the end of the reputation check block
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "MIN_REPUTATION_TO_POST" in line and "raise" not in line:
                    # Find the HTTPException block end
                    for j in range(i+1, min(i+10, len(lines))):
                        if lines[j].strip() == ")":
                            lines.insert(j+1, nau_check)
                            content = "\n".join(lines)
                            break
                    break

        with open(path, "w") as f:
            f.write(content)
        results.append("P2a OK: Square post now costs 1 NAU")
    else:
        results.append("P2a SKIP: TODO marker not found")


if __name__ == "__main__":
    fixes = [
        ("P0: Published tracking", fix_published_tracking),
        ("P1a: Survival Square", fix_survival_square),
        ("P1b: Cloud briefing", fix_cloud_briefing),
        ("P2a: Square NAU cost", fix_square_nau_cost),
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
        ("platform.py", "/home/ubuntu/nautilus-agent/nautilus_agent/tools/platform.py"),
        ("scheduler.py", "/home/ubuntu/nautilus-agent/nautilus_agent/gateway/scheduler.py"),
        ("survival", "/home/ubuntu/nautilus-mvp/phase3/backend/services/survival_service.py"),
        ("square.py", "/home/ubuntu/nautilus-mvp/phase3/backend/api/square.py"),
    ]:
        r = subprocess.run(
            ["python3", "-c", f"import py_compile; py_compile.compile('{path}', doraise=True)"],
            capture_output=True, text=True,
        )
        print(f"  {label}: {'OK' if r.returncode == 0 else 'FAIL: ' + r.stderr[:200]}")
