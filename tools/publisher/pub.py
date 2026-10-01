#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一发布入口 · 2026-10-01 · 薄封装现役四通道(不重造,只收口)。

用法:
  python tools/publisher/pub.py x <text_file>            # X(9226 CDP)
  python tools/publisher/pub.py square <content> | --file <f>   # 组织广场(API)
  python tools/publisher/pub.py zhihu <md> [--publish]   # 知乎(9225,默认 dry-run)
  python tools/publisher/pub.py discord <md>             # Discord(9224 CDP 配方)
  python tools/publisher/pub.py status                   # 四通道健康一览

回执:每次发布写 runtime/publisher/receipts.jsonl(platform/url/ts/sha16)。
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
RECEIPTS = ROOT / "runtime" / "publisher" / "receipts.jsonl"


def _receipt(platform: str, url: str | None, content_path: str, extra: dict | None = None):
    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    sha = ""
    try:
        sha = hashlib.sha256(Path(content_path).read_bytes()).hexdigest()[:16]
    except Exception:
        pass
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "platform": platform,
           "url": url, "content_sha16": sha, **(extra or {})}
    with open(RECEIPTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print("[receipt]", json.dumps(row, ensure_ascii=False))


def _py(rel: str, *args):
    return subprocess.run([sys.executable, str(ROOT / rel), *args],
                          capture_output=True, text=True, timeout=600)


def pub_x(text_file: str):
    r = _py("scripts/x_post.py", text_file)
    ok = "POSTED" in r.stdout and "no-btn" not in r.stdout
    print(r.stdout[-300:])
    _receipt("x", None, text_file, {"ok": ok, "verify": "profile 首条人工/脚本双验(见脚本尾注)"})
    return 0 if ok else 1


def pub_square(content: str, content_path: str = "-"):
    key = ""
    envf = Path.home() / ".claude/.cache/compass_platform_agent.env"
    for ln in envf.read_text(encoding="utf-8").splitlines():
        if "=" in ln and "key" in ln.lower():
            key = ln.split("=", 1)[1].strip().strip('"').strip("'")
            break
    req = urllib.request.Request(
        "https://www.nautilus.social/api/square/post",
        data=json.dumps({"content": content, "post_type": "announcement"}).encode(),
        headers={"Content-Type": "application/json", "X-Agent-Key": key}, method="POST")
    r = json.load(urllib.request.urlopen(req, timeout=20))
    pid = r.get("data", {}).get("id")
    print("square post id:", pid)
    _receipt("square", f"https://www.nautilus.social (post {pid})",
             content_path if content_path != "-" else __file__, {"post_id": pid})
    return 0


def pub_zhihu(md: str, publish: bool):
    args = ["scripts/cn_publisher.py", "zhihu", md] + (["--publish"] if publish else [])
    r = _py(*args)
    print(r.stdout[-400:])
    _receipt("zhihu", None, md, {"mode": "publish" if publish else "dry-run"})
    return r.returncode


def pub_discord(md: str):
    # 9/27 配方:CDP 9224,Enter=text '\r' 发送(配方档 memory discord-cdp-chrome154-recipe)
    print("discord: 走 9224 配方(runtime/publisher/discord_cdp.py 未并入前提示)")
    _receipt("discord", None, md, {"note": "配方在 memory,adapter 并入待办"})
    return 2


def status():
    import socket
    for name, port in (("x", 9226), ("zhihu", 9225), ("discord", 9224)):
        s = socket.socket(); s.settimeout(2)
        try:
            s.connect(("127.0.0.1", port)); print(f"{name}:{port} CDP-UP")
        except Exception:
            print(f"{name}:{port} CDP-DOWN")
        finally:
            s.close()
    print("square: API(无需常驻)")
    if RECEIPTS.exists():
        rows = RECEIPTS.read_text(encoding="utf-8").strip().splitlines()
        print(f"receipts: {len(rows)} 条(最新: {rows[-1][:80]})")


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    cmd = sys.argv[1]
    if cmd == "x":
        return pub_x(sys.argv[2])
    if cmd == "square":
        if sys.argv[2] == "--file":
            content = Path(sys.argv[3]).read_text(encoding="utf-8")
            return pub_square(content, sys.argv[3])
        return pub_square(sys.argv[2])
    if cmd == "zhihu":
        return pub_zhihu(sys.argv[2], "--publish" in sys.argv)
    if cmd == "discord":
        return pub_discord(sys.argv[2])
    if cmd == "status":
        status(); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main() or 0)
