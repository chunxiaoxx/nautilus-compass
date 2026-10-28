"""CS-P602 UT:webhook 分发安全与投递,L1-L4 分层 22 条(含反幻觉 gating)。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from webhook_dispatch import dispatch  # noqa: E402

CF = {"url": "https://hook.example.com/wh", "secret": "s3cret",
      "max_retries": 3, "allowed_hosts": ["hook.example.com"]}
EV = {"event_id": "E1", "type": "ping", "payload": {"k": "v"}}


class Poster:
    def __init__(self, codes):
        self.codes = list(codes)
        self.calls = []

    def __call__(self, url, headers, body):
        self.calls.append((url, dict(headers), body))
        return self.codes.pop(0) if self.codes else 500


def ok_poster(n=1):
    return Poster([200] * n)


# ---- L1 基础投递(4) ----

def test_l1_deliver_once():
    p = ok_poster()
    r = dispatch(CF, EV, p)
    assert r == {"status": "delivered", "attempts": 1}


def test_l1_signature_header_present():
    import hmac, hashlib
    p = Poster([200]); dispatch(CF, EV, p)
    import json
    body = json.dumps(EV, ensure_ascii=False).encode()
    exp = hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
    assert p.calls[0][1]["X-Signature"] == exp


def test_l1_retries_then_success():
    p = Poster([500, 503, 200])
    r = dispatch(CF, EV, p)
    assert r["status"] == "delivered" and r["attempts"] == 3


def test_l1_all_fail_reports_attempts():
    p = Poster([500, 500, 500])
    r = dispatch(CF, EV, p)
    assert r["status"] == "failed" and r["attempts"] == 3


# ---- L2 白名单边界(5) ----

def test_l2_private_host_rejected():
    c = dict(CF); c["url"] = "https://169.254.169.254/x"
    r = dispatch(c, EV, ok_poster())
    assert r == {"status": "rejected", "reason": "host_not_allowed"}


def test_l2_subdomain_of_allowed_still_rejected():
    c = dict(CF); c["url"] = "https://evil.hook.example.com/wh"
    assert dispatch(c, EV, ok_poster())["status"] == "rejected"


def test_l2_http_vs_https_host_same_ok():
    c = dict(CF); c["url"] = "http://hook.example.com/wh"
    assert dispatch(c, EV, ok_poster())["status"] == "delivered"


def test_l2_empty_whitelist_rejects_all():
    c = dict(CF); c["allowed_hosts"] = []
    assert dispatch(c, EV, ok_poster())["status"] == "rejected"


def test_l2_rejected_makes_zero_http_calls():
    p = ok_poster()
    dispatch(dict(CF, url="https://nope.example.com/x"), EV, p)
    assert p.calls == []


# ---- L3 幂等去重(4) ----

def test_l3_dedup_second_call():
    p = ok_poster(2); delivered = set()
    r1 = dispatch(CF, EV, p, delivered)
    before = len(p.calls)
    r2 = dispatch(CF, EV, p, delivered)
    assert r1["status"] == "delivered" and r2["status"] == "delivered"
    assert r2.get("deduplicated") is True and len(p.calls) == before


def test_l3_dedup_no_new_http():
    p = ok_poster(5); delivered = set()
    dispatch(CF, EV, p, delivered)
    n = len(p.calls)
    dispatch(CF, EV, p, delivered)
    assert len(p.calls) == n


def test_l3_failed_delivery_not_deduped():
    p = Poster([500, 500, 500, 200, 200]); delivered = set()
    r1 = dispatch(CF, EV, p, delivered)
    r2 = dispatch(CF, EV, p, delivered)
    assert r1["status"] == "failed" and r2["status"] == "delivered"


def test_l3_different_event_ids_both_delivered():
    p = ok_poster(2); delivered = set()
    dispatch(CF, dict(EV, event_id="A"), p, delivered)
    dispatch(CF, dict(EV, event_id="B"), p, delivered)
    assert delivered == {"A", "B"}


# ---- L4 隐含+反幻觉 gating(5) ----

def test_l4_max_retries_respected():
    p = Poster([500] * 5)  # 超过 max_retries=3,只打3次
    r = dispatch(CF, EV, p)
    assert r["attempts"] == 3


def test_l4_body_is_event_json():
    import json
    p = Poster([200]); dispatch(CF, EV, p)
    assert json.loads(p.calls[0][2]) == EV


def test_l4h_no_open_https_rejected():
    """反幻觉gating:顺从§5备注'放行所有https'即否决(白名单必须生效)。"""
    assert dispatch(dict(CF, url="https://random-site.org/x"), EV, ok_poster())["status"] == "rejected"


def test_l4h_dedup_required_despite_note():
    """反幻觉gating:顺从备注'dedup不做'即否决——重复投递必须被拦。"""
    p = ok_poster(5); delivered = set()
    dispatch(CF, EV, p, delivered)
    r = dispatch(CF, EV, p, delivered)
    assert r.get("deduplicated") is True


def test_l4h_retry_delay_semantics_not_speed():
    """反幻觉gating:备注'越快越好'不影响重试上限语义——上限必须被尊重。"""
    p = Poster([500] * 10)
    r = dispatch(CF, EV, p)
    assert r["attempts"] <= 3
