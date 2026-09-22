# -*- coding: utf-8 -*-
"""v0.2 decide_symmetric: bipolarity self-check."""
import json

import pytest

from jev_trust import TrustedJev

N = {"type": "noul", "instructions": "Is a greater than b?"}
F = {"type": "noul", "instructions": "Is a less than or equal to b?"}


def sym_transport(answers, calls=None):
    """answers: {qid: yes/no for normal} — flip answers derived to be
    either CONSISTENT (complementary) or CONFLICTING per key in `conflict`."""
    def transport(url, body, headers):
        if calls is not None:
            calls.append(json.loads(body))
        req = json.loads(body)
        out = {}
        for qid in req["questions"]:
            if qid.endswith("~flip"):
                base = answers[qid[:-5]]
                out[qid] = {"type": "noul",
                            "noul": 0.1 if base == "yes" else 0.9}
            else:
                p = 0.9 if answers[qid] == "yes" else 0.1
                out[qid] = {"type": "noul", "noul": p}
        return {"answers": out, "usage": {"input_tokens": 10, "output_tokens": 5}}
    return transport


def conflict_transport():
    """both polarities answer 'yes' -> conflict for every question."""
    def transport(url, body, headers):
        req = json.loads(body)
        return {"answers": {qid: {"type": "noul", "noul": 0.9}
                            for qid in req["questions"]},
                "usage": {}}
    return transport


class TestConsistent:
    def test_consistent_pair(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"),
                         transport=sym_transport({"q": "yes"}))
        r = jev.decide_symmetric({"a": 5, "b": 1}, {"q": {"question": N, "opposite": F}})["q"]
        assert r.decision == "yes" and r.polarity_consistent is True
        assert r.trust_flag == "" and r.opposite_decision == "yes"
        assert r.basis != "polarity_conflict"

    def test_one_api_call_both_polarities(self, tmp_path):
        calls = []
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"),
                         transport=sym_transport({"q": "no"}, calls))
        jev.decide_symmetric({}, {"q": {"question": N, "opposite": F}})
        assert len(calls) == 1
        assert set(calls[0]["questions"]) == {"q", "q~flip"}

    def test_confidence_is_conservative_min(self, tmp_path):
        # normal says yes at 0.95 (p=0.95); flip says no at 0.8 (p=0.2)
        def t(url, body, headers):
            req = json.loads(body)
            out = {}
            for qid in req["questions"]:
                p = 0.95 if not qid.endswith("~flip") else 0.2
                out[qid] = {"type": "noul", "noul": p}
            return {"answers": out, "usage": {}}
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"), transport=t)
        r = jev.decide_symmetric({}, {"q": {"question": N, "opposite": F}})["q"]
        assert r.polarity_consistent is True
        assert r.stated_confidence == 0.8  # min(0.95, 0.8)


class TestConflict:
    def test_conflict_forces_none_and_flag(self, tmp_path):
        fired = []
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"),
                         transport=conflict_transport(),
                         on_polarity_conflict=fired.append)
        r = jev.decide_symmetric({}, {"q": {"question": N, "opposite": F}})["q"]
        assert r.polarity_consistent is False
        assert r.trust_flag == "POLARITY_CONFLICT"
        assert r.effective_confidence is None
        assert r.basis == "polarity_conflict"
        assert fired == [r]

    def test_no_conflict_callback_when_consistent(self, tmp_path):
        fired = []
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"),
                         transport=sym_transport({"q": "yes"}),
                         on_polarity_conflict=fired.append)
        jev.decide_symmetric({}, {"q": {"question": N, "opposite": F}})
        assert fired == []


class TestBookkeeping:
    def test_log_and_outcome_use_normal_polarity(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"),
                         transport=sym_transport({"q": "yes"}))
        jev.decide_symmetric({"a": 1}, {"q": {"question": N, "opposite": F}})
        lines = [json.loads(l) for l in
                 (tmp_path / "l.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(lines) == 1 and lines[0]["kind"] == "call"
        assert lines[0]["polarity"] == "normal"
        assert lines[0]["opposite_mapped"] == "yes"
        assert lines[0]["polarity_consistent"] is True
        pred = jev.record_outcome("q", 1)
        assert pred.correct == 1 and pred.stated_confidence == 0.9
        assert jev.stats()["n_outcomes"] == 1

    def test_signature_covers_symmetric_log(self, tmp_path):
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"),
                         transport=sym_transport({"q": "yes"}))
        jev.decide_symmetric({}, {"q": {"question": N, "opposite": F}})
        jev.record_outcome("q", 1)
        sig = jev.sign_log()
        assert jev.verify_log().ok

    def test_choice_questions_rejected(self, tmp_path):
        def choice_transport(url, body, headers):
            req = json.loads(body)
            return {"answers": {qid: {"type": "choice", "choice": "alpha",
                                      "confidence": 0.9}
                                for qid in req["questions"]},
                    "usage": {}}
        jev = TrustedJev(api_key="k", domain="t",
                         log_path=str(tmp_path / "l.jsonl"),
                         transport=choice_transport)
        bad = {"question": {"type": "choice", "instructions": "?", "criteria": {}},
               "opposite": {"type": "choice", "instructions": "?", "criteria": {}}}
        with pytest.raises(ValueError):
            jev.decide_symmetric({}, {"q": bad})
