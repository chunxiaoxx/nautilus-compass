"""RED test: per user 7/4 11:15 disclosure, the GPT-5.5 config below
must work end-to-end. User claims it works. If it doesn't, log details
so we can see exactly which piece fails (header? path? base? key?).

User config:
  ANTHROPIC_BASE_URL = https://v2.qixuw.com
  ANTHROPIC_AUTH_TOKEN = sk-c16301d1475dc595011320892cac17cd23d58d92d19a308668bf04b1878c84c8
  model_provider = OpenAI
  model = gpt-5.5
  review_model = gpt-5.5
  model_reasoning_effort = xhigh
  disable_response_storage = true
  base_url = https://v2.qixuw.com
  wire_api = responses
  requires_openai_auth = true
  OPENAI_API_KEY = sk-c16301d1475dc595011320892cac17cd23d58d92d19a308668bf04b1878c84c8
"""

from __future__ import annotations

import json
import os
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://v2.qixuw.com"
WIRE = "responses"
MODEL = "gpt-5.5"
REASONING_EFFORT = "xhigh"
KEY = os.environ.get("OPENAI_API_KEY", "")


def _post(url, body, headers, timeout=30):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return 0, f"URLError: {e.reason}"
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


def test_basic_gpt55_with_user_headers():
    """Test 1: user-provided headers verbatim. Should return 200 with content."""
    status, body = _post(
        BASE + "/" + WIRE,
        {
            "model": MODEL,
            "input": "Reply with exactly: PONG",
            "reasoning_effort": REASONING_EFFORT,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY}",
            "x-no-store": "true",
        },
    )
    print(f"[test 1] status={status}")
    print(f"[test 1] body[:400]={body[:400]}")
    assert status == 200, f"expected 200, got {status}: {body[:300]}"
    data = json.loads(body)
    # /v1/responses schema: output[].content[].text or output_text
    text = ""
    if "output" in data and data["output"]:
        for item in data["output"]:
            if isinstance(item, dict) and item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        text += c.get("text", "")
    assert "PONG" in text.upper(), f"expected PONG in response, got: {text!r}"


def test_chat_completions_fallback():
    """Test 2: try /v1/chat/completions on v2.qixuw.com (Anthropic path was claude)"""
    status, body = _post(
        BASE + "/v1/chat/completions",
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": "Reply with exactly: CHAT-OK"}],
            "max_tokens": 200,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY}",
            "x-no-store": "true",
        },
    )
    print(f"[test 2] /v1/chat/completions status={status}")
    print(f"[test 2] body[:300]={body[:300]}")
    # We don't assert success here — this is exploratory. Just log.
    return status, body


def test_responses_no_x_no_store():
    """Test 3: try without x-no-store header (maybe header is the issue)"""
    status, body = _post(
        BASE + "/" + WIRE,
        {
            "model": MODEL,
            "input": "Reply with exactly: NO-HEADER-OK",
            "reasoning_effort": REASONING_EFFORT,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY}",
        },
    )
    print(f"[test 3] no x-no-store status={status}")
    print(f"[test 3] body[:300]={body[:300]}")
    return status, body


def test_responses_no_reasoning_effort():
    """Test 4: try without reasoning_effort (maybe xhigh unsupported)"""
    status, body = _post(
        BASE + "/" + WIRE,
        {
            "model": MODEL,
            "input": "Reply with exactly: NO-EFFORT-OK",
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY}",
            "x-no-store": "true",
        },
    )
    print(f"[test 4] no reasoning_effort status={status}")
    print(f"[test 4] body[:300]={body[:300]}")
    return status, body


if __name__ == "__main__":
    print("=" * 60)
    print("RED test 1: gpt-5.5 /v1/responses with x-no-store + xhigh")
    print("=" * 60)
    try:
        test_basic_gpt55_with_user_headers()
        print("✅ TEST 1 PASSED")
    except AssertionError as e:
        print(f"❌ TEST 1 FAILED: {e}")
    except Exception as e:
        print(f"❌ TEST 1 ERRORED: {type(e).__name__}: {e}")

    print()
    print("=" * 60)
    print("EXPLORATORY test 2: /v1/chat/completions (no reasoning_effort)")
    print("=" * 60)
    test_chat_completions_fallback()

    print()
    print("=" * 60)
    print("EXPLORATORY test 3: no x-no-store header")
    print("=" * 60)
    test_responses_no_x_no_store()

    print()
    print("=" * 60)
    print("EXPLORATORY test 4: no reasoning_effort")
    print("=" * 60)
    test_responses_no_reasoning_effort()
