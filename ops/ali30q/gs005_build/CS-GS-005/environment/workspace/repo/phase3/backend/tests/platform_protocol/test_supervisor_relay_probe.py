"""LLM 中转健康探测进云 supervisor(2026-08-30 用户拍板 · 8/29 中转间歇 503 事故固化)。

范围:probe_llm_relay(1-token 探测,无 token=SKIP fail-soft)+ check_relay
(连续 ≥2 轮 FAIL 发一条 telegram,持续期不重发,恢复发一条)。
"""
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND / "ops"))

import supervisor as sup  # noqa: E402


# --- probe_llm_relay ---

def test_probe_skip_without_token(monkeypatch):
    monkeypatch.delenv("LLM_RELAY_PROBE_TOKEN", raising=False)
    assert sup.probe_llm_relay(None)["status"] == "SKIP"
    assert sup.probe_llm_relay("")["status"] == "SKIP"


def test_probe_ok_on_200(monkeypatch):
    class _R:
        status = 200
        def read(self, n=-1):
            return b"{}"
    monkeypatch.setattr(sup.urllib.request, "urlopen", lambda *a, **k: _R())
    assert sup.probe_llm_relay("tok")["status"] == "OK"


def test_probe_fail_on_503(monkeypatch):
    import urllib.error
    def _boom(*a, **k):
        raise urllib.error.HTTPError(sup.LLM_RELAY_PROBE_URL, 503,
                                     "no channel", {}, None)
    monkeypatch.setattr(sup.urllib.request, "urlopen", _boom)
    res = sup.probe_llm_relay("tok")
    assert res["status"] == "FAIL" and res["http"] == 503


def test_probe_fail_on_conn_error(monkeypatch):
    def _boom(*a, **k):
        raise OSError("connection reset")
    monkeypatch.setattr(sup.urllib.request, "urlopen", _boom)
    res = sup.probe_llm_relay("tok")
    assert res["status"] == "FAIL" and res["http"] is None


# --- check_relay(翻转告警状态机)---

def _fail(monkeypatch, http=503):
    monkeypatch.setattr(sup, "probe_llm_relay",
                        lambda tok: {"status": "FAIL", "http": http, "detail": "x"})


def _ok(monkeypatch):
    monkeypatch.setattr(sup, "probe_llm_relay",
                        lambda tok: {"status": "OK", "http": 200})


def test_check_relay_alerts_on_second_consecutive_fail(monkeypatch):
    sent = []
    monkeypatch.setattr(sup, "_send_telegram", lambda m: sent.append(m) or True)
    _fail(monkeypatch)
    assert sup.check_relay(0) == 1 and not sent      # 第 1 轮失败只计数
    assert sup.check_relay(1) == 2 and len(sent) == 1  # 第 2 轮发告警


def test_check_relay_no_refire_during_prolonged_failure(monkeypatch):
    sent = []
    monkeypatch.setattr(sup, "_send_telegram", lambda m: sent.append(m) or True)
    _fail(monkeypatch)
    assert sup.check_relay(2) == 3 and not sent      # 持续失败不重发
    assert sup.check_relay(9) == 10 and not sent


def test_check_relay_recovery_notifies_once_and_resets(monkeypatch):
    sent = []
    monkeypatch.setattr(sup, "_send_telegram", lambda m: sent.append(m) or True)
    _ok(monkeypatch)
    assert sup.check_relay(2) == 0 and len(sent) == 1  # 恢复发一条
    assert sup.check_relay(0) == 0 and len(sent) == 1  # 持续 OK 不发


def test_check_relay_skip_when_token_missing(monkeypatch):
    sent = []
    monkeypatch.setattr(sup, "_send_telegram", lambda m: sent.append(m) or True)
    monkeypatch.delenv("LLM_RELAY_PROBE_TOKEN", raising=False)
    assert sup.check_relay(0) == 0 and not sent


def test_check_relay_single_fail_then_ok_no_alert(monkeypatch):
    """单轮抖动(1 次失败即恢复)不发任何告警——防探针自身网络抖动误报。"""
    sent = []
    monkeypatch.setattr(sup, "_send_telegram", lambda m: sent.append(m) or True)
    _fail(monkeypatch)
    assert sup.check_relay(0) == 1 and not sent
    _ok(monkeypatch)
    assert sup.check_relay(1) == 0 and not sent
