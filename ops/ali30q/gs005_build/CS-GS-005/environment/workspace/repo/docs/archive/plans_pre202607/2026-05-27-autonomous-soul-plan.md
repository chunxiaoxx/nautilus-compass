# Autonomous Soul · MVP (P0) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship the P0 MVP of an autonomous Soul daemon that, every 2h, selects a goal, runs the existing engine in dry-run, gates the diff, opens a draft PR, and records the outcome — with 4 in-code safety layers and anti-self-loop guards.

**Architecture:** New `phase3/soul/` package. Pure-Python components (budget_gate, pause_check, goal_selector, pr_gate, failure_track) orchestrated by `daemon.py`. Reuses existing `engine.ship()` + `engine_cycle_outcomes` + `v_engine_progress`. Runs from an independent clean origin-synced clone (`~/nautilus-soul-workspace`) on cloud-server via systemd timer. Never touches the diverged `~/nautilus-mvp`.

**Tech Stack:** Python 3.8+ stdlib + PyYAML (goals.yaml) + `gh` CLI (draft PR + issue alert) + git + DeepSeek/Vertex LLM (via existing `agent_engine.llm.client.LLMClient`).

**Scope:** P0 only. P1 (cross-repo read), P2 (auth platform + compass), P3 (skills-hub) deferred — each gated on cross-dialog consent.

---

## Pre-flight

Confirm prerequisites before starting.

Run: `cd /c/Users/chunx/Projects/nautilus-core && git status -b -s | head -1`
Expected: `## master...origin/master` clean (or ahead by pushed design+plan commits).

Run: `python -c "import yaml; print(yaml.__version__)"`
Expected: PyYAML version string. If ImportError, add `pyyaml` to `phase3/cli/setup.py` deps in Task 1.

Run: `gh --version`
Expected: gh CLI present (used for draft PR + issue alerts). Confirmed available this environment (2.87.3).

Read the design doc first: `docs/plans/2026-05-27-autonomous-soul-design.md` — the 5 locked decisions + 4 safety layers + anti-self-loop guards are authoritative.

---

### Task 1: Package scaffold + config

**Files:**
- Create: `phase3/soul/__init__.py`
- Create: `phase3/soul/config.py`
- Create: `phase3/soul/tests/__init__.py`

**Step 1: Write config.py**

```python
"""Autonomous Soul · configuration constants (single source of truth)."""
from __future__ import annotations
import os
from pathlib import Path

# Workspace root = repo root (soul/ lives in phase3/soul/, repo root is parents[2])
REPO_ROOT = Path(__file__).resolve().parents[2]

# Safety · budget
DAILY_COST_CAP_USD = float(os.getenv("SOUL_DAILY_COST_CAP", "20.0"))
COST_LEDGER = REPO_ROOT / ".soul-cost-ledger.jsonl"

# Safety · pause + circuit breaker
PAUSE_FILE = REPO_ROOT / ".soul-pause"
FAILURE_STATE = REPO_ROOT / ".soul-failure-state.json"
MAX_CONSECUTIVE_FAILURES = int(os.getenv("SOUL_MAX_FAILURES", "5"))

# Safety · PR gate
MAX_PR_DIFF_LOC = int(os.getenv("SOUL_MAX_PR_LOC", "500"))
PATH_BLACKLIST = (
    ".env", "alembic/", "migrations/", "contracts/", "secrets",
    "_dead_code_backup", ".soul-",
)

# Goal selection
GOALS_FILE = REPO_ROOT / "phase3" / "soul" / "goals.yaml"
MAX_REFLECTION_TASKS_PER_DAY = int(os.getenv("SOUL_MAX_REFLECTION_DAILY", "2"))
REFLECTION_COMPOSITE_THRESHOLD = 0.7
DOCS_SCRAPE_GLOBS = ("README.md", "docs/**/*.md")
DOCS_SCRAPE_MARKERS = ("TODO", "FIXME", "Pending")

# GitHub
GITHUB_REPO = "chunxiaoxx/nautilus-core"
```

**Step 2: Empty __init__ files**

