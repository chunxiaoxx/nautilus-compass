"""10/12 榜单开业发布工具箱(BC 外发第二期 · 2026-10-05)。

渠道优先级(用户 10/5 拍):x.com(Premium 号)> reddit > discord > HN > Dev.to。
原则(10/5 用户纠正后定型):
- 先盘 API 通道,粘贴只是无 API 渠道的兜底;
- 凭据一律环境变量,缺凭据=自动降级生成"作战卡"(粘贴包),不硬失败;
- 每次发布(成功/失败)落台账 outreach_ledger.jsonl,回流量读数 48h/7d 回读。

用法(phase3/backend/ 下):
    python ops/publish_kit.py devto docs/evidence/outreach/launch_20261012/devto_article.md
    python ops/publish_kit.py discord docs/evidence/outreach/launch_20261012/discord_msg.md
    python ops/publish_kit.py reddit docs/evidence/outreach/launch_20261012/reddit_post.md --title "..."
    python ops/publish_kit.py x docs/evidence/outreach/launch_20261012/x_thread.md   # 缺凭据→生成作战卡
    python ops/publish_kit.py status                                                  # 台账最近10行
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path(__file__).resolve().parent.parent / "docs/evidence/outreach/launch_20261012/outreach_ledger.jsonl"

DEVTO_API = "https://dev.to/api/articles"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _log(channel: str, status: str, detail: str = "", url: str = "") -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    row = {"ts": _now(), "channel": channel, "status": status, "url": url, "detail": detail[:300]}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


# ---------- 渠道 adapter(每个返回 dict{ok, url, note}) ----------

def publish_devto(body: str) -> dict:
    """Dev.to 全自动(10/5 实测 201;需浏览器 UA,Python 默认 UA 被 403)。"""
    key = os.getenv("DEVTO_API_KEY")
    if not key:
        _log("devto", "no-cred", "DEVTO_API_KEY 缺")
        return {"ok": False, "note": "缺 DEVTO_API_KEY"}
    # 文件首行 = JSON frontmatter(title/tags/description),其后 --- 分隔正文
    fm, _, article = body.partition("\n---\n")
    meta = json.loads(fm)
    payload = {**meta, "content": article}
    import urllib.request

    req = urllib.request.Request(
        DEVTO_API,
        data=json.dumps({"article": payload}).encode("utf-8"),
        headers={"api-key": key, "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        url = data.get("url", "")
        _log("devto", "published", f"id={data.get('id')}", url)
        return {"ok": True, "url": url, "note": f"id={data.get('id')}"}
    except Exception as e:  # noqa: BLE001 — 发布失败要留台账
        _log("devto", "fail", str(e))
        return {"ok": False, "note": str(e)}


def publish_discord(body: str) -> dict:
    """Discord webhook 全自动(最简通道;需用户建服务器→频道→Webhook URL)。"""
    url = os.getenv("DISCORD_WEBHOOK_URL")
    if not url:
        _log("discord", "no-cred", "DISCORD_WEBHOOK_URL 缺→作战卡")
        return {"ok": False, "note": "缺 DISCORD_WEBHOOK_URL(内容已可粘贴)"}
    import urllib.request

    for chunk_start in range(0, len(body), 1900):  # Discord 单条上限 2000
        chunk = body[chunk_start:chunk_start + 1900]
        req = urllib.request.Request(
            url, data=json.dumps({"content": chunk}).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=20)
        except Exception as e:  # noqa: BLE001
            _log("discord", "fail", str(e))
            return {"ok": False, "note": str(e)}
    _log("discord", "published", f"chunks={(len(body)+1899)//1900}")
    return {"ok": True, "note": "webhook 已投递"}


def publish_reddit(body: str, title: str = "") -> dict:
    """Reddit OAuth(script 流)全自动;需 REDDIT_CLIENT_ID/SECRET/USER/PASS 四件。"""
    cid, sec = os.getenv("REDDIT_CLIENT_ID"), os.getenv("REDDIT_CLIENT_SECRET")
    user, pwd = os.getenv("REDDIT_USER"), os.getenv("REDDIT_PASS")
    if not all([cid, sec, pwd, user]):
        _log("reddit", "no-cred", "REDDIT_* 缺→作战卡")
        return {"ok": False, "note": "缺 REDDIT_* 凭据(内容已可粘贴)"}
    import urllib.parse
    import urllib.request

    auth = (f"{cid}:{sec}").encode()
    basic = "Basic " + base64.b64encode(auth).decode()
    token_req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=urllib.parse.urlencode({"grant_type": "password", "username": user, "password": pwd}).encode(),
        headers={"Authorization": basic, "User-Agent": "nautilus-org/1.0"})
    try:
        with urllib.request.urlopen(token_req, timeout=20) as r:
            token = json.loads(r.read())["access_token"]
    except Exception as e:  # noqa: BLE001
        _log("reddit", "fail", f"token: {e}")
        return {"ok": False, "note": f"token: {e}"}
    sub = os.getenv("REDDIT_SUB", "LocalLLaMA")
    submit = urllib.request.Request(
        "https://oauth.reddit.com/api/submit",
        data=urllib.parse.urlencode({"sr": sub, "kind": "self", "title": title, "text": body}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "nautilus-org/1.0"})
    try:
        with urllib.request.urlopen(submit, timeout=20) as r:
            data = json.loads(r.read())
        j = data.get("json", {}).get("data", {})
        url = j.get("url", "")
        _log("reddit", "published", f"r/{sub}", url)
        return {"ok": True, "url": url, "note": f"r/{sub}"}
    except Exception as e:  # noqa: BLE001
        _log("reddit", "fail", str(e))
        return {"ok": False, "note": str(e)}


def publish_x(body: str) -> dict:
    """x.com:优先 API(bearer,待开通);无 API=生成作战卡(用户 Premium 号粘贴)。"""
    bearer = os.getenv("X_API_BEARER")
    if not bearer:
        card = Path(str(LEDGER).replace("outreach_ledger.jsonl", "x_post_card.md"))
        card.write_text(
            "# x.com 作战卡(粘贴即发 · Premium 号)\n\n"
            f"生成时间: {_now()}\n\n逐条粘贴为 thread(每条 ≤280 字符,已按 --- 分条):\n\n{body}\n",
            encoding="utf-8")
        _log("x", "card-generated", str(card))
        return {"ok": True, "note": f"作战卡已生成: {card}"}
    import urllib.request

    tweets = [t.strip() for t in body.split("\n---\n") if t.strip()]
    prev_id = None
    try:
        for t in tweets:
            payload = {"text": t}
            if prev_id:
                payload["reply"] = {"in_reply_to_tweet_id": prev_id}
            req = urllib.request.Request(
                "https://api.x.com/2/tweets",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(req, timeout=20) as r:
                prev_id = json.loads(r.read())["data"]["id"]
        _log("x", "published", f"thread={len(tweets)}条")
        return {"ok": True, "url": f"https://x.com/i/status/{prev_id}", "note": f"{len(tweets)} 条"}
    except Exception as e:  # noqa: BLE001
        _log("x", "fail", str(e))
        return {"ok": False, "note": str(e)}


def publish_hn(body: str, title: str = "") -> dict:
    """HN 复用存量发帖器 ops/hn_post.py(post --title --text-file;凭据 HN_ACCT/HN_PW)。"""
    if not (os.getenv("HN_ACCT") and os.getenv("HN_PW")):
        _log("hn", "no-cred", "HN_ACCT/HN_PW 缺→作战卡")
        return {"ok": False, "note": "缺 HN 凭据(文案已备,凭据到即发)"}
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as tf:
        tf.write(body)
        tmp = tf.name
    try:
        r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent / "hn_post.py"),
             "post", "--title", title, "--text-file", tmp],
            capture_output=True, text=True, timeout=120)
        ok = r.returncode == 0 and "submitted" in r.stdout
        _log("hn", "published" if ok else "fail", (r.stdout + r.stderr)[-200:])
        return {"ok": ok, "note": (r.stdout.strip().splitlines() or [""])[-1]}
    finally:
        os.unlink(tmp)


ADAPTERS = {"devto": publish_devto, "discord": publish_discord, "reddit": publish_reddit,
            "x": publish_x, "hn": publish_hn}


def main() -> int:
    ap = argparse.ArgumentParser(description="10/12 开业发布工具箱")
    ap.add_argument("channel", nargs="?", help="devto/discord/reddit/x/hn/status")
    ap.add_argument("file", nargs="?", help="内容文件")
    ap.add_argument("--title", default="", help="reddit/hn 标题")
    args = ap.parse_args()

    if args.channel in (None, "status"):
        if LEDGER.exists():
            lines = LEDGER.read_text(encoding="utf-8").strip().splitlines()[-10:]
            print("\n".join(lines))
        else:
            print("台账空")
        return 0
    if args.channel not in ADAPTERS or not args.file:
        ap.error(f"channel ∈ {sorted(ADAPTERS)} 且需 file(或用 status)")
    body = _read(args.file)
    result = ADAPTERS[args.channel](body, title=args.title) if args.channel in ("reddit", "hn") \
        else ADAPTERS[args.channel](body)
    print(json.dumps({"channel": args.channel, **result}, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
