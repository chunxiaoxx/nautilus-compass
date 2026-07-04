# -*- coding: utf-8 -*-
# cross_dialog_audit.py - 真扫 5 dialog 本地仓库(不靠 MCP)
# 治 6/17 rootcause 钉死的 用户当人肉 relay 病

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


DIALOGS = {
    "compass": r"C:\Users\chunx\Projects\nautilus-compass",
    "v5":      r"C:\Users\chunx\Projects\nautilus-v5",
    "core":    r"C:\Users\chunx\Projects\nautilus-core",
    "buyer":   r"C:\Users\chunx\Projects\nautilus-compass-buyer-tasks",
    "expert":  r"C:\Users\chunx\Projects\nautilus-compass-expert-settle",
}

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 14
SINCE = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")


def sh(cmd, cwd):
    try:
        p = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True,
            timeout=20, encoding="utf-8", errors="replace",
        )
        return p.stdout.strip(), p.stderr.strip(), p.returncode
    except Exception as e:
        return "", str(e), -1


def audit_dialog(name, path):
    p = Path(path)
    result = {"name": name, "path": path, "exists": p.exists()}
    if not p.exists():
        return result

    # 1. git log
    out, _, _ = sh(
        'git log --since="%s" --oneline 2>&1 | head -20' % SINCE, path
    )
    commits = [c for c in out.splitlines() if c and not c.startswith("fatal")]
    result["recent_commits"] = commits[:10]
    result["commit_count"] = len(commits)

    # 2. git status
    out, _, _ = sh("git status --short 2>&1 | head -10", path)
    result["dirty"] = [l for l in out.splitlines() if l][:5]

    # 3. 顶层 .md
    md_files = sorted([f.name for f in p.glob("*.md")])[:15]
    result["top_md"] = md_files

    # 4. .claude/memory/ 最新 3
    mem_dir = p / ".claude" / "memory"
    if mem_dir.exists():
        mems = sorted(
            mem_dir.glob("*.md"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:3]
        result["memory"] = [m.name for m in mems]
    else:
        result["memory"] = []

    # 5. _OUTBOUND_*.md 最近 5
    outbounds = sorted(
        p.glob("_OUTBOUND_*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )[:5]
    result["outbounds"] = [o.name for o in outbounds]

    # 6. worktree
    out, _, _ = sh("git worktree list 2>&1", path)
    result["worktrees"] = out.splitlines()[:5]

    return result


def main():
    print("=== cross dialog audit · %d days · since %s ===" % (DAYS, SINCE))
    print("=" * 80)
    rows = []
    for name, path in DIALOGS.items():
        if name == "buyer" and not Path(path).exists():
            continue
        if name == "expert" and not Path(path).exists():
            continue
        r = audit_dialog(name, path)
        rows.append(r)

        print("[%s] %s" % (r["name"], r["path"]))
        if not r["exists"]:
            print("  X 不存在")
            print()
            continue

        print("  commits(%d):" % r["commit_count"])
        for c in r["recent_commits"][:5]:
            print("    " + c[:90])
        if r["dirty"]:
            print("  dirty (%d files):" % len(r["dirty"]))
            for d in r["dirty"][:3]:
                print("    " + d[:80])
        else:
            print("  dirty: (clean)")
        if r["memory"]:
            print("  memory:")
            for m in r["memory"]:
                print("    " + m)
        else:
            print("  memory: (无 .claude/memory/)")
        if r["outbounds"]:
            print("  outbounds (%d):" % len(r["outbounds"]))
            for o in r["outbounds"]:
                print("    " + o)
        else:
            print("  outbounds: (无)")
        wt = r["worktrees"]
        if len(wt) > 1:
            print("  worktrees: %d extra" % (len(wt) - 1))
        print()

    print("=" * 80)
    print("汇总:")
    print("  5 dialog 仓库探测完成 · %d/%d 存在" % (
        sum(1 for r in rows if r["exists"]), len(rows)
    ))
    total_commits = sum(r["commit_count"] for r in rows)
    print("  近 %d 天总 commit 数: %d" % (DAYS, total_commits))
    print("  有 dirty 的 dialog: %s" % [r["name"] for r in rows if r.get("dirty")])
    print("  有 memory 的 dialog: %s" % [r["name"] for r in rows if r.get("memory")])
    return 0


if __name__ == "__main__":
    sys.exit(main())