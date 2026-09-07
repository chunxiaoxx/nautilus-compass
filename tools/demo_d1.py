#!/usr/bin/env python
"""Demo D1 driver · cross-session memory (demo_recording_script.md 的可执行版).

60-90s 录屏用:写入三个"会话"→跨会话提问→空空间对照组。
走本地 daemon 9876(全本地叙事),token 同 stop_hook 配方。

Usage:
  python tools/demo_d1.py write 1|2|3   # 三次,每次一条"会话"事实
  python tools/demo_d1.py ask           # 跨会话问题(只有 session-1 能答)
  python tools/demo_d1.py control       # 空间对照组:同 query 打到空 project
  python tools/demo_d1.py reset         # 清掉 demo project,可重录
"""
from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path

HOST, PORT = "127.0.0.1", 9876
PROJECT = "DEMO-D1-20260907"          # demo 专用空间,reset 只清这个
CONTROL = "DEMO-D1-CONTROL"           # 永远为空的对照空间
FILES_LOG = Path(os.environ.get("TEMP", "/tmp")) / "demo_d1_files.txt"

SESSIONS = {
    "1": ("The user said they walk their dog every Tuesday morning; the dog's name is Momo.", "session-1"),
    "2": ("The user mentioned they are learning Rust, aiming to rewrite the company's data pipeline with it.", "session-2"),
    "3": ("The user complained that the weekly Monday standup keeps getting cancelled at the last minute.", "session-3"),
}
QUESTION = "What does the user do on Tuesday mornings?"


def _tok() -> str:
    p = Path.home() / ".claude" / ".cache" / "compass_daemon_token"
    try:
        return p.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def call(req: dict) -> dict:
    req = {**req, "token": _tok()}
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(60)
    try:
        s.connect((HOST, PORT))
        s.sendall((json.dumps(req) + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
        return json.loads(buf.decode("utf-8"))
    finally:
        s.close()


def write(n: str) -> None:
    text, fname = SESSIONS[n]
    r = call({"action": "ingest", "text": text, "project": PROJECT,
              "tier": "episodic", "filename": f"{fname}.md",
              "agent_type": "demo", "tags": ["demo-d1", fname]})
    if r.get("ok"):
        print(f"[ok] {fname} ingested -> {Path(r['path']).name} (embedded dim {r.get('embed_dim')})")
        with open(FILES_LOG, "a", encoding="utf-8") as f:
            f.write(r["path"] + "\n")
    else:
        print("[fail]", json.dumps(r, ensure_ascii=False)[:200])


def ask(project: str, label: str, expect_keywords: tuple[str, ...] = ()) -> None:
    r = call({"action": "recall", "query": QUESTION, "project": project, "top_k": 3})
    if not r.get("ok"):
        print(f"[{label} fail]", json.dumps(r, ensure_ascii=False)[:200])
        return
    hits = r.get("recall") or []
    print(f"[{label}] Q: {QUESTION}")
    if not hits:
        print("  (no hits — memory has nothing on this)")
        return
    for h in hits:
        txt = (h.get("body") or "")[:90].replace("\n", " ")
        print(f"  {h.get('score', '?'):.2f}  {h.get('path', '?')}  | {txt}")
    # 对照组叙事:近邻算法总会返回"最近的",是否真的能答要看内容。
    # expect_keywords 给出可答的关键要素;全部命中不含 → 明示"答不出"。
    if expect_keywords:
        relevant = any(all(k.lower() in (h.get("body") or "").lower()
                           for k in ("tuesday",)) and
                       any(k.lower() in (h.get("body") or "").lower()
                           for k in expect_keywords)
                       for h in hits)
        print("  -> ANSWERED: walks the dog (Momo)" if relevant
              else "  -> NO ANSWER in this memory space (only irrelevant hits)")


def reset() -> None:
    if not FILES_LOG.exists():
        print("nothing recorded to reset")
        return
    n = 0
    for line in FILES_LOG.read_text(encoding="utf-8").splitlines():
        p = Path(line)
        if p.exists() and "DEMO-D1" not in p.parts and p.suffix == ".md":
            continue  # safety: only touch demo-tagged paths
        if p.exists() and any("DEMO" in part for part in p.parts):
            p.unlink()
            n += 1
    FILES_LOG.unlink(missing_ok=True)
    print(f"[ok] removed {n} demo files; project space clean for a re-take")


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "write" and sys.argv[2] in SESSIONS:
        write(sys.argv[2])
    elif cmd == "ask":
        ask(PROJECT, "recall")
    elif cmd == "control":
        # daemon 对无目录 project 直接报错——对照组预置一条无关事实,
        # 让"空间存在但与问题无关"的对照成立(预期:无 Tuesday 相关命中)。
        r = call({"action": "ingest",
                  "text": "The office coffee machine broke last Thursday.",
                  "project": CONTROL, "tier": "episodic",
                  "filename": "irrelevant.md", "agent_type": "demo",
                  "tags": ["demo-d1", "control"]})
        if r.get("ok"):
            with open(FILES_LOG, "a", encoding="utf-8") as f:
                f.write(r["path"] + "\n")
        ask(CONTROL, "control", expect_keywords=("dog", "walk", "momo"))
    elif cmd == "reset":
        reset()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
