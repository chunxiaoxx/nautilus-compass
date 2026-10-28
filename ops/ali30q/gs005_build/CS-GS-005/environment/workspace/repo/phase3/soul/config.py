"""Autonomous Soul · configuration constants (single source of truth).

Safety gates (budget / pause / circuit-breaker) + goal_selector + pr_gate.
"""
from __future__ import annotations
import os
from pathlib import Path

def _safe_env_cast(cast, var, default):
    try:
        return cast(os.environ[var])
    except (KeyError, ValueError, TypeError):
        return default

# Workspace root = repo root (soul/ lives in phase3/soul/, repo root is parents[2])
REPO_ROOT = Path(__file__).resolve().parents[2]

# Safety · budget (daily cost ceiling, JSONL ledger)
DAILY_COST_CAP_USD = _safe_env_cast(float, "SOUL_DAILY_COST_CAP", 20.0)
COST_LEDGER = REPO_ROOT / ".soul-cost-ledger.jsonl"

# Safety · pause + circuit breaker
PAUSE_FILE = REPO_ROOT / ".soul-pause"
FAILURE_STATE = REPO_ROOT / ".soul-failure-state.json"
MAX_CONSECUTIVE_FAILURES = _safe_env_cast(int, "SOUL_MAX_FAILURES", 5)

# Memory (U17 · 2026-09-26):cycle 笔记 JSONL。untracked + .soul- 前缀双保险
# → bootstrap 硬重置免疫(reset --hard 不删未跟踪文件),PR 门禁黑名单亦挡。
MEMORY_FILE = REPO_ROOT / ".soul-memory.jsonl"

# GitHub (circuit-breaker alert + draft PR)
GITHUB_REPO = "chunxiaoxx/nautilus-core"
# 2026-09-14 修:soul PR 曾写死 base=master(8/26 已归档的老分支)→ PR 带 30 万行
# 历史包袱(#143/#144 实证)。主干自 8/26 起 = soul-distill-deploy。
MAIN_BRANCH = os.environ.get("SOUL_MAIN_BRANCH", "soul-distill-deploy")

# Goal selection (goal_selector)
GOALS_FILE = REPO_ROOT / "phase3" / "soul" / "goals.yaml"
MAX_REFLECTION_TASKS_PER_DAY = _safe_env_cast(int, "SOUL_MAX_REFLECTION_DAILY", 2)
REFLECTION_COMPOSITE_THRESHOLD = 0.7
# docs-scrape goal source DISABLED (empty globs): markdown TODO/FIXME markers
# produce prose-shaped goals that the CODE engine can't ship (parse_error), and
# they pre-empt the self-improve cycle. With this empty + no yaml goals + no DB
# reflection, select_goal returns None → the daemon runs its self-improve cycle
# (the durable, cloud-verified goal source). Re-enable by setting real globs.
DOCS_SCRAPE_GLOBS: tuple = ()
DOCS_SCRAPE_MARKERS = ("TODO", "FIXME", "Pending")

# PR gate (pr_gate · diff cap + path blacklist)
MAX_PR_DIFF_LOC = _safe_env_cast(int, "SOUL_MAX_PR_LOC", 500)
PATH_BLACKLIST = (
    ".env", "alembic/", "migrations/", "contracts/", "secrets",
    "_dead_code_backup", ".soul-",
)

# Self-improve scope (L2 platform-scope) · which modules the daemon may self-improve.
# Widened beyond soul/ to ALSO cover the soul's own engine + soul service layer,
# but NEVER agent cognitive code (anchor #7 safety — see SELF_IMPROVE_EXCLUDE).
# U17 扩域(2026-09-26 用户批):+soul tests +backend ops 脚本(*.py 直子文件,
# nginx/ 等子目录不匹配)。评审/名册/函件工具在 EXCLUDE 锁死——提案者不得改考官。
SELF_IMPROVE_SCOPE = (
    "phase3/soul/*.py",
    "phase3/soul/tests/*.py",
    "phase3/backend/engine/*.py",
    "phase3/backend/services/soul_*.py",
    "phase3/backend/ops/*.py",
)
# Substrings that, if present in a candidate's repo-relative path, disqualify it.
# = PATH_BLACKLIST (security/runtime) + agent cognitive + other-dialog markers.
SELF_IMPROVE_EXCLUDE = PATH_BLACKLIST + (
    "agent_brain", "bicameral_mind", "autonomous_loop", "curiosity_engine",
    "agent_parliament", "daemon_", "kairos", "compass", "_v5", "v7_",
    # U17 利益冲突防护:评审器/名册/销账/函件工具=soul 的考官与喉舌,禁自改
    "ops/pr_review", "ops/agent_roster", "ops/auto_ack",
    "ops/send_org_mail", "ops/ack_org_mail",
    # U19 感官器官禁自改:工具箱(compass/搜索/第二意见)是 soul 的眼睛,
    # 改自己的眼睛=既当运动员又改裁判席
    "soul/tools",
)
# Stricter LOC cap for platform-scope (non-soul) targets — smaller blast radius.
# Use _safe_env_cast for consistency with the other env-driven constants above
# (post-merge of #56 · prevents daemon crash on garbage env value).
PLATFORM_MAX_PR_DIFF_LOC = _safe_env_cast(int, "SOUL_PLATFORM_MAX_PR_LOC", 150)
