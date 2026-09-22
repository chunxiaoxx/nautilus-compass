# -*- coding: utf-8 -*-
import pytest

from jev_trust.calib import (CalibrationState, Prediction, brier, ece_toplabel,
                             verdict_for, effective_confidence, FACE_VALUE,
                             DISCOUNT, DOWNGRADE, UNVERIFIED)


def P(conf, correct):
    return Prediction(qid="x", stated_confidence=conf, correct=correct,
                      p_true=conf if correct else 1.0 - conf)


class TestECE:
    def test_perfect(self):
        preds = [P(1.0, 1) for _ in range(10)]
        assert ece_toplabel(preds) == 0.0

    def test_confidently_wrong(self):
        preds = [P(1.0, 0) for _ in range(10)]
        assert ece_toplabel(preds) == 1.0
        assert brier(preds) == 1.0

    def test_hand_mixed_case(self):
        # p=0.75 x4, half right: bin acc 0.5 vs conf 0.75 -> ECE 0.25
        # Brier = mean((0.75-1)^2, (0.75-0)^2 x2...) = (0.0625+0.5625)*2/4 = 0.3125
        preds = [P(0.75, 1), P(0.75, 0), P(0.75, 1), P(0.75, 0)]
        assert ece_toplabel(preds) == 0.25
        assert brier(preds) == 0.3125

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            ece_toplabel([])
        with pytest.raises(ValueError):
            brier([])


class TestVerdict:
    def test_insufficient_n_is_unverified(self):
        assert verdict_for(0.99, 10, min_n=20) == UNVERIFIED

    def test_levels(self):
        assert verdict_for(0.959, 100) == FACE_VALUE
        assert verdict_for(0.65, 100) == DISCOUNT
        assert verdict_for(0.086, 100) == DOWNGRADE
        assert verdict_for(None, 100) == UNVERIFIED


class TestEffectiveConfidence:
    def _state(self, n, conf, acc):
        s = CalibrationState()
        n_correct = int(n * acc)
        for i in range(n):
            s.add(P(conf, 1 if i < n_correct else 0))
        return s

    def test_bin_observed(self):
        # 10 past calls at conf ~0.9 with only 50% correct -> 0.9 is worth 0.5
        s = self._state(10, 0.9, 0.5)
        eff, basis = effective_confidence(s, 0.91)
        assert basis == "bin_observed"
        assert eff == 0.5

    def test_c_adjusted_fallback(self):
        # evidence exists but not in THIS bin -> C-adjusted fallback
        s = self._state(20, 0.3, 0.5)  # C = 1 - |0.5-0.3| = 0.8
        eff, basis = effective_confidence(s, 0.9)
        assert basis == "C_adjusted"
        assert eff == round(0.5 + 0.8 * (0.9 - 0.5), 4)

    def test_insufficient(self):
        s = CalibrationState()
        eff, basis = effective_confidence(s, 0.9)
        assert eff is None and basis == UNVERIFIED

    def test_too_few_overall(self):
        s = self._state(5, 0.3, 1.0)
        eff, basis = effective_confidence(s, 0.9)
        assert eff is None and basis == "insufficient_n"
