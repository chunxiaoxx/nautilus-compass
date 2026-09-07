#!/usr/bin/env python
"""Reddit comment watch — launch-day read-only monitor (9/8 值守工具).

只读:拉新评论、标记已回复。不投票、不发帖、不自动回复——写侧永远人工
(launch_plan 红线:不买量不刷票不用小号;新账号 API 写入=shadowban 风险)。

Env(一次性配置,见 BENCHMARKS/README 或 9/8 runbook):
  REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET   # reddit.com/prefs/apps → script app
  REDDIT_USERNAME / REDDIT_PASSWORD

Usage:
  python tools/reddit_watch.py init <post_id>   # 定帖子+快照已有评论
  python tools/reddit_watch.py check            # 列出自上次 check 以来的新评论
  python tools/reddit_watch.py mark <comment_id># 标记已回复
  python tools/reddit_watch.py status           # 当前帖子/未回复数
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STATE = Path(__file__).resolve().parent / ".reddit_watch_state.json"


def _creds() -> dict:
    need = ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
            "REDDIT_USERNAME", "REDDIT_PASSWORD")
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        sys.exit(f"missing env: {', '.join(missing)}")
    return {k.lower().replace("reddit_", ""): os.environ[k] for k in need}


def _reddit():
    import praw
    c = _creds()
    return praw.Reddit(client_id=c["client_id"], client_secret=c["client_secret"],
                       username=c["username"], password=c["password"],
                       user_agent="nautilus-compass launch watch (read-only)")


def _load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"post_id": None, "seen": [], "replied": []}


def _save(s: dict) -> None:
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def _all_comments(sub) -> list[dict]:
    out = []
    sub.comments.replace_more(limit=0)
    for c in sub.comments.list():
        out.append({"id": c.id, "author": str(c.author),
                    "body": (c.body or "")[:500],
                    "score": c.score, "utc": int(c.created_utc)})
    return out


def init(post_id: str) -> None:
    s = _load()
    s["post_id"] = post_id
    s["seen"] = [c["id"] for c in _all_comments(_reddit().submission(id=post_id))]
    s["replied"] = [i for i in s.get("replied", []) if i in set(s["seen"])]
    _save(s)
    print(f"[ok] watching t3_{post_id} · {len(s['seen'])} existing comments snapshotted")


def check() -> None:
    s = _load()
    if not s.get("post_id"):
        sys.exit("run `init <post_id>` first")
    comments = _all_comments(_reddit().submission(id=s["post_id"]))
    fresh = [c for c in comments if c["id"] not in set(s["seen"])]
    pending = [c for c in comments
               if c["id"] not in set(s["replied"]) and c["id"] in set(s["seen"])]
    s["seen"] = [c["id"] for c in comments]
    _save(s)
    if not fresh and not pending:
        print(f"[quiet] no new comments · {len(comments)} total")
        return
    if fresh:
        print(f"=== NEW ({len(fresh)}) — draft replies for these ===")
        for c in fresh:
            print(f"--- {c['id']} · u/{c['author']} · score {c['score']}")
            print(f"    {c['body'][:400]}")
    if pending:
        print(f"=== UNREPLIED ({len(pending)}) — seen but not yet answered ===")
        for c in pending[:8]:
            print(f"--- {c['id']} · u/{c['author']}: {c['body'][:120]}")


def mark(cid: str) -> None:
    s = _load()
    if cid not in s["replied"]:
        s["replied"].append(cid)
        _save(s)
    print(f"[ok] {cid} marked replied ({len(s['replied'])} total)")


def status() -> None:
    s = _load()
    print(f"post: {s.get('post_id')} · seen {len(s['seen'])} · replied {len(s['replied'])}")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "init" and len(sys.argv) > 2:
        init(sys.argv[2])
    elif cmd == "check":
        check()
    elif cmd == "mark" and len(sys.argv) > 2:
        mark(sys.argv[2])
    elif cmd == "status":
        status()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
