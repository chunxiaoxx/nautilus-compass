#!/usr/bin/env python
"""Memory git keeper · frame-upgrade-20260904-compass #3 (letta MemFS 原则).

对 ~/.claude/projects/*/memory/ 各目录: 有变化才 commit,误改可回滚、版本可追溯。
由 Stop hook 每次调用(见 ~/.claude/settings.json hooks.Stop),任何失败静默退出
(记忆 keeper 永不阻塞会话收尾)。

2026-09-06 · perf(HANDOFF_20260906_STOPHOOK_PERF_DAEMON):1513 个 memory 目录
逐个 spawn git add/diff = 0.21s/仓 ≈ 314s,把每轮 Stop 拖到 ~5 分钟。修法 =
mtime 预过滤:目录内 .md 全部早于窗口(默认 7 天,MEMKEEP_WINDOW_DAYS 可调)
则跳过——死目录零 git 调用,活跃目录行为不变(全目录覆盖保留,与被 revert 的
54e4a3a「只管当前项目」不同,不丢其他目录的 checkpoint 覆盖)。
"""
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / ".claude" / "projects"
TIMEOUT = 25  # 单目录单命令超时;大目录跳过,记忆 keeper 永不拖垮收尾


def _window_days() -> float:
    try:
        return float(os.environ.get("MEMKEEP_WINDOW_DAYS", "7"))
    except ValueError:
        return 7.0


def _has_recent_md(mem: Path, window_days: float) -> bool:
    """目录内任一 .md 的 mtime 在窗口内 → 视为活跃,才值得跑 git。"""
    cutoff = time.time() - window_days * 86400.0
    try:
        for p in mem.rglob("*.md"):
            try:
                if p.stat().st_mtime > cutoff:
                    return True
            except OSError:
                continue
    except OSError:
        return False
    return False


def git(*args: str, cwd: Path) -> int:
    try:
        return subprocess.run(["git", *args], cwd=cwd, timeout=TIMEOUT,
                              capture_output=True, text=True).returncode
    except subprocess.TimeoutExpired:
        return 0


def main() -> int:
    if not BASE.exists():
        return 0
    window = _window_days()
    for mem in BASE.glob("*/memory"):
        if not _has_recent_md(mem, window):
            continue  # 窗口外的死目录:零 git 调用(1513 仓的绝大多数)
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
