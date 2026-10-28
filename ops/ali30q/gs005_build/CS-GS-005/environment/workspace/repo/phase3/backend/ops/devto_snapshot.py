# -*- coding: utf-8 -*-
"""Dev.to 内容线读数(10/4 用户批"扶上马送一程"件②):取最近 7 天发布文章的
互动/评论数,写人话段落到 /tmp/devto_digest.txt,由 digest_human 附进每日日报。
fail-open:任何异常不写文件,digest 照常出(内容线段缺席≠日报失败)。
API 配方(10/4 实测):api-key 头+浏览器 UA(Python 默认 UA 被 403 Forbidden Bots),
列表端点 /api/articles/me/all 不带参数(per_page 曾 404)。
云端跑:python3 ops/devto_snapshot.py"""
from __future__ import annotations

import json
import os
import urllib.request as u
from datetime import datetime, timedelta, timezone

OUT = "/tmp/devto_digest.txt"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def main() -> None:
    key = None
    for _p in (".env", "/home/ubuntu/nautilus-mvp/phase3/backend/.env"):
        for _l in open(_p, encoding="utf-8"):
            if _l.startswith("DEVTO_API_KEY="):
                key = _l.split("=", 1)[1].strip()
    assert key, "DEVTO_API_KEY not found"
    req = u.Request("https://dev.to/api/articles/me/all",
                    headers={"api-key": key, "User-Agent": UA})
    arts = json.loads(u.urlopen(req, timeout=30).read())
    pub = [a for a in arts if a.get("published")]
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent = []
    for a in pub:
        ts = a.get("published_at") or a.get("created_at")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if dt >= cutoff:
            recent.append((dt, a))
    recent.sort(reverse=True)
    total_react = sum(a.get("positive_reactions_count", 0) for a in pub)
    total_comment = sum(a.get("comments_count", 0) for a in pub)
    L = [f"公开文章 {len(pub)} 篇;近 7 天新增 {len(recent)} 篇;"
         f"累计互动 {total_react}、评论 {total_comment}。"]
    for dt, a in recent:
        title = (a.get("title") or "")[:48]
        L.append(f"- {dt:%m/%d} 《{title}》 互动 {a.get('positive_reactions_count', 0)}"
                 f" 评论 {a.get('comments_count', 0)}")
    open(OUT, "w", encoding="utf-8").write("\n".join(L))
    print(f"devto snapshot ok: {len(recent)} recent / {len(pub)} total")


if __name__ == "__main__":
    main()
