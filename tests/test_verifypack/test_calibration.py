"""calibration check kind(校准声明验证 · SPEC v0.3 §C)测试。

Jev 生态结合件:概率输出型决策模型的校准声明(Brier/ECE)必须可从逐样本
预测独立重算。契约:recomputed = {"brier": …, "ece": …, "n": N}(按 metrics
请求),对 claim.value 逐键容差比对;keys 不齐 = disagree。
"""
import json

import pytest

from tools.verifypack import checks, spec


@pytest.fixture()
def pack_dir(tmp_path):
    d = tmp_path / "pack"
    d.mkdir()
    (d / "pack.json").write_text('{"pack": "p1"}', encoding="utf-8")
    return d


def _write_preds(pack_dir, rows):
    p = pack_dir / "payload"
    p.mkdir(exist_ok=True)
    (p / "preds.json").write_text(json.dumps({"predictions": rows}), encoding="utf-8")
    return "payload/preds.json#predictions"


def _claim(value):
    return {"id": "C1", "level": "L1", "value": value,
            "checks": {"kind": "calibration", "from": None}}


# 4 样本二分类,手工可算:
# brier = mean((p - y)^2) = ((0.9-1)^2 + (0.3-0)^2 + (0.8-1)^2 + (0.2-0)^2)/4
#      = (0.01 + 0.09 + 0.04 + 0.04)/4 = 0.045
# ece(2 bins;本组预测全对:bin(p<0.5) y=0,0 acc=2/2 conf=0.25;bin(p>=0.5) y=1,1 acc=2/2 conf=0.85)
#      = 2/4*|1-0.25| + 2/4*|1-0.85| = 0.375 + 0.075 = 0.45(系统性欠自信)
ROWS = [
    {"outcome": 1, "p": 0.9},
    {"outcome": 0, "p": 0.3},
    {"outcome": 1, "p": 0.8},
    {"outcome": 0, "p": 0.2},
]


def test_binary_brier_ece_handcomputed(pack_dir):
    ref = _write_preds(pack_dir, ROWS)
    chk = {"kind": "calibration", "from": ref, "outcome_field": "outcome",
           "prob_field": "p", "metrics": {"brier": True, "ece": True}, "ece_bins": 2}
    r = checks.run_check({"pack": "p1"}, _claim({"brier": 0.045, "ece": 0.45, "n": 4}), chk, pack_dir)
    assert r["ok"], r
    assert abs(r["recomputed"]["brier"] - 0.045) < 1e-12
    assert abs(r["recomputed"]["ece"] - 0.45) < 1e-12
    assert r["recomputed"]["n"] == 4


def test_binary_wrong_claim_disagree(pack_dir):
    ref = _write_preds(pack_dir, ROWS)
    chk = {"kind": "calibration", "from": ref, "outcome_field": "outcome",
           "prob_field": "p", "metrics": {"brier": True}, "ece_bins": 2}
    r = checks.run_check({"pack": "p1"}, _claim({"brier": 0.01, "n": 4}), chk, pack_dir)
    assert not r["ok"]


def test_multiclass_probs(pack_dir):
    # 多类:brier = mean over classes (p_k - y_k)^2;样本1 p=[.7,.2,.1] y=[1,0,0] → (.09+.04+.01)=.14
    # 样本2 p=[.1,.8,.1] y=[0,1,0] → (.01+.04+.01)=.06 → 总 = .1
    rows = [{"outcome": 0, "probs": [0.7, 0.2, 0.1]},
            {"outcome": 1, "probs": [0.1, 0.8, 0.1]}]
    ref = _write_preds(pack_dir, rows)
    chk = {"kind": "calibration", "from": ref, "outcome_field": "outcome",
           "probs_field": "probs", "metrics": {"brier": True}}
    r = checks.run_check({"pack": "p1"}, _claim({"brier": 0.1, "n": 2}), chk, pack_dir)
    assert r["ok"], r


def test_missing_field_raises(pack_dir):
    ref = _write_preds(pack_dir, [{"outcome": 1}])  # 无 p
    chk = {"kind": "calibration", "from": ref, "outcome_field": "outcome",
           "prob_field": "p", "metrics": {"brier": True}}
    with pytest.raises(checks.CheckError):
        checks.run_check({"pack": "p1"}, _claim({"brier": 0.0, "n": 1}), chk, pack_dir)


def test_bad_probability_range_raises(pack_dir):
    ref = _write_preds(pack_dir, [{"outcome": 1, "p": 1.5}])
    chk = {"kind": "calibration", "from": ref, "outcome_field": "outcome",
           "prob_field": "p", "metrics": {"brier": True}}
    with pytest.raises(checks.CheckError):
        checks.run_check({"pack": "p1"}, _claim({"brier": 0.0, "n": 1}), chk, pack_dir)


def test_spec_validation():
    ok = {"kind": "calibration", "from": "x#y", "outcome_field": "o",
          "prob_field": "p", "metrics": {"brier": True}}
    spec.validate_check(ok)
    with pytest.raises(spec.SpecError):  # 缺 from
        spec.validate_check({"kind": "calibration", "outcome_field": "o", "metrics": {}})
    with pytest.raises(spec.SpecError):  # metrics 空
        spec.validate_check({"kind": "calibration", "from": "x#y",
                             "outcome_field": "o", "prob_field": "p", "metrics": {}})
    with pytest.raises(spec.SpecError):  # 未知 metric
        spec.validate_check({"kind": "calibration", "from": "x#y", "outcome_field": "o",
                             "prob_field": "p", "metrics": {"auc": True}})
