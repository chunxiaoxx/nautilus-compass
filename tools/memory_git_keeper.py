#!/usr/bin/env python
"""Memory git keeper · frame-upgrade-20260904-compass #3 (letta MemFS 原则).

对会话所属项目的 ~/.claude/projects/<proj>/memory/: 有变化才 commit,
误改可回滚、版本可追溯。由 Stop hook 每次调用(见 ~/.claude/settings.json
hooks.Stop),任何失败静默退出(记忆 keeper 永不阻塞会话收尾)。

2026-09-06 平台代修:原版全量扫 */memory(本机 1513 个项目目录,Windows 下
仅 glob 即分钟级),每轮 Stop 把所有对话框拖到 49s+。改法:
- 主路径:从 stdin hook payload 的 transcript_path 提取项目目录名,只管当前会话(1513→1);
- fallback(无 stdin/提取失败):扫最近修改的 3 个 memory 目录;
- 墙钟预算 15s,超时立即放弃,下轮 Stop 继续增量保存。
"""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / ".claude" / "projects"
TIMEOUT = 10  # 单命令超时
BUDGET_S = 15  # 整体墙钟预算:keeper 永不拖垮收尾
FALLBACK_SCAN = 3  # 无 payload 时只碰最近活跃的 N 个项目


def _expired(deadline: float) -> bool:
    return time.monotonic() > deadline


def git(*args: str, cwd: Path, timeout: int = TIMEOUT) -> int:
    try:
        return subprocess.run(["git", *args], cwd=cwd, timeout=timeout,
                              capture_output=True, text=True).returncode
    except subprocess.TimeoutExpired:
        return 1  # 超时按失败处理,本轮跳过该目录


def _targets_from_stdin() -> list[Path]:
    """transcript_path = BASE/<proj>/<session>.jsonl → 只保存当前会话的项目。"""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return []
    tp = Path(payload.get("transcript_path") or "")
    if not tp.name:
        return []
    mem = BASE / tp.parent.name / "memory"
    return [mem] if mem.is_dir() else []


def _targets_recent() -> list[Path]:
    """fallback:无 payload(手动/异构调用)时,按 memory 目录 mtime 取最近 N 个。"""
    try:
        dirs = [d for d in BASE.glob("*/memory") if d.is_dir()]
        dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
        return dirs[:FALLBACK_SCAN]
    except OSError:
        return []


def _keep(mem: Path, deadline: float) -> None:
    if _expired(deadline):
        return
    if not (mem / ".git").exists():
        if git("init", "-q", cwd=mem) != 0:
            return
    if git("add", "-A", cwd=mem) != 0:
        return
    r = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=mem,
                       timeout=TIMEOUT, capture_output=True, text=True)
    if r.returncode == 0:
        return  # 无变化
    git("commit", "-q", "-m",
        "chore(memory): auto checkpoint (memory_git_keeper)", cwd=mem)


def main() -> int:
    if not BASE.exists():
        return 0
    deadline = time.monotonic() + BUDGET_S
    targets = _targets_from_stdin() or _targets_recent()
    for mem in targets:
        try:
            _keep(mem, deadline)
        except Exception:
            continue  # keeper 永不阻塞会话收尾
        if _expired(deadline):
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
