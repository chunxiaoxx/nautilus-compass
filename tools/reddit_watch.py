#!/usr/bin/env python
"""Reddit comment watch — launch-day read-only monitor (9/8 值守工具).

只读,零凭据:走 Reddit 公开 .json 端点(浏览器等价读取,单帖低频轮询),
不需要 API app(Responsible Builder Policy 对新账号关了 API 申请也没关系)。
不投票、不发帖、不自动回复——写侧永远人工(launch_plan 红线)。

Usage:
  python tools/reddit_watch.py init <post_url_or_id>  # 定帖子+快照已有评论
  python tools/reddit_watch.py check                  # 新评论+未回复列表
  python tools/reddit_watch.py mark <comment_id>      # 标记已回复
  python tools/reddit_watch.py status
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

STATE = Path(__file__).resolve().parent / ".reddit_watch_state.json"
UA = ("nautilus-compass-launch-watch/1.0 (read-only comment monitor; "
      "contact via github.com/chunxiaoxx/nautilus-compass)")


def _fetch_json(url: str) -> dict:
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _normalize_post(ref: str) -> str:
    m = re.search(r"comments/([a-z0-9]+)", ref)
    return m.group(1) if m else ref.strip()


def _all_comments(post_id: str) -> list[dict]:
    data = _fetch_json(f"https://www.reddit.com/comments/{post_id}.json?limit=500")
    out: list[dict] = []

    def walk(children: list) -> None:
        for ch in children:
            node = ch.get("data", {})
            body = node.get("body")
            if body:  # comments have body; the submission node doesn't
                out.append({"id": node.get("id", ""), "author": node.get("author", ""),
                            "body": body[:500], "score": node.get("score", 0),
                            "utc": int(node.get("created_utc", 0))})
            replies = node.get("replies")
            if isinstance(replies, dict):
                walk(replies.get("data", {}).get("children", []))

    walk(data[1].get("data", {}).get("children", []))
    return out


def _load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"post_id": None, "seen": [], "replied": []}


def _save(s: dict) -> None:
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")


def init(ref: str) -> None:
    pid = _normalize_post(ref)
    comments = _all_comments(pid)
    s = {"post_id": pid, "seen": [c["id"] for c in comments],
         "replied": [i for i in _load().get("replied", [])]}
    _save(s)
    print(f"[ok] watching {pid} · {len(comments)} existing comments snapshotted")


def check() -> None:
    s = _load()
    if not s.get("post_id"):
        sys.exit("run `init <post_url>` first")
    time.sleep(0.5)  # gentle pacing
    comments = _all_comments(s["post_id"])
    seen_set = set(s["seen"])
    fresh = [c for c in comments if c["id"] not in seen_set]
    replied_set = set(s["replied"])
    pending = [c for c in comments
               if c["id"] in seen_set and c["id"] not in replied_set]
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
        print(f"=== UNREPLIED ({len(pending)}) — seen, not yet answered ===")
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
