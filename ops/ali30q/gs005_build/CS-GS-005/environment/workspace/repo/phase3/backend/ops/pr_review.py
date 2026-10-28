# -*- coding: utf-8 -*-
"""soul PR 机审(三权分立一期 · Assay Bench 重考层,U15 · 2026-09-25 用户定方向)。

判决权=评委团(二期 judge hook 接通后移交);本脚本只重考+分级+亮牌,
**不合不关**(soul 安全锚"draft PR 永不自动合并"一期不动,改锚=用户批件在途)。

每 2h 由 nautilus-pr-review.timer 调用(照 org-autoack 配方)。
流程:gh 捞 open soul draft PR → 专用克隆 worktree 试合当前主干(不信旧成绩)→
重跑三重门(engine.checks+pytest_runner+soul.pr_gate)+红线扫描(新增行)→
分级(操作/政策/宪章,照 quorum 定谳 U4②)→ PR 评注(仅状态变化时)+
platform_audit 台账行(V-Sign②回读可验)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")
sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3")

GH_REPO = "chunxiaoxx/nautilus-core"
MAIN_BRANCH = "soul-distill-deploy"
REVIEW_CLONE = "/home/ubuntu/nautilus-pr-review"
STATE_FILE = Path("/home/ubuntu/.pr_review_state.json")
# 评审在主干副本上做,专用克隆避免与 soul workspace 的每轮硬重置赛跑
WORKTREE_ROOT = "/tmp/pr-review"

# 分级规则(照 compass #1056 三档机械判定表对齐,2026-09-26)
# 操作:≤1文件 ∧ ≤50行 ∧ 无行为变更嫌疑;政策:2-5文件或50-400行;
# 宪章:安全部件/红线域/协议正本/≥400行或>5文件。判据与判分器改动
# 不论行数升档(风险在语义不在体量)。
SAFETY_FILES = frozenset({
    "phase3/soul/pause_check.py", "phase3/soul/failure_track.py",
    "phase3/soul/pr_gate.py", "phase3/soul/config.py",
    "phase3/soul/budget_gate.py", "phase3/backend/services/soul_pr_gate.py",
})
SAFETY_PREFIXES = (".github/", "migrations/", "alembic/", ".env", "ops/nginx/",
                   # 组织协议正本(宪章域,compass 表)
                   "CLAUDE.md", "docs/LOOP_", "docs/GOAL_STACK",
                   "docs/IMMUNE_LEDGER", "docs/THREE_WINDOWS")
ALLOWED_PREFIXES = ("phase3/soul/", "phase3/backend/engine/",
                    "phase3/backend/services/soul_")
# 行为变更机械信号:触及判分/校验/门禁 → 至少政策档(compass:不论行数升档)
BEHAVIOR_SIGNALS = ("engine/checks", "verify", "judge", "pr_gate",
                    "auth", "token", "scope")
OPS_MAX_LOC = 50          # compass 表:≤50 行
POLICY_MAX_LOC = 400      # ≥400 → 宪章

# 红线(只扫 diff 新增行;命中=必须人判,不是判死)
REDLINE_PATTERNS = ("rm -rf /", "DROP TABLE", "DROP DATABASE", "TRUNCATE ",
                    "taskkill", "push --force", "-----BEGIN", "passwd=",
                    "password =", "secret_key =")


def classify_pr(files: list, loc: int) -> str:
    """操作/政策/宪章三档。空 diff 或越界文件一律宪章(保守呈人)。"""
    if not files:
        return "charter"
    for f in files:
        if f in SAFETY_FILES or any(f.startswith(p) for p in SAFETY_PREFIXES):
            return "charter"
        if not any(f.startswith(p) for p in ALLOWED_PREFIXES):
            return "charter"
    if loc >= POLICY_MAX_LOC or len(files) > 5:
        return "charter"
    # 行为变更机械信号:判据/门禁/鉴权类文件,不论体量至少政策档
    if any(s in f for f in files for s in BEHAVIOR_SIGNALS):
        return "policy"
    if loc > OPS_MAX_LOC or len(files) > 1:
        return "policy"
    return "ops"


def redline_scan(diff_text: str) -> list:
    """扫描 diff 新增行(+)的危险/密钥模式;上下文与删除行不算。"""
    hits = []
    for line in diff_text.splitlines():
        if not line.startswith("+"):
            continue
        for pat in REDLINE_PATTERNS:
            if pat in line and pat not in hits:
                hits.append(pat)
    return hits


def verdict_color(checks_passed, pytest_result, paths_ok, loc_ok,
                  redlines, mergeable) -> tuple:
    """GREEN=直通候选(全绿)·RED=重考挂·GREY=需人判(红线/信号缺失)。"""
    reasons = []
    if not mergeable:
        reasons.append("与当前主干冲突")
    if not checks_passed:
        reasons.append("静态检查未过")
    if pytest_result is False:
        reasons.append("pytest 红")
    if not paths_ok:
        reasons.append("路径门禁未过")
    if not loc_ok:
        reasons.append("超 LOC 上限")
    if reasons:
        return "RED", reasons
    if pytest_result is None:
        reasons.append("pytest 信号不可用")
    if redlines:
        reasons.append("红线命中:" + ",".join(redlines))
    if reasons:
        return "GREY", reasons
    return "GREEN", []


# --- 以下为云上编排(本地单测不覆盖;部署窗手动首验) ---


def _git(repo: str, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True, timeout=120)


def _gh(*args) -> subprocess.CompletedProcess:
    # 9/26 实证:backend .env 携带失效 GITHUB_TOKEN(fine-grained PAT),gh 优先
    # 环境令牌→静默空列表(首两班 reviewed=0 假空转)。剔除之,落回 hosts.yml 有效凭据。
    env = {k: v for k, v in os.environ.items() if k not in ("GITHUB_TOKEN", "GH_TOKEN")}
    return subprocess.run(["gh", *args, "--repo", GH_REPO],
                          capture_output=True, text=True, timeout=60, env=env)


def _ensure_clone() -> None:
    if not Path(REVIEW_CLONE, ".git").exists():
        subprocess.run(["git", "clone", f"https://github.com/{GH_REPO}.git",
                        REVIEW_CLONE], capture_output=True, text=True, timeout=600,
                       check=True)
    _git(REVIEW_CLONE, "fetch", "origin", MAIN_BRANCH)
    _git(REVIEW_CLONE, "checkout", MAIN_BRANCH)
    _git(REVIEW_CLONE, "reset", "--hard", f"origin/{MAIN_BRANCH}")
    _git(REVIEW_CLONE, "worktree", "prune")


def _list_soul_prs() -> list:
    r = _gh("pr", "list", "--state", "open", "--limit", "50", "--json",
            "number,title,headRefName,isDraft")
    if r.returncode != 0:
        return []
    return [p for p in json.loads(r.stdout)
            if p["headRefName"].startswith("soul/")]


def _review_one(pr: dict) -> dict:
    """单个 PR 重考:试合主干→三重门→红线→分级→三色。"""
    from engine.checks import run_pipeline
    from engine.pytest_runner import run_pytest_for_changed
    from soul import pr_gate

    n = pr["number"]
    wt = f"{WORKTREE_ROOT}-{n}"
    res = {"pr": n, "title": pr["title"], "color": "GREY", "tier": "charter",
           "reasons": ["未跑到评审"], "loc": 0, "files": []}
    try:
        r = _git(REVIEW_CLONE, "fetch", "origin", f"pull/{n}/head")
        if r.returncode != 0:
            res["reasons"] = ["fetch 失败"]
            return res
        r = _git(REVIEW_CLONE, "worktree", "add", "--detach", wt,
                 f"origin/{MAIN_BRANCH}")
        if r.returncode != 0:
            res["reasons"] = ["worktree 失败"]
            return res
        try:
            m = _git(wt, "merge", "--no-commit", "--no-ff", "FETCH_HEAD")
            mergeable = m.returncode == 0
            if not mergeable:
                _git(wt, "merge", "--abort")
            changed = [ln for ln in
                       _git(wt, "diff", "--cached", "--name-only").stdout.splitlines()
                       if ln.strip()] if mergeable else []
            loc = 0
            for ln in _git(wt, "diff", "--cached", "--numstat").stdout.splitlines():
                parts = ln.split("\t")
                loc += sum(int(c) for c in parts[:2] if c.isdigit())
            diff_text = _git(wt, "diff", "--cached").stdout if mergeable else ""
            res["files"], res["loc"] = changed, loc
            res["tier"] = classify_pr(changed, loc)

            if mergeable and changed:
                staged = [str(Path(wt, f)) for f in changed]
                pypath = os.pathsep.join([wt, str(Path(wt, "phase3", "backend"))])
                checks = run_pipeline(staged, pythonpath=pypath)
                pytest_res = run_pytest_for_changed(wt, changed)
                paths_ok, _ = pr_gate.check_paths(changed)
                loc_ok, _ = pr_gate.check_diff_loc(loc)
                red = redline_scan(diff_text)
                color, reasons = verdict_color(
                    checks.get("passed"), pytest_res, paths_ok, loc_ok, red, True)
                res["color"], res["reasons"] = color, reasons
            elif not mergeable:
                res["color"], res["reasons"] = "RED", ["与当前主干冲突"]
            else:
                res["color"], res["reasons"] = "GREY", ["空 diff"]
        finally:
            _git(REVIEW_CLONE, "worktree", "remove", "--force", wt)
    except Exception as e:  # noqa: BLE001 — 单 PR 异常不拖垮整轮
        res["reasons"] = [f"评审异常:{type(e).__name__} {str(e)[:120]}"]
    return res


def _comment_and_ledger(res: dict) -> None:
    """状态变化才评注(防抖);台账每变化一行 platform_audit。"""
    state = {}
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            state = {}
    key = str(res["pr"])
    sig = f"{res['color']}|{res['tier']}|{res['loc']}"
    if state.get(key) == sig:
        return
    state[key] = sig
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    tier_cn = {"ops": "操作", "policy": "政策", "charter": "宪章"}[res["tier"]]
    body = (f"[机审·Bench 重考 {datetime.now():%m-%d %H:%M}] "
            f"分级={tier_cn} · 判定={res['color']}\n"
            f"改动 {len(res['files'])} 文件/{res['loc']} 行;依据: "
            + ("; ".join(res["reasons"]) if res["reasons"] else "三重门全绿")
            + "\n判决权=评委团(二期);本评注=重考成绩单,不合不关。")
    _gh("pr", "comment", str(res["pr"]), "--body", body)

    try:
        import models.agent_survival  # noqa: F401 — mapper dependency
        from models.platform_audit import PlatformAudit
        from utils.database import SessionLocal
        s = SessionLocal()
        try:
            s.add(PlatformAudit(actor="pr-review", actor_type="system",
                                action="pr_review", target=f"PR#{res['pr']}",
                                target_type="github_pr", outcome=res["color"],
                                ip="127.0.0.1", meta={"tier": res["tier"],
                                                      "reasons": res["reasons"][:3]}))
            s.commit()
        finally:
            s.close()
    except Exception:  # noqa: BLE001 — 台账失败不阻塞评审
        pass


def run() -> dict:
    _ensure_clone()
    prs = _list_soul_prs()
    results = [_review_one(p) for p in prs]
    for r in results:
        _comment_and_ledger(r)
    return {"reviewed": len(results),
            "green": sum(1 for r in results if r["color"] == "GREEN"),
            "red": sum(1 for r in results if r["color"] == "RED"),
            "grey": sum(1 for r in results if r["color"] == "GREY")}


if __name__ == "__main__":
    summary = run()
    print(f"pr_review {summary} at {datetime.now():%F %T}", flush=True)