`phase3/soul/__init__.py`:
```python
"""Autonomous Soul · self-growing engine daemon."""
```

`phase3/soul/tests/__init__.py`: empty file.

**Step 3: Verify import**

Run: `cd /c/Users/chunx/Projects/nautilus-core/phase3 && python -c "from soul.config import DAILY_COST_CAP_USD, MAX_PR_DIFF_LOC; print(DAILY_COST_CAP_USD, MAX_PR_DIFF_LOC)"`
Expected: `20.0 500`

**Step 4: Commit**

```bash
git add phase3/soul/__init__.py phase3/soul/config.py phase3/soul/tests/__init__.py
git commit -m "feat(soul): package scaffold + config constants"
```

---

### Task 2: budget_gate

**Files:**
- Create: `phase3/soul/budget_gate.py`
- Test: `phase3/soul/tests/test_budget_gate.py`

**Step 1: Write failing test**

```python
import json
from datetime import datetime, timezone
from soul import budget_gate


def test_under_cap_allows(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ledger.write_text(json.dumps({"date": today, "cost_usd": 5.0}) + "\n")
    monkeypatch.setattr(budget_gate, "COST_LEDGER", ledger)
    monkeypatch.setattr(budget_gate, "DAILY_COST_CAP_USD", 20.0)
    assert budget_gate.under_cap() is True


def test_over_cap_blocks(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ledger.write_text(json.dumps({"date": today, "cost_usd": 25.0}) + "\n")
    monkeypatch.setattr(budget_gate, "COST_LEDGER", ledger)
    monkeypatch.setattr(budget_gate, "DAILY_COST_CAP_USD", 20.0)
    assert budget_gate.under_cap() is False


def test_record_appends(tmp_path, monkeypatch):
    ledger = tmp_path / "ledger.jsonl"
    monkeypatch.setattr(budget_gate, "COST_LEDGER", ledger)
    budget_gate.record_cost(0.003, "cycle_abc")
    lines = ledger.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["cost_usd"] == 0.003
```

**Step 2: Run · expect fail**

Run: `cd phase3 && python -m pytest soul/tests/test_budget_gate.py -v`
Expected: ModuleNotFoundError or AttributeError.

**Step 3: Implement budget_gate.py**

```python
"""Daily cost ceiling gate · reads/writes JSONL cost ledger."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from soul.config import COST_LEDGER, DAILY_COST_CAP_USD


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def today_cost() -> float:
    if not COST_LEDGER.exists():
        return 0.0
    total = 0.0
    today = _today()
    for line in COST_LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("date") == today:
            total += float(row.get("cost_usd", 0.0))
    return total


def under_cap() -> bool:
    return today_cost() < DAILY_COST_CAP_USD


def record_cost(cost_usd: float, cycle_id: str) -> None:
    COST_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "date": _today(),
        "ts": datetime.now(timezone.utc).isoformat(),
        "cost_usd": float(cost_usd),
        "cycle_id": cycle_id,
    }
    with COST_LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
```

**Step 4: Run · expect pass**

Run: `cd phase3 && python -m pytest soul/tests/test_budget_gate.py -v`
Expected: 3 passed.

**Step 5: Commit**

```bash
git add phase3/soul/budget_gate.py phase3/soul/tests/test_budget_gate.py
git commit -m "feat(soul): budget_gate · daily cost cap + JSONL ledger"
```

---

### Task 3: pause_check

**Files:**
- Create: `phase3/soul/pause_check.py`
- Test: `phase3/soul/tests/test_pause_check.py`

**Step 1: Write failing test**

```python
from soul import pause_check


def test_paused_when_file_exists(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    pf.write_text("paused")
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    assert pause_check.is_paused() is True


def test_not_paused_when_absent(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    assert pause_check.is_paused() is False
```

**Step 2: Run · expect fail.**

**Step 3: Implement pause_check.py**

```python
"""Manual pause + circuit-breaker pause check."""
from __future__ import annotations
from soul.config import PAUSE_FILE


def is_paused() -> bool:
    return PAUSE_FILE.exists()


def engage_pause(reason: str) -> None:
    PAUSE_FILE.write_text(reason, encoding="utf-8")
```

