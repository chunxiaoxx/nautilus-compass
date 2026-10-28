"""G2-B1 daily miner: 每日定时增量挖矿(schtasks g2b1_daily_miner · 每日 09:30)。

9/7 定时化(用户拍板「timer+幂等防重」):
- 五仓增量(g2_b1_bug_miner.mine,since=2.days.ago 窗口重叠,靠幂等挡重)
- 幂等键 = (repo_path 规范化, buggy_commit, reference_fix_commit),已在队列 → 跳过
  (历史批次正斜杠/反斜杠混用,norm_repo 统一后比对)
- append 队列;新行必带 repo_path(executor 按 task["repo_path"] 逐行消费)
- 锁防重入(LOCK_MAX_AGE 内第二实例即退;陈旧/损坏锁抢占)
- 只 append 不 commit:git 留痕交会话收口(R4);矿采完是常态,0 new 即静默退出

引导链:vbs(隐藏窗)→ cmd(cd + python 真身 + 日志重定向,治 schtasks 四层坑)。
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from g2_b1_bug_miner import mine  # noqa: E402

REPOS = [
    r"C:\Users\chunx\Projects\nautilus-core",
    r"C:\Users\chunx\Projects\nautilus-compass",
    r"C:\Users\chunx\Projects\nautilusflywheel",
    r"C:\Users\chunx\Projects\nautilus-fde-phase3",
    r"C:\Users\chunx\nautilus-v5",
]
QUEUE = (Path(__file__).resolve().parents[1]
         / "docs/evidence/g2b1_mine_20260827/deep_batch.jsonl")
LOCK_PATH = Path.home() / ".nautilus" / "g2b1_miner.lock"
SINCE = "2.days.ago"
LOCK_MAX_AGE = 30 * 60  # 秒;矿机单轮几分钟,超龄锁视为死锁抢占


def norm_repo(p: str | Path) -> str:
    return str(Path(p).resolve()).lower()


def queue_keys(rows: list[dict]) -> set[tuple[str, str, str]]:
    out: set[tuple[str, str, str]] = set()
    for r in rows:
        rp = r.get("repo_path")
        if not rp:
            continue  # 历史 row 缺 repo_path 无法构造键,保守不挡
        out.add((norm_repo(rp), r.get("buggy_commit", ""), r.get("reference_fix_commit", "")))
    return out


def dedupe(existing: set[tuple[str, str, str]], rows: list[dict]) -> list[dict]:
    kept = []
    for r in rows:
        key = (norm_repo(r["repo_path"]), r["buggy_commit"], r["reference_fix_commit"])
        if key not in existing:
            kept.append(r)
    return kept


def acquire_lock(path: Path, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    try:
        ts = float(path.read_text(encoding="utf-8").strip().split("|")[0])
    except (OSError, ValueError):
        ts = None
    if ts is not None and (now - ts) < LOCK_MAX_AGE:
        return False
    try:
        path.unlink()
    except OSError:
        pass
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(f"{now}|{os.getpid()}")
    return True


def release_lock(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def main() -> int:
    if not acquire_lock(LOCK_PATH):
        print("another miner instance holds the lock; exit", flush=True)
        return 0
    try:
        existing_rows = _read_jsonl(QUEUE)
        existing = queue_keys(existing_rows)
        candidates: list[dict] = []
        for repo in REPOS:
            root = Path(repo)
            if not (root / ".git").exists():
                print(f"skip missing repo: {repo}", flush=True)
                continue
            try:
                found = mine(root, since=SINCE)
            except Exception as exc:  # 单仓失败不拖垮其余仓
                print(f"mine {repo} failed: {exc}", flush=True)
                continue
            for r in found:
                r["repo_path"] = repo
            candidates.extend(found)
        fresh = dedupe(existing, candidates)
        with QUEUE.open("a", encoding="utf-8") as f:
            for r in fresh:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"mined {len(candidates)} candidates, {len(fresh)} new "
              f"-> queue now {len(existing_rows) + len(fresh)} rows", flush=True)
        return 0
    finally:
        release_lock(LOCK_PATH)


if __name__ == "__main__":
    raise SystemExit(main())
