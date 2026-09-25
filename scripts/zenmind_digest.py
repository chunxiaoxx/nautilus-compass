# -*- coding: utf-8 -*-
"""禅心(台式机)→compass 平台信箱 digest 投递器 · 自包含纯 stdlib。

部署在台式机(禅心所在机器)。两种模式:
  --scan   机械扫描本机 ~/.claude/projects/*/ 最近会话,生成结构化 digest 并投递
  --file F 投递禅心自己写好的 digest 文件(F=markdown 正文)

投递目标:https://nautilus.social/api/platform/org/mailbox (to=compass)
鉴权:X-API-Key,读取 %USERPROFILE%\\.claude\\.cache\\zenmind_mailkey.env
     (key 由 platform 签发,见 SETUP 文档;无 key 时尝试裸发并明确报错)。

用法示例(Windows 计划任务每日 22:00):
  python zenmind_digest.py --scan
  python zenmind_digest.py --file C:/zenmind/digest_20260926.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://nautilus.social/api/platform/org/mailbox"
KEYFILE = Path.home() / ".claude" / ".cache" / "zenmind_mailkey.env"
PROJECTS = Path.home() / ".claude" / "projects"
FROM = "zenmind"
TO = "compass"
TRACE_PREFIX = "zenmind-digest"
MAX_PROJECTS = 12          # 单封 digest 最多覆盖的项目数
MAX_SESSIONS_PER = 1       # 每项目只取最近 1 个会话
MAX_USER_MSGS = 5          # 每会话抽取最近 5 条用户消息线索


def _key() -> str | None:
    k = os.environ.get("ZENMIND_MAILKEY")
    if k:
        return k.strip()
    if KEYFILE.is_file():
        for line in KEYFILE.read_text(encoding="utf-8").splitlines():
            if line.startswith(("X-API-KEY=", "ZENMIND_MAILKEY=")):
                return line.split("=", 1)[1].strip()
    return None


def _safe_text(x) -> str:
    """剥嵌套结构,取人话文本,压空白,截 160。"""
    if isinstance(x, str):
        t = x
    elif isinstance(x, dict):
        t = x.get("text") or x.get("content") or json.dumps(x, ensure_ascii=False)
    else:
        t = json.dumps(x, ensure_ascii=False)
    return " ".join(t.split())[:160]


def scan() -> str:
    today = dt.date.today().isoformat()
    rows = []
    for proj in sorted(PROJECTS.glob("*/"),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:MAX_PROJECTS]:
        jsonls = sorted(proj.glob("*.jsonl"), key=lambda f: f.stat().st_mtime,
                        reverse=True)[:MAX_SESSIONS_PER]
        for jf in jsonls:
            users = []
            try:
                with jf.open(encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                for line in reversed(lines):
                    if len(users) >= MAX_USER_MSGS:
                        break
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue
                    if d.get("type") == "user" and not d.get("isMeta"):
                        msg = d.get("message", {})
                        c = msg.get("content")
                        if isinstance(c, list):  # 取首个 text 块
                            c = next((b.get("text") for b in c
                                      if isinstance(b, dict)
                                      and b.get("type") == "text"), None)
                        if c and not str(c).lstrip().startswith("<"):
                            users.append(_safe_text(c))
            except OSError:
                continue
            mt = dt.datetime.fromtimestamp(jf.stat().st_mtime)
            rows.append((proj.name, mt, jf.name[:8], list(reversed(users))))
    out = [f"# 禅心 digest · {today}(机械扫描版,禅心可补写人工摘要覆盖)", ""]
    if not rows:
        out.append("(本机无 claude 会话记录)")
    for name, mt, sid, users in rows:
        out.append(f"## {name} · 最近会话 {sid} · {mt:%m-%d %H:%M}")
        for u in users:
            out.append(f"- {u}")
        out.append("")
    out.append("<!-- 隐私边界:仅含会话时间戳与用户消息截断线索,无密钥无工件内容 -->")
    return "\n".join(out)


def send(body: str, title: str) -> int:
    key = _key()
    payload = {"from_agent": FROM, "to_agent": TO,
               "trace_id": f"{TRACE_PREFIX}-{dt.date.today().isoformat()}",
               "title": title, "body": body,
               "deadline": (dt.datetime.now() + dt.timedelta(days=2)
                            ).strftime("%Y-%m-%d %H:%M:%S")}
    req = urllib.request.Request(
        BASE, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 **({"X-API-Key": key} if key else {})}, method="POST")
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:200]
        print(f"[FAIL] HTTP {e.code}: {detail}")
        print("  无 key 或 key 无效→按 SETUP 文档向 platform 申请 zenmind key")
        return 1
    if r.get("success"):
        print(f"[OK] id {r.get('data', {}).get('id')} · key={'✓' if key else '✗(宽限?)'}")
        return 0
    print(f"[FAIL] {json.dumps(r, ensure_ascii=False)[:200]}")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scan", action="store_true")
    g.add_argument("--file")
    a = ap.parse_args()
    if a.scan:
        body = scan()
        title = f"[禅心 digest] {dt.date.today().isoformat()} 台式机会话机械摘要"
    else:
        body = Path(a.file).read_text(encoding="utf-8")
        title = f"[禅心 digest] {dt.date.today().isoformat()} 摘要"
    return send(body, title)


if __name__ == "__main__":
    sys.exit(main())
