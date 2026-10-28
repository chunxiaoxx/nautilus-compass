"""
Phase 2-4 Patch: Speed + Safety + Stability
Run on cloud: python3 /tmp/phase234_patch.py
"""
import os
import json
import re

SCHEDULER = "/home/ubuntu/nautilus-agent/nautilus_agent/gateway/scheduler.py"
AGENT = "/home/ubuntu/nautilus-agent/nautilus_agent/agent.py"
MARKETPLACE = "/home/ubuntu/nautilus-mvp/phase3/backend/api/agent_marketplace.py"
ROUTER = "/home/ubuntu/nautilus-agent/nautilus_agent/llm/router.py"

results = []

# ═══════════════════════════════════════════════════════════════
# Phase 2.2: Smart Model Routing
# ═══════════════════════════════════════════════════════════════

def patch_smart_routing():
    with open(ROUTER, "r") as f:
        content = f.read()

    if "resolve_turn_route" in content:
        results.append("2.2 SKIP: smart routing already exists")
        return

    routing_code = '''

# ── Smart Model Routing (ported from Hermes) ─────────────────
_COMPLEX_KEYWORDS = frozenset({
    "debug", "implement", "refactor", "error", "analyze", "test",
    "fix", "deploy", "migrate", "optimize", "architecture", "security",
    "database", "performance", "docker", "kubernetes", "写代码", "修复",
    "bug", "exception", "traceback", "重构", "分析", "部署",
})

def is_simple_message(text: str, max_chars: int = 160, max_words: int = 28) -> bool:
    """Detect simple messages that can use a cheaper model."""
    if not text or len(text) > max_chars:
        return False
    words = text.split()
    if len(words) > max_words:
        return False
    text_lower = text.lower()
    # Has code or URLs?
    if any(c in text for c in ["```", "http://", "https://", "def ", "class ", "import "]):
        return False
    # Has complex keywords?
    if any(kw in text_lower for kw in _COMPLEX_KEYWORDS):
        return False
    return True
'''
    content += routing_code
    with open(ROUTER, "w") as f:
        f.write(content)
    results.append("2.2 OK: smart routing added to router.py")

# ═══════════════════════════════════════════════════════════════
# Phase 2.3: Bounty List Cache in Scheduler
# ═══════════════════════════════════════════════════════════════

def patch_bounty_cache():
    with open(SCHEDULER, "r") as f:
        content = f.read()

    if "_bounty_cache" in content:
        results.append("2.3 SKIP: bounty cache already exists")
        return

    # Add cache fields to __init__ or class level
    old = "    def _get_bounties(self) -> str:"
    new = """    _bounty_cache = ""
    _bounty_cache_ts = 0.0

    def _get_bounties(self) -> str:
        import time as _time
        if _time.time() - self._bounty_cache_ts < 300 and self._bounty_cache:
            return self._bounty_cache
        result = self._fetch_bounties()
        self._bounty_cache = result
        self._bounty_cache_ts = _time.time()
        return result

    def _fetch_bounties(self) -> str:"""

    if old in content:
        content = content.replace(old, new, 1)
        with open(SCHEDULER, "w") as f:
            f.write(content)
        results.append("2.3 OK: bounty cache (5min) added")
    else:
        results.append("2.3 SKIP: _get_bounties not found")

# ═══════════════════════════════════════════════════════════════
# Phase 3.1: Dev.to Article Dedup in World Briefing
# ═══════════════════════════════════════════════════════════════

def patch_article_dedup():
    with open(SCHEDULER, "r") as f:
        content = f.read()

    if "[PUBLISHED]" in content:
        results.append("3.1 SKIP: article dedup already exists")
        return

    # Add published articles tracking to world briefing
    old = '            f"[MISSION] Create external value.'
    new = '            f"[PUBLISHED] Do NOT repeat these topics: {self._get_recent_published()}\\n"\n            f"[MISSION] Create external value.'

    if old in content:
        content = content.replace(old, new, 1)

        # Add the _get_recent_published method
        method = '''
    _published_titles = []

    def _track_published(self, title: str):
        """Track a published article title for dedup."""
        self._published_titles.append(title[:60])
        if len(self._published_titles) > 20:
            self._published_titles = self._published_titles[-20:]

    def _get_recent_published(self) -> str:
        if not self._published_titles:
            return "none yet"
        return ", ".join(self._published_titles[-5:])
'''
        # Insert before _get_bounties
        insert_point = "    _bounty_cache" if "_bounty_cache" in content else "    def _get_bounties"
        if insert_point in content:
            content = content.replace(insert_point, method + "\n" + insert_point, 1)

        with open(SCHEDULER, "w") as f:
            f.write(content)
        results.append("3.1 OK: article dedup [PUBLISHED] added to briefing")
    else:
        results.append("3.1 SKIP: [MISSION] pattern not found")

# ═══════════════════════════════════════════════════════════════
# Phase 3.2: Bounty Creation Rate Limit
# ═══════════════════════════════════════════════════════════════

def patch_bounty_rate_limit():
    with open(MARKETPLACE, "r") as f:
        content = f.read()

    if "daily_bounties" in content:
        results.append("3.2 SKIP: bounty rate limit already exists")
        return

    old = '    """Agent posts a bounty for other agents to claim. NAU escrowed from poster."""'
    new = '''    """Agent posts a bounty for other agents to claim. NAU escrowed from poster."""
    # Rate limit: max bounties/day scales with reputation
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_bounties = db.query(AcademicTask).filter(
        AcademicTask.description.like(f"%BOUNTY by {agent.name}%"),
        AcademicTask.created_at >= today_start
    ).count()
    rep = getattr(agent, "reputation_score", 50) or 50
    max_daily = max(3, int(rep // 20))  # 3-5 bounties/day based on reputation
    if daily_bounties >= max_daily:
        raise HTTPException(429, detail={"error": {"code": "DAILY_LIMIT", "message": f"Daily bounty limit ({max_daily}) reached"}})'''

    if old in content:
        content = content.replace(old, new, 1)
        with open(MARKETPLACE, "w") as f:
            f.write(content)
        results.append("3.2 OK: bounty daily rate limit added")
    else:
        results.append("3.2 SKIP: bounty docstring not found")

