#!/usr/bin/env python
"""Memory git keeper · frame-upgrade-20260904-compass #3 (letta MemFS 原则).

对 ~/.claude/projects/*/memory/ 各目录: 有变化才 commit,误改可回滚、版本可追溯。
由 Stop hook 每次调用(见 ~/.claude/settings.json hooks.Stop),任何失败静默退出
(记忆 keeper 永不阻塞会话收尾)。
"""
import subprocess
import sys
from pathlib import Path

BASE = Path.home() / ".claude" / "projects"
TIMEOUT = 25  # 单目录单命令超时;大目录跳过,记忆 keeper 永不拖垮收尾


def git(*args: str, cwd: Path) -> int:
    try:
        return subprocess.run(["git", *args], cwd=cwd, timeout=TIMEOUT,
                              capture_output=True, text=True).returncode
    except subprocess.TimeoutExpired:
        return 0


def main() -> int:
    if not BASE.exists():
        return 0
    for mem in BASE.glob("*/memory"):
        if not (mem / ".git").exists():
            try:
                git("init", "-q", cwd=mem)
            except Exception:
                continue
        if git("add", "-A", cwd=mem) != 0:
            continue
        r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=mem,
                           timeout=TIMEOUT, capture_output=True, text=True)
        if r.returncode == 0:
            continue  # 无变化
        git("commit", "-q", "-m",
            "chore(memory): auto checkpoint (memory_git_keeper)", cwd=mem)
    return 0


if __name__ == "__main__":
    sys.exit(main())
