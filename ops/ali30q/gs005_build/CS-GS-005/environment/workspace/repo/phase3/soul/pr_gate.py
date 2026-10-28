"""PR gate · blacklist + diff LOC cap + draft PR creation (never auto-merge)."""
from __future__ import annotations
import json
import subprocess
from typing import Tuple, List
from soul.config import PATH_BLACKLIST, MAX_PR_DIFF_LOC, REPO_ROOT, GITHUB_REPO, MAIN_BRANCH


def check_paths(changed_paths: List[str]) -> Tuple[bool, str]:
    for p in changed_paths:
        for bad in PATH_BLACKLIST:
            if bad in p:
                return False, f"blacklisted path: {p} (matched '{bad}')"
    return True, "ok"


def check_diff_loc(total_loc: int, max_loc: "int | None" = None) -> Tuple[bool, str]:
    cap = MAX_PR_DIFF_LOC if max_loc is None else max_loc
    if total_loc > cap:
        return False, f"diff {total_loc} LOC exceeds cap {cap}"
    return True, "ok"


def create_draft_pr(branch: str, title: str, body: str) -> str:
    """Push branch + open a DRAFT PR via gh. Returns PR URL. Never merges."""
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), "push", "-u", "origin", branch],
        capture_output=True, text=True, check=True,
    )
    res = subprocess.run(
        ["gh", "pr", "create", "--draft", "--title", title, "--body", body,
         "--base", MAIN_BRANCH, "--head", branch],
        cwd=str(REPO_ROOT), capture_output=True, text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"gh pr create failed: {res.stderr[:300]}")
    return res.stdout.strip()


def check_expect_files(repo: str, expect_files: List[str]) -> Tuple[bool, List[str]]:
    """2026-09-14 修:yaml goal 的产出文件必须真实存在于 cycle 分支 HEAD。

    PR #144 事故:soul 对 'Create <path>' 任务交了不含目标文件的空 PR 且
    checks 全过——交付判据必须断言物在,不能只看编译/黑名单/LOC。
    """
    missing: List[str] = []
    for path in expect_files:
        r = subprocess.run(
            ["git", "-C", repo, "cat-file", "-e", f"HEAD:{path}"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            missing.append(path)
    return (not missing, missing)


def has_open_pr_for(goal_id: str) -> bool:
    """True if an open PR titled 'soul: <goal_id>' already exists (anti-duplicate).

    Prevents PR spam: while a cycle PR is unmerged, master's goals.yaml stays
    pending and bootstrap's reset --hard re-selects the same goal each run.
    Fail-open (return False) on gh error — a missed dedup is recoverable;
    blocking forever on a transient gh failure is worse.

    Slice B followup bug-fix · gh search tokenizes 'soul: <goal_id> in:title'
    by word boundary, so a Slice B PR titled 'feat(soul): ... /api/soul/dispatch ...'
    matches a search for goal_id='dispatch-3' (the tokens 'soul' + 'dispatch'
    + '3' all hit). That false-positive dedup silently blocked the daemon from
    picking new P2 dispatch rows. Fetch titles and filter for an exact prefix
    match post-fetch · gh search stays as a coarse pre-filter for cheap
    network behaviour; exact prefix match is the authoritative gate.
    """
    res = subprocess.run(
        ["gh", "pr", "list", "--repo", GITHUB_REPO, "--state", "open",
         "--search", f"soul: {goal_id} in:title", "--json", "number,title"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return False
    try:
        prs = json.loads(res.stdout or "[]")
    except (ValueError, TypeError):
        return False
    exact = f"soul: {goal_id}"
    # Accept titles that are exactly 'soul: <goal_id>' or start with it (the
    # daemon emits the exact form today; startswith leaves room for a future
    # 'soul: <goal_id> [retry]' variant to still dedup).
    return any((pr.get("title") or "").startswith(exact) for pr in prs)
