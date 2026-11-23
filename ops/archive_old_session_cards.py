#!/usr/bin/env python3
"""旧 session 卡滚出检索池 → 归档层(2026-11-23,C 项目检索池治理第 3 件配套)。

- 只移动 session_*.md(mtime 超过 ARCHIVE_AGE_DAYS,默认 30 天)到 _archive/YYYY-MM/。
- 非 session 卡(手写规格/反馈等)与 MEMORY.MD/INDEX.MD 永不移动。
- 同文件系统 mv = 可逆;每次移动写入 _archive/ARCHIVE_MANIFEST.jsonl 留痕。
- 默认 dry-run 只报数;--apply 才执行。flock 防双跑。
"""
import argparse
import fcntl
import json
import os
import pathlib
import sys
import time

SRC = pathlib.Path.home() / ".claude/projects/C--Users-chunx/memory"
ARCHIVE = SRC / "_archive"
MANIFEST = ARCHIVE / "ARCHIVE_MANIFEST.jsonl"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--age-days", type=int,
                        default=int(os.environ.get("ARCHIVE_AGE_DAYS", "30")))
    args = parser.parse_args()

    cutoff = time.time() - args.age_days * 86400
    cards = sorted(SRC.glob("session_*.md"))
    old = [p for p in cards if p.stat().st_mtime < cutoff]
    by_month = {}
    for p in old:
        month = time.strftime("%Y-%m", time.localtime(p.stat().st_mtime))
        by_month[month] = by_month.get(month, 0) + 1

    print(json.dumps({
        "mode": "apply" if args.apply else "dry-run",
        "src": str(SRC),
        "pool_root_session": len(cards) - len(old),
        "to_archive": len(old),
        "by_month": dict(sorted(by_month.items())),
        "protected_non_session": len(list(SRC.glob("*.md"))) - len(cards),
    }, ensure_ascii=False))

    if not args.apply:
        return 0

    ARCHIVE.mkdir(parents=True, exist_ok=True)
    lock_path = ARCHIVE / ".archive.lock"
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        moved = 0
        errors = 0
        with MANIFEST.open("a", encoding="utf-8") as mf:
            for p in old:
                try:
                    mt = p.stat().st_mtime  # 改名前先取,旧路径改后即失效
                    month = time.strftime("%Y-%m", time.localtime(mt))
                    dest_dir = ARCHIVE / month
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    dest = dest_dir / p.name
                    if dest.exists():
                        continue
                    os.rename(p, dest)
                    mf.write(json.dumps({
                        "moved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "file": p.name,
                        "from": str(p), "to": str(dest),
                        "mtime": mt,
                    }, ensure_ascii=False) + "\n")
                    moved += 1
                    if moved % 5000 == 0:
                        print(f"moved {moved}/{len(old)}", file=sys.stderr)
                except FileNotFoundError:
                    errors += 1  # 并发消失(新写入竞争等),跳过不中断
        print(json.dumps({"applied": True, "moved": moved, "errors": errors},
                         ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