**Step 4: Run · expect 2 passed.**

**Step 5: Commit**

```bash
git add phase3/soul/pause_check.py phase3/soul/tests/test_pause_check.py
git commit -m "feat(soul): pause_check · manual + circuit-breaker pause file"
```

---

### Task 4: goal_selector · goals.yaml loader

**Files:**
- Create: `phase3/soul/goals.yaml`
- Create: `phase3/soul/goal_selector.py`
- Test: `phase3/soul/tests/test_goal_selector.py`

**Step 1: Seed goals.yaml** (anchor #2 external-facing first per design section 5)

```yaml
# Autonomous Soul · goal queue · human-curated (highest priority tier)
# category: external (anchor #2 OSS pivot artifacts) ranks above internal (self-improvement)
# status: pending | done
goals:
  - id: a2-readme-hero
    priority: 100
    category: external
    description: "Rewrite README hero section: lead with Stage 1 closed-loop demo + D1 drift evidence + cycle 17 self-catch. Remove stale 'MIT licensed' sentence in Nautilus Soul section (now Apache 2.0)."
    status: pending
    acceptance: "README top 40 lines lead with self-modification proof, not platform DMAS pitch. No 'MIT licensed' string remains."
  - id: a4-devto-draft
    priority: 90
    category: external
    description: "Draft a 1500-2000 word dev.to article: git log + before/after fidelity of cycle 5 + cycle 9 dogfood ships."
    status: pending
    acceptance: "docs/articles/devto-draft.md exists, 1500-2000 words, cites verifiable commits."
```

**Step 2: Write failing test**

```python
from soul import goal_selector


def test_loads_pending_external_first(tmp_path, monkeypatch):
    g = tmp_path / "goals.yaml"
    g.write_text(
        "goals:\n"
        "  - id: low\n    priority: 10\n    category: internal\n    description: x\n    status: pending\n"
        "  - id: high\n    priority: 100\n    category: external\n    description: y\n    status: pending\n"
        "  - id: done1\n    priority: 200\n    category: external\n    description: z\n    status: done\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(goal_selector, "GOALS_FILE", g)
    goal = goal_selector.next_yaml_goal()
    assert goal is not None
    assert goal["id"] == "high"  # highest priority among pending


def test_returns_none_when_all_done(tmp_path, monkeypatch):
    g = tmp_path / "goals.yaml"
    g.write_text("goals:\n  - id: a\n    priority: 5\n    category: external\n    description: x\n    status: done\n", encoding="utf-8")
    monkeypatch.setattr(goal_selector, "GOALS_FILE", g)
    assert goal_selector.next_yaml_goal() is None
```

**Step 3: Run · expect fail.**

**Step 4: Implement goal_selector.py (yaml part only)**

```python
"""Goal selection · priority queue: goals.yaml > reflection > docs scrape."""
from __future__ import annotations
from typing import Optional
import yaml
from soul.config import GOALS_FILE


def next_yaml_goal() -> Optional[dict]:
    """Highest-priority pending goal from goals.yaml, or None."""
    if not GOALS_FILE.exists():
        return None
    data = yaml.safe_load(GOALS_FILE.read_text(encoding="utf-8")) or {}
    pending = [g for g in data.get("goals", []) if g.get("status") != "done"]
    if not pending:
        return None
    return sorted(pending, key=lambda g: g.get("priority", 0), reverse=True)[0]
```

**Step 5: Run · expect 2 passed.**

**Step 6: Commit**

```bash
git add phase3/soul/goals.yaml phase3/soul/goal_selector.py phase3/soul/tests/test_goal_selector.py
git commit -m "feat(soul): goal_selector yaml loader + seed goals (anchor #2 external first)"
```

---

### Task 5: goal_selector · reflection + docs-scrape fallback + priority integration

**Files:**
- Modify: `phase3/soul/goal_selector.py`
- Modify: `phase3/soul/tests/test_goal_selector.py`

**Step 1: Add failing tests**

```python
def test_docs_scrape_finds_marker(tmp_path, monkeypatch):
    d = tmp_path / "README.md"
    d.write_text("line1\n<!-- TODO: wire up the foo endpoint -->\nline3\n", encoding="utf-8")
    monkeypatch.setattr(goal_selector, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(goal_selector, "DOCS_SCRAPE_GLOBS", ("README.md",))
    goal = goal_selector.next_docs_goal()
    assert goal is not None
    assert "foo endpoint" in goal["description"]


def test_select_prefers_yaml_over_fallback(tmp_path, monkeypatch):
    g = tmp_path / "goals.yaml"
    g.write_text("goals:\n  - id: y1\n    priority: 50\n    category: external\n    description: yaml-task\n    status: pending\n", encoding="utf-8")
    monkeypatch.setattr(goal_selector, "GOALS_FILE", g)
    chosen = goal_selector.select_goal(reflection_done_today=0)
    assert chosen["source"] == "yaml"
    assert chosen["id"] == "y1"
```

**Step 2: Run · expect fail.**

**Step 3: Implement reflection + docs + select_goal**

```python
import re
from soul.config import (
    REPO_ROOT, DOCS_SCRAPE_GLOBS, DOCS_SCRAPE_MARKERS,
    MAX_REFLECTION_TASKS_PER_DAY, REFLECTION_COMPOSITE_THRESHOLD,
)


def next_reflection_goal() -> Optional[dict]:
    """Query engine_cycle_outcomes via v_engine_progress for low-composite cycles.

    Returns None if DATABASE_URL unset (P0 may run without DB; reflection is best-effort).
    """
    import os
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        return None
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute(
            "SELECT cycle_id, avg_composite FROM v_engine_progress "
            "WHERE avg_composite < %s ORDER BY avg_composite ASC LIMIT 1",
            (REFLECTION_COMPOSITE_THRESHOLD,),
        )
        row = cur.fetchone()
        conn.close()
    except Exception:
        return None
    if not row:
        return None
    return {
        "id": f"reflect-{row[0]}",
        "category": "internal",
        "description": f"Improve low-composite cycle {row[0]} (avg_composite={row[1]:.3f}).",
        "source": "reflection",
    }


def next_docs_goal() -> Optional[dict]:
    for pattern in DOCS_SCRAPE_GLOBS:
        for path in sorted(REPO_ROOT.glob(pattern)):
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                for marker in DOCS_SCRAPE_MARKERS:
                    if marker in line:
                        desc = re.sub(r"^.*?" + marker + r"[:\s]*", "", line).strip(" -<>!")
                        if len(desc) >= 10:
                            return {
                                "id": f"docs-{path.stem}-{abs(hash(line)) % 10000}",
                                "category": "internal",
                                "description": desc,
                                "source": "docs",
                            }
    return None


def select_goal(reflection_done_today: int = 0) -> Optional[dict]:
    """Priority queue: yaml > reflection (capped) > docs scrape."""
    y = next_yaml_goal()
    if y is not None:
        y = dict(y)
        y["source"] = "yaml"
        return y
    if reflection_done_today < MAX_REFLECTION_TASKS_PER_DAY:
        r = next_reflection_goal()
        if r is not None:
            return r
    return next_docs_goal()
```

**Step 4: Run · expect all goal_selector tests pass.**

**Step 5: Commit**

```bash
git add phase3/soul/goal_selector.py phase3/soul/tests/test_goal_selector.py
git commit -m "feat(soul): goal_selector reflection + docs fallback + priority queue (reflection daily cap)"
```

---

### Task 6: pr_gate · diff cap + blacklist

**Files:**
- Create: `phase3/soul/pr_gate.py`
- Test: `phase3/soul/tests/test_pr_gate.py`

**Step 1: Write failing test**

```python
from soul import pr_gate


def test_blacklist_rejects():
    ok, reason = pr_gate.check_paths([".env", "phase3/soul/daemon.py"])
    assert ok is False
    assert ".env" in reason


def test_clean_paths_pass():
    ok, reason = pr_gate.check_paths(["phase3/soul/daemon.py", "README.md"])
    assert ok is True


def test_diff_cap_rejects():
    ok, reason = pr_gate.check_diff_loc(600)
    assert ok is False


def test_diff_cap_allows():
    ok, reason = pr_gate.check_diff_loc(400)
    assert ok is True
```

**Step 2: Run · expect fail.**

**Step 3: Implement pr_gate.py (gate logic only · PR creation in Task 7)**

```python
"""PR gate · blacklist + diff LOC cap. Draft PR creation added in Task 7."""
from __future__ import annotations
from typing import Tuple, List
from soul.config import PATH_BLACKLIST, MAX_PR_DIFF_LOC


def check_paths(changed_paths: List[str]) -> Tuple[bool, str]:
    for p in changed_paths:
        for bad in PATH_BLACKLIST:
            if bad in p:
                return False, f"blacklisted path: {p} (matched '{bad}')"
    return True, "ok"


def check_diff_loc(total_loc: int) -> Tuple[bool, str]:
    if total_loc > MAX_PR_DIFF_LOC:
        return False, f"diff {total_loc} LOC exceeds cap {MAX_PR_DIFF_LOC}"
    return True, "ok"
```

**Step 4: Run · expect 4 passed.**

**Step 5: Commit**

```bash
git add phase3/soul/pr_gate.py phase3/soul/tests/test_pr_gate.py
git commit -m "feat(soul): pr_gate · blacklist + diff LOC cap"
```

---

### Task 7: pr_gate · draft PR creation (mock gh)

**Files:**
- Modify: `phase3/soul/pr_gate.py`
- Modify: `phase3/soul/tests/test_pr_gate.py`

**Step 1: Add failing test (subprocess mocked)**

```python
def test_create_draft_pr_invokes_gh(monkeypatch):
    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class R:
            returncode = 0
            stdout = "https://github.com/chunxiaoxx/nautilus-core/pull/123\n"
            stderr = ""
        return R()
    monkeypatch.setattr(pr_gate.subprocess, "run", fake_run)
    url = pr_gate.create_draft_pr("soul/cycle-x", "Soul: test", "body text")
    assert "pull/123" in url
    # confirm --draft flag present in the gh pr create call
    assert any("--draft" in c for c in calls if isinstance(c, list))
```

**Step 2: Run · expect fail.**

**Step 3: Implement create_draft_pr**

```python
import subprocess
from soul.config import REPO_ROOT


def create_draft_pr(branch: str, title: str, body: str) -> str:
    """Push branch + open a DRAFT PR via gh. Returns PR URL. Never merges."""
    subprocess.run(["git", "-C", str(REPO_ROOT), "push", "-u", "origin", branch],
                   capture_output=True, text=True, check=True)
    res = subprocess.run(
        ["gh", "pr", "create", "--draft", "--title", title, "--body", body,
         "--base", "master", "--head", branch],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"gh pr create failed: {res.stderr[:300]}")
    return res.stdout.strip()
```

**Step 4: Run · expect pass.**

**Step 5: Commit**

```bash
git add phase3/soul/pr_gate.py phase3/soul/tests/test_pr_gate.py
git commit -m "feat(soul): pr_gate · draft PR creation via gh (never auto-merge)"
```

---

### Task 8: failure_track · circuit breaker

**Files:**
- Create: `phase3/soul/failure_track.py`
- Test: `phase3/soul/tests/test_failure_track.py`

**Step 1: Write failing test**

```python
import json
from soul import failure_track


def test_consecutive_failures_engage_pause(tmp_path, monkeypatch):
    state = tmp_path / "fail.json"
    pause = tmp_path / ".soul-pause"
    monkeypatch.setattr(failure_track, "FAILURE_STATE", state)
    monkeypatch.setattr(failure_track, "MAX_CONSECUTIVE_FAILURES", 3)
    monkeypatch.setattr(failure_track.pause_check, "PAUSE_FILE", pause)
    monkeypatch.setattr(failure_track, "_alert", lambda msg: None)
    for _ in range(2):
        failure_track.record_failure("cyc")
    assert not pause.exists()
    failure_track.record_failure("cyc")  # 3rd
    assert pause.exists()


def test_success_resets(tmp_path, monkeypatch):
    state = tmp_path / "fail.json"
    monkeypatch.setattr(failure_track, "FAILURE_STATE", state)
    failure_track.record_failure("c")
    failure_track.record_success()
    assert json.loads(state.read_text())["consecutive"] == 0
```

**Step 2: Run · expect fail.**

**Step 3: Implement failure_track.py**

```python
"""Circuit breaker · N consecutive failures → engage pause + alert."""
from __future__ import annotations
import json
import subprocess
from soul import pause_check
from soul.config import FAILURE_STATE, MAX_CONSECUTIVE_FAILURES, GITHUB_REPO


def _read() -> int:
    if not FAILURE_STATE.exists():
        return 0
    try:
        return int(json.loads(FAILURE_STATE.read_text()).get("consecutive", 0))
    except Exception:
        return 0


def _write(n: int) -> None:
    FAILURE_STATE.write_text(json.dumps({"consecutive": n}), encoding="utf-8")


def _alert(msg: str) -> None:
    subprocess.run(["gh", "issue", "create", "--repo", GITHUB_REPO,
                    "--title", "Soul circuit breaker engaged", "--body", msg],
                   capture_output=True, text=True)


def record_failure(cycle_id: str) -> None:
    n = _read() + 1
    _write(n)
    if n >= MAX_CONSECUTIVE_FAILURES:
        pause_check.engage_pause(f"circuit breaker · {n} consecutive failures · last={cycle_id}")
        _alert(f"Soul paused after {n} consecutive failures (last cycle {cycle_id}).")


def record_success() -> None:
    _write(0)
```

**Step 4: Run · expect 2 passed.**

**Step 5: Commit**

```bash
git add phase3/soul/failure_track.py phase3/soul/tests/test_failure_track.py
git commit -m "feat(soul): failure_track · N=5 circuit breaker + GitHub issue alert"
```

---

### Task 9: daemon · main orchestration loop

**Files:**
- Create: `phase3/soul/daemon.py`
- Test: `phase3/soul/tests/test_daemon.py`

**Step 1: Write failing test (all components mocked)**

```python
from soul import daemon


def test_daemon_skips_when_paused(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: True)
    rc = daemon.run_once()
    assert rc == 0  # graceful skip


def test_daemon_skips_when_over_budget(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: False)
    rc = daemon.run_once()
    assert rc == 0


def test_daemon_skips_when_no_goal(monkeypatch):
    monkeypatch.setattr(daemon.pause_check, "is_paused", lambda: False)
    monkeypatch.setattr(daemon.budget_gate, "under_cap", lambda: True)
    monkeypatch.setattr(daemon.goal_selector, "select_goal", lambda **k: None)
    rc = daemon.run_once()
    assert rc == 0
```

**Step 2: Run · expect fail.**

**Step 3: Implement daemon.py**

```python
"""Autonomous Soul daemon · one orchestration cycle.

Order: pause_check → budget_gate → goal_selector → engine.ship(dry) →
pr_gate → outcome_emit → failure_track.
"""
from __future__ import annotations
import logging
import sys
from soul import budget_gate, pause_check, goal_selector, pr_gate, failure_track

logger = logging.getLogger("soul.daemon")


def run_once() -> int:
    if pause_check.is_paused():
        logger.info("paused · skipping cycle")
        return 0
    if not budget_gate.under_cap():
        logger.info("daily budget cap reached · skipping cycle")
        return 0

    goal = goal_selector.select_goal()
    if goal is None:
        logger.info("no goal available · skipping cycle")
        return 0

    logger.info("selected goal: %s (source=%s)", goal.get("id"), goal.get("source"))

    # Engine ship in dry-run · import lazily to keep tests light
    try:
        from engine.nautilus_engine import NautilusEngine
        from engine.ship import ship
    except ImportError as e:
        logger.error("engine import failed: %s", e)
        failure_track.record_failure(goal.get("id", "unknown"))
        return 1

    from soul.config import REPO_ROOT
    engine = NautilusEngine(base_dir=str(REPO_ROOT), dry_run=True)
    result = ship(engine, goal["description"], str(REPO_ROOT),
                  apply=False, dispatch_audit=False)

    # Record cost (best-effort · engine may expose token usage later)
    budget_gate.record_cost(0.005, goal.get("id", "cycle"))

    if not result.check_result.get("passed"):
        logger.warning("checks failed for goal %s", goal.get("id"))
        failure_track.record_failure(goal.get("id", "unknown"))
        return 1

    # PR gate
    changed = [f["path"] for f in result.files_planned]
    ok_paths, reason = pr_gate.check_paths(changed)
    total_loc = sum(f.get("size", 0) for f in result.files_planned) // 40  # rough LOC est
    ok_loc, loc_reason = pr_gate.check_diff_loc(total_loc)
    if not (ok_paths and ok_loc):
        logger.warning("pr_gate reject: %s %s", reason, loc_reason)
        failure_track.record_failure(goal.get("id", "unknown"))
        return 1

    # NOTE: actual apply + branch + draft PR wired in P0 acceptance (Task 11) ·
    # this run_once proves the gate chain. Full apply path is a follow-up within P0.
    failure_track.record_success()
    logger.info("cycle complete · goal %s passed gates (dry-run)", goal.get("id"))
    return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    return run_once()


if __name__ == "__main__":
    sys.exit(main())
```

**Step 4: Run · expect 3 passed.**

**Step 5: Commit**

```bash
git add phase3/soul/daemon.py phase3/soul/tests/test_daemon.py
git commit -m "feat(soul): daemon run_once · pause→budget→goal→ship→gate→track chain"
```

---

### Task 10: systemd units + bootstrap script

**Files:**
- Create: `phase3/soul/systemd/nautilus-soul.service`
- Create: `phase3/soul/systemd/nautilus-soul.timer`
- Create: `phase3/soul/bootstrap.sh`

**Step 1: Write nautilus-soul.service**

```ini
[Unit]
Description=Autonomous Nautilus Soul · one cycle
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=/home/ubuntu/nautilus-soul-workspace/phase3
EnvironmentFile=/home/ubuntu/nautilus-soul-workspace/.soul-env
ExecStart=/usr/bin/python3 -m soul.daemon
```

**Step 2: Write nautilus-soul.timer**

```ini
[Unit]
Description=Run Nautilus Soul every 2 hours

[Timer]
OnBootSec=10min
OnUnitActiveSec=2h
Persistent=true

[Install]
WantedBy=timers.target
```

**Step 3: Write bootstrap.sh**

```bash
#!/bin/bash
# Bootstrap autonomous Soul on cloud-server in an isolated clean clone.
# Does NOT touch ~/nautilus-mvp.
set -euo pipefail

WORKSPACE="$HOME/nautilus-soul-workspace"
REPO="https://github.com/chunxiaoxx/nautilus-core.git"

if [ ! -d "$WORKSPACE" ]; then
    git clone "$REPO" "$WORKSPACE"
fi
cd "$WORKSPACE"
git fetch origin master
git reset --hard origin/master

# Env file (edit secrets here · never commit)
if [ ! -f "$WORKSPACE/.soul-env" ]; then
    cat > "$WORKSPACE/.soul-env" <<'EOF'
DEEPSEEK_API_KEY=__SET_ME__
DEEPSEEK_BASE_URL=https://api.deepseek.com/anthropic
DEEPSEEK_MODEL=deepseek-v4-pro
GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/.config/gcloud/soul-sa.json
SOUL_DAILY_COST_CAP=20.0
PYTHONPATH=/home/ubuntu/nautilus-soul-workspace/phase3/backend
EOF
    echo "EDIT $WORKSPACE/.soul-env with real DEEPSEEK_API_KEY before enabling timer"
fi

pip install --user pyyaml psycopg2-binary anthropic >/dev/null 2>&1 || true

sudo cp phase3/soul/systemd/nautilus-soul.service /etc/systemd/system/
sudo cp phase3/soul/systemd/nautilus-soul.timer /etc/systemd/system/
sudo systemctl daemon-reload
echo "Bootstrap complete. To activate: sudo systemctl enable --now nautilus-soul.timer"
echo "First verify a manual run: cd $WORKSPACE/phase3 && python3 -m soul.daemon"
```

**Step 4: Make executable + verify syntax**

Run: `bash -n phase3/soul/bootstrap.sh && echo "syntax ok"`
Expected: `syntax ok`

**Step 5: Commit**

```bash
git add phase3/soul/systemd/ phase3/soul/bootstrap.sh
git commit -m "feat(soul): systemd timer + service + isolated-workspace bootstrap script"
```

---

### Task 11: Full test sweep + P0 acceptance (manual cloud step)

**Step 1: Run all soul tests**

Run: `cd phase3 && python -m pytest soul/tests/ -v`
Expected: all tests pass (budget 3 + pause 2 + goal 4 + pr 5 + failure 2 + daemon 3 = ~19).

**Step 2: Confirm engine tests still green (no regression)**

Run: `cd phase3/backend/engine && python -m pytest -q --tb=no`
Expected: 196 passed · 6 skipped.

**Step 3: Commit any fixups, then push**

```bash
git add -A phase3/soul/
git commit -m "test(soul): full P0 suite green"
git push origin master   # via fresh PAT
```

**Step 4: P0 acceptance on cloud (manual · fresh session with cloud access)**

```bash
ssh cloud "bash <(curl -s https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/phase3/soul/bootstrap.sh)"
# edit ~/nautilus-soul-workspace/.soul-env with real DEEPSEEK_API_KEY
ssh cloud "cd ~/nautilus-soul-workspace/phase3 && set -a && source ../.soul-env && set +a && python3 -m soul.daemon"
```

Expected: daemon selects `a2-readme-hero` goal (yaml top priority), runs engine dry-run, passes gates, logs "cycle complete". (Full apply+PR path is the next P0 increment after this dry-run proof.)

**Step 5: Activate timer (only after dry-run proof + human review)**

```bash
ssh cloud "sudo systemctl enable --now nautilus-soul.timer && systemctl list-timers nautilus-soul.timer"
```

---

## Out of Scope (P0)

- Full apply + branch + draft-PR wiring inside run_once (Task 9 proves gate chain in dry-run; the apply path is the immediate P0 follow-up increment, kept separate to verify gates first)
- P1 cross-repo read · P2 auth platform + compass · P3 skills-hub (cross-dialog gated)
- Real token-usage cost accounting (uses flat 0.005/cycle estimate; refine when engine exposes usage)
- Soul wallet / NAU / marketplace (excluded by decision D)
- Touching `~/nautilus-mvp` (uses isolated clean workspace)
- alembic / migrations / contracts (blacklist)

## Risk + Rollback

- Risk: low for P0 — dry-run only, draft PRs only, human merge gate, daily cost cap, circuit breaker.
- Rollback: `sudo systemctl disable --now nautilus-soul.timer` stops all autonomy instantly. `rm -rf ~/nautilus-soul-workspace` removes Soul entirely. No production (`~/nautilus-mvp`) impact.

## Done Criteria (P0)

1. `phase3/soul/` package with 7 components + tests (~19 tests green)
2. Engine 196 tests unchanged
3. systemd timer + service + bootstrap.sh present
4. Cloud dry-run proof: daemon selects top goal, runs engine, passes gates, logs completion
5. Timer NOT auto-activated until human reviews dry-run output
6. anti-self-loop guard live: goals.yaml external goals rank above reflection; reflection daily cap enforced

## Execution note

This plan is for a FRESH SESSION. Do not execute mid-current-session (R3 already 3x overridden, ~8h elapsed). Token revocation (`action_token_revoke_20260527.md`) should happen before any push using a PAT.
