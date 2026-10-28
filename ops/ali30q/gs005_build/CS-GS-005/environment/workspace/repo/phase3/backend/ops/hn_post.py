#!/usr/bin/env python3
"""hn_post.py — Hacker News 发帖器(逆向 web 流程;HN 无官方发帖 API)。

用法(凭据只从环境变量读,不落仓/不落日志):
  干跑(验证登录+表单 token,不发帖):
    HN_ACCT=xxx HN_PW=xxx python hn_post.py dryrun
  发布 text post:
    HN_ACCT=xxx HN_PW=xxx python hn_post.py post --title "..." --text-file body.txt

流程:login 拿 cookie → GET /submit 抽 fnid(表单 token)→ POST /r
(HN 两步提交:首次响应为确认页,带新 fnid,再 POST 一次)→ 302 到
/item?id=NNN → 独立验证(GET item 页核对标题/作者,验证优先于宣布)。

坑备忘:
- 默认 Python UA 会被 Cloudflare 拦 → 固定浏览器 UA(dev.to 同坑)
- HN 非官方接口,表单结构可能变 → dryrun 先行
"""

from __future__ import annotations

import argparse
import os
import re
import sys

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
BASE = "https://news.ycombinator.com"
FNID_RE = re.compile(r'name="fnid" value="([^"]+)"')
ITEM_RE = re.compile(r"item\?id=(\d+)")


def login(acct: str, pw: str) -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = UA
    r = s.post(
        f"{BASE}/login",
        data={"goto": "news", "acct": acct, "pw": pw},
        timeout=30,
    )
    if "Bad login" in r.text or "user" not in s.cookies:
        raise SystemExit("login failed (Bad login / no user cookie)")
    return s


def get_fnid(s: requests.Session) -> str:
    r = s.get(f"{BASE}/submit", timeout=30)
    m = FNID_RE.search(r.text)
    if not m:
        raise SystemExit("no fnid on /submit (form changed or not logged in?)")
    return m.group(1)


def post_text(s: requests.Session, title: str, text: str) -> int:
    """两步提交;返回新帖 item id。"""
    data = {"fnid": get_fnid(s), "title": title, "url": "", "text": text}
    r = s.post(f"{BASE}/r", data=data, timeout=30)
    for _ in range(2):  # 确认页最多再走一轮
        m = FNID_RE.search(r.text)
        final = ITEM_RE.search(r.url or "")
        if final and "item" in (r.url or ""):
            return int(final.group(1))
        if not m:
            break
        data = {"fnid": m.group(1), "title": title, "url": "", "text": text}
        r = s.post(f"{BASE}/r", data=data, timeout=30)
    # 兜底:响应体里的 item 链接
    ids = ITEM_RE.findall(r.text)
    if ids:
        return int(ids[0])
    raise SystemExit(f"submit failed (no item id; final url={r.url})")


def verify(item_id: int, acct: str, title: str) -> None:
    r = requests.get(f"{BASE}/item?id={item_id}", headers={"User-Agent": UA}, timeout=30)
    ok_title = f">{title}<" in r.text or title in r.text
    ok_author = f"user?id={acct}" in r.text
    if not (ok_title and ok_author):
        raise SystemExit(f"verify FAILED (title={ok_title} author={ok_author}) — 手查 {BASE}/item?id={item_id}")
    print(f"VERIFIED: {BASE}/item?id={item_id}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["dryrun", "post"])
    p.add_argument("--title")
    p.add_argument("--text-file")
    args = p.parse_args()

    acct = os.environ.get("HN_ACCT")
    pw = os.environ.get("HN_PW")
    if not acct:
        raise SystemExit("HN_ACCT not set (环境变量传入,勿写死)")
    if not pw:
        raise SystemExit("HN_PW not set (环境变量传入,勿写死)")

    s = login(acct, pw)
    fnid = get_fnid(s)
    print(f"login OK · fnid {fnid[:6]}…")
    if args.cmd == "dryrun":
        print("dryrun complete — 凭据与表单链路通,未发帖")
        return

    if not (args.title and args.text_file):
        raise SystemExit("post 需要 --title 与 --text-file")
    with open(args.text_file, encoding="utf-8") as f:
        body = f.read()
    item_id = post_text(s, args.title, body)
    print(f"submitted: item id {item_id}")
    verify(item_id, acct, args.title)


if __name__ == "__main__":
    sys.exit(main())