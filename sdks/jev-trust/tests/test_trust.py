# -*- coding: utf-8 -*-
import json

import pytest

from jev_trust import (TrustedJev, TrustResult, UNVERIFIED, FACE_VALUE,
                       top_label, correctness)
from jev_trust.client import JevAPIError
from jev_trust.receipt import KeyPair, verify_log


def fake_transport_factory(answers, calls=None):
    def transport(url, body, headers):
        if calls is not None:
            calls.append(json.loads(body))
        return {"answers": answers, "usage": {"input_tokens": 10, "output_tokens": 5}}
    return transport


NOUL_YES = {"type": "noul", "noul": 0.93}
CHOICE_A = {"type": "choice", "choice": "alpha", "confidence": 0.91,
            "probabilities": {"alpha": 0.91, "beta": 0.06, "gamma": 0.03}}


class TestNormalize:
    def test_noul(self):
        t = top_label(NOUL_YES)
        assert t["decision"] == "yes" and t["stated_confidence"] == 0.93

    def test_noul_no(self):
        t = top_label({"type": "noul", "noul": 0.1})
        assert t["decision"] == "no" and t["stated_confidence"] == 0.9

    def test_choice(self):
        t = top_label(CHOICE_A)
        assert t["decision"] == "alpha" and t["stated_confidence"] == 0.91

    def test_correctness(self):
        assert correctness(top_label(NOUL_YES), 1) == 1
        assert correctness(top_label(NOUL_YES), 0) == 0
        assert correctness(top_label(CHOICE_A), "alpha") == 1
        assert correctness(top_label(CHOICE_A), "beta") == 0
        with pytest.raises(ValueError):
            correctness(top_label({"type": "score", "score": 0.8}), 1)


class TestDecide:
    def test_first_call_is_unverified(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory({"q": dict(NOUL_YES)}))
        r = jev.decide({"a": 1}, {"q": {"type": "noul", "instructions": "a>0?"}})["q"]
        assert isinstance(r, TrustResult)
        assert r.stated_confidence == 0.93
        assert r.domain_verdict == UNVERIFIED
        assert r.effective_confidence is None
        assert r.basis == UNVERIFIED
        assert jev.log_path.exists()
        lines = jev.log_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1 and json.loads(lines[0])["kind"] == "call"

    def test_outcome_updates_stats(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory({"q": dict(NOUL_YES)}))
        jev.decide({"a": 1}, {"q": {"type": "noul", "instructions": "a>0?"}})
        pred = jev.record_outcome("q", 1)
        assert pred.correct == 1 and pred.p_true == 0.93
        s = jev.stats()
        assert s["n_outcomes"] == 1 and s["accuracy"] == 1.0
        # single sample: bin acc 1.0 vs conf 0.93 -> ECE 0.07, C 0.93
        assert s["ece"] == 0.07 and s["C"] == 0.93
        assert s["brier"] == 0.0049  # (1 - 0.93)^2

    def test_choice_outcome_and_brier(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory({"q": dict(CHOICE_A)}))
        jev.decide({}, {"q": {"type": "choice", "instructions": "?", "criteria": {}}})
        pred = jev.record_outcome("q", "beta")  # wrong; model gave beta 0.06
        assert pred.correct == 0 and pred.p_true == 0.06
        assert jev.stats()["brier"] == round((1 - 0.06) ** 2, 8)

    def test_double_record_rejected(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory({"q": dict(NOUL_YES)}))
        jev.decide({"a": 1}, {"q": {"type": "noul", "instructions": "?"}})
        jev.record_outcome("q", 1)
        with pytest.raises(KeyError):
            jev.record_outcome("q", 1)

    def test_unknown_qid_rejected(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory({"q": dict(NOUL_YES)}))
        with pytest.raises(KeyError):
            jev.record_outcome("nope", 1)


class TestAlerts:
    def test_overconfidence_alert_fires(self, tmp_path):
        fired = []
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory({"q": dict(CHOICE_A)}),
                         on_overconfidence=fired.append)
        jev.decide({}, {"q": {"type": "choice", "instructions": "?", "criteria": {}}})
        assert len(fired) == 1 and fired[0].qid == "q"

    def test_no_alert_once_calibration_earned(self, tmp_path):
        fired = []
        # stated 0.9, outcomes 90% correct -> calibrated; after 20 outcomes
        # verdict flips to FACE_VALUE and the alert goes silent
        ans = {"q": {"type": "noul", "noul": 0.9}}
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory(ans),
                         on_overconfidence=fired.append)
        for i in range(20):  # 18 correct, 2 wrong -> bin acc == conf == 0.9
            jev.decide({"a": i}, {"q": {"type": "noul", "instructions": "?"}})
            jev.record_outcome("q", 0 if i in (3, 11) else 1)
        n_after_warmup = len(fired)  # fired during UNVERIFIED warmup — by design
        r = jev.decide({"a": 99}, {"q": {"type": "noul", "instructions": "?"}})["q"]
        assert jev.stats()["verdict"] == FACE_VALUE
        assert r.domain_verdict == FACE_VALUE
        assert len(fired) == n_after_warmup  # final call added no alert


class TestClient:
    def test_retry_then_fail(self, tmp_path):
        calls = {"n": 0}

        def broken(url, body, headers):
            calls["n"] += 1
            raise OSError("network down")

        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=broken)
        with pytest.raises(JevAPIError):
            jev.decide({}, {"q": {"type": "noul", "instructions": "?"}})
        assert calls["n"] == 3  # 1 + 2 retries


class TestReceipt:
    def _session_with_data(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t", log_path=str(tmp_path / "l.jsonl"),
                         transport=fake_transport_factory({"q": dict(NOUL_YES)}))
        jev.decide({"a": 1}, {"q": {"type": "noul", "instructions": "?"}})
        jev.record_outcome("q", 1)
        return jev

    def test_sign_verify_roundtrip(self, tmp_path):
        jev = self._session_with_data(tmp_path)
        sig_path = jev.sign_log()
        assert sig_path.exists()
        assert jev.verify_log().ok
        # independent verification with published pubkey hex
        res = verify_log(jev.log_path, sig_path, jev.keys.pub_hex)
        assert res.ok and res.detail == "VALID"

    def test_tamper_detected(self, tmp_path):
        jev = self._session_with_data(tmp_path)
        sig_path = jev.sign_log()
        with open(jev.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": "outcome", "qid": "ghost",
                                "truth": 1, "correct": 1}) + "\n")
        res = verify_log(jev.log_path, sig_path, jev.keys.pub_hex)
        assert not res.ok and "INVALID" in res.detail


class TestReplay:
    def test_resume_restores_state(self, tmp_path):
        log = tmp_path / "l.jsonl"
        jev = TrustedJev(api_key="k", domain="t", log_path=str(log),
                         transport=fake_transport_factory({"q": dict(NOUL_YES)}))
        for i in range(3):
            jev.decide({"a": i}, {"q": {"type": "noul", "instructions": "?"}})
            jev.record_outcome("q", 1)
        s1 = jev.stats()
        # fresh session on the same log
        jev2 = TrustedJev(api_key="k", domain="t", log_path=str(log),
                          transport=fake_transport_factory({"q": dict(NOUL_YES)}))
        s2 = jev2.stats()
        assert s2["n_outcomes"] == s1["n_outcomes"] == 3
        assert s2["C"] == s1["C"]
        assert s2["n_calls"] == s1["n_calls"] == 3
        # and can keep going: next call gets rid 4
        r = jev2.decide({"a": 9}, {"q": {"type": "noul", "instructions": "?"}})["q"]
        assert r.rid == 4