# ═══════════════════════════════════════════════════════════════
# Phase 3.3: Core File Read-Only Protection
# ═══════════════════════════════════════════════════════════════

def patch_core_protection():
    with open(AGENT, "r") as f:
        content = f.read()

    if "PROTECTED_CORE_FILES" in content:
        results.append("3.3 SKIP: core protection already exists")
        return

    # Find guarded_tool_executor and add protection
    # Look for the safe_edit/write_file guard pattern
    protection = '''
# Core file protection — agents must not modify these files
PROTECTED_CORE_FILES = {"agent.py", "constitution.py", "main.py", "run_loop.py", "router.py"}

def _is_protected_path(path_str: str) -> bool:
    """Check if a file path points to a protected core file."""
    if not path_str:
        return False
    import os
    basename = os.path.basename(path_str.split("|")[0].strip())
    return basename in PROTECTED_CORE_FILES

'''
    # Insert before the class definition or at module level
    if "class NautilusAgent" in content:
        content = content.replace("class NautilusAgent", protection + "class NautilusAgent", 1)
    elif "class Agent" in content:
        # Find the first class definition
        match = re.search(r'^class \w+.*:', content, re.MULTILINE)
        if match:
            content = content[:match.start()] + protection + content[match.start():]

    with open(AGENT, "w") as f:
        f.write(content)
    results.append("3.3 OK: PROTECTED_CORE_FILES added")

# ═══════════════════════════════════════════════════════════════
# Phase 4.2: Scheduler pain_history Memory Leak Fix
# ═══════════════════════════════════════════════════════════════

def patch_pain_history_leak():
    with open(SCHEDULER, "r") as f:
        content = f.read()

    if "_pain_history_cap" in content or "pain_history) > 100" in content:
        results.append("4.2 SKIP: pain_history cap already exists")
        return

    # Find _pain_history usage and add cap
    if "_pain_history" in content:
        # Add cap after any append/update to _pain_history
        old = "_detect_pain"
        # Find the method and add a cap at the end
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "def _detect_pain" in line:
                # Find the next method (return statement or next def)
                for j in range(i + 1, min(i + 100, len(lines))):
                    if lines[j].strip().startswith("return "):
                        # Insert cap before the return
                        indent = "        "
                        cap_code = f"{indent}# Cap pain history to prevent memory leak\n{indent}if hasattr(self, '_pain_history') and len(getattr(self, '_pain_history', {{}})) > 100:\n{indent}    self._pain_history = dict(list(self._pain_history.items())[-50:])\n"
                        lines.insert(j, cap_code)
                        content = "\n".join(lines)
                        with open(SCHEDULER, "w") as f:
                            f.write(content)
                        results.append("4.2 OK: pain_history capped at 100 entries")
                        return
        results.append("4.2 SKIP: could not find insertion point")
    else:
        results.append("4.2 SKIP: _pain_history not found in scheduler")

# ═══════════════════════════════════════════════════════════════
# Phase 4.3: PM2 Memory Limit
# ═══════════════════════════════════════════════════════════════

def patch_pm2_memory():
    import subprocess
    # Set max_memory_restart for all PM2 processes
    for name in ["kairos-loop", "minimax-loop", "explorer-alpha"]:
        try:
            subprocess.run(
                ["pm2", "set", f"{name}:max_memory_restart", "800M"],
                capture_output=True, text=True, timeout=10
            )
        except Exception:
            pass

    # Alternative: use pm2 ecosystem file
    eco_path = "/home/ubuntu/nautilus-agent/ecosystem.config.js"
    if os.path.exists(eco_path):
        with open(eco_path, "r") as f:
            eco = f.read()
        if "max_memory_restart" not in eco:
            eco = eco.replace("'fork'", "'fork',\n      max_memory_restart: '800M'")
            with open(eco_path, "w") as f:
                f.write(eco)
            results.append("4.3 OK: PM2 max_memory_restart set to 800M")
            return

    results.append("4.3 INFO: PM2 memory limits need manual config")


# ═══════════════════════════════════════════════════════════════
# Apply all patches
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    patches = [
        ("2.2 Smart Routing", patch_smart_routing),
        ("2.3 Bounty Cache", patch_bounty_cache),
        ("3.1 Article Dedup", patch_article_dedup),
        ("3.2 Bounty Rate Limit", patch_bounty_rate_limit),
        ("3.3 Core Protection", patch_core_protection),
        ("4.2 Pain History Cap", patch_pain_history_leak),
        ("4.3 PM2 Memory", patch_pm2_memory),
    ]

    for name, fn in patches:
        try:
            fn()
        except Exception as e:
            results.append(f"{name} ERROR: {e}")

    print("\n".join(results))

    # Verify syntax
    print("\nSyntax verification:")
    import subprocess
    for label, path in [
        ("scheduler", SCHEDULER),
        ("agent", AGENT),
        ("marketplace", MARKETPLACE),
        ("router", ROUTER),
    ]:
        r = subprocess.run(
            ["python3", "-c", f"import py_compile; py_compile.compile('{path}', doraise=True)"],
            capture_output=True, text=True
        )
        status = "OK" if r.returncode == 0 else f"FAIL: {r.stderr[:200]}"
        print(f"  {label}: {status}")
