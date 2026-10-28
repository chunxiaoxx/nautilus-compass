#!/usr/bin/env python3
"""LLM 通道探针:对 .env 里全部候选凭据实测 chat,报活通道。"""
import sys

sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")
from dotenv import load_dotenv
load_dotenv("/home/ubuntu/nautilus-mvp/phase3/backend/.env")
import os

from anthropic import Anthropic

CASES = [
    ("minimax-token-plan", os.getenv("MINIMAX_TOKEN_PLAN_KEY"), "https://api.minimaxi.com/anthropic"),
    ("chunxiao-relay", os.getenv("CHUNXIAO_API_KEY"), os.getenv("CHUNXIAO_BASE_URL")),
    ("minimax-old-key", os.getenv("MINIMAX_API_KEY"), "https://api.minimaxi.com/anthropic"),
]
for name, key, url in CASES:
    if not key or not url:
        print(f"[{name}] SKIP (no key/url)")
        continue
    try:
        c = Anthropic(api_key=key, base_url=url, timeout=30)
        r = c.messages.create(model="claude-sonnet-4-5-20250929", max_tokens=16,
                              messages=[{"role": "user", "content": "回复ok两个字母"}])
        print(f"[{name}] OK -> {r.content[0].text[:30]}")
    except Exception as e:
        print(f"[{name}] FAIL {type(e).__name__} {str(e)[:100]}")
