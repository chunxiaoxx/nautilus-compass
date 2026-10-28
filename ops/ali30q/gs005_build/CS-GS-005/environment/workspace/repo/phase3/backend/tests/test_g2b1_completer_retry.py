# -*- coding: utf-8 -*-
"""completer 重试路径单测(9/8:题10 揭出 ReadTimeout 首试后 UnboundLocalError)。

bug:attempt-1 ReadTimeout 被捕获后未 continue,代码掉到 response.status_code
引用未绑定变量 → 等 30 分钟后崩掉整题。修 = except 里 continue 重试 attempt-2。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import g2_b1_executor_agent as ex  # noqa: E402

httpx = pytest.importorskip("httpx")


def test_readtimeout_first_attempt_retries(monkeypatch):
    """首试 ReadTimeout → 第二次必须真正发出请求并成功(而不是崩溃)。"""
    calls = {"n": 0}

    class _Resp:
        status_code = 200
        text = '{"choices":[{"message":{"content":"ok"}}],"usage":{}}'

        def json(self):
            return {"choices": [{"message": {"content": "ok"}}],
                    "usage": {}, "model": "m"}

    class _Client:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **kw):
            calls["n"] += 1
            if calls["n"] == 1:
                raise httpx.ReadTimeout("first-token stall")
            return _Resp()

    monkeypatch.setattr(ex.httpx, "Client", _Client)
    monkeypatch.setattr(ex.os.environ, "get", lambda k, d=None: "k" if k.endswith("API_KEY") else d, raising=False)
    complete = ex.make_completer("chunxiao_k3")
    out = complete("prompt")
    assert out["content"] == "ok"
    assert calls["n"] == 2


def test_readtimeout_second_attempt_raises(monkeypatch):
    """两次都 ReadTimeout → 必须抛出(不能静默成功)。"""
    class _Client:
        def __init__(self, **kw):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, *a, **kw):
            raise httpx.ReadTimeout("still stalled")

    monkeypatch.setattr(ex.httpx, "Client", _Client)
    monkeypatch.setattr(ex.os.environ, "get", lambda k, d=None: "k" if k.endswith("API_KEY") else d, raising=False)
    complete = ex.make_completer("chunxiao_k3")
    with pytest.raises(httpx.ReadTimeout):
        complete("prompt")
