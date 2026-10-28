"""Tests for arm-agnostic escape-noise statistics (Phase 4 Task 2).

Ports the Phase-3 paired multi-seed verdict logic to arbitrary arm names so
Probe 1 (arm1 vs arm3) reuses it. The conservative gate is unchanged: an effect
escapes noise only if net mean > 0 AND every seed is individually positive AND
the paired sign-test p < 0.05.
"""
from escape_noise_stats import aggregate_paired_multiseed, binom_sign_test


def test_binom_sign_test_no_discordant_is_one():
    assert binom_sign_test(0, 0) == 1.0


def test_binom_sign_test_symmetric_and_two_sided():
    # 10-0 split is strongly significant; 5-5 is not.
    assert binom_sign_test(10, 0) < 0.01
    assert binom_sign_test(5, 5) > 0.5
    # symmetry: wins/losses order does not change the p-value
    assert binom_sign_test(8, 2) == binom_sign_test(2, 8)


def _seed(base_items, trt_items):
    return {
        "baseline": {"pass_at_1": sum(base_items.values()) / len(base_items),
                     "items": base_items},
        "treatment": {"pass_at_1": sum(trt_items.values()) / len(trt_items),
                      "items": trt_items},
    }


def test_escapes_noise_when_lopsided_and_all_seeds_positive():
    # Treatment beats baseline in both seeds on a lopsided item tally.
    seeds = []
    for _ in range(2):
        base = {f"i{j}": (j >= 6) for j in range(20)}   # first 6 fail -> 14/20
        trt = {f"i{j}": (j >= 2) for j in range(20)}    # first 2 fail -> 18/20
        seeds.append(_seed(base, trt))
    agg = aggregate_paired_multiseed(seeds, baseline_key="baseline",
                                     treatment_key="treatment")
    assert agg["item_level"]["treatment_wins"] > agg["item_level"]["baseline_wins"]
    assert agg["item_level"]["discordant"] > 0
    assert agg["treatment_net"]["all_seeds_positive"] is True
    assert agg["escapes_noise"] is True


def test_sign_flip_does_not_escape():
    s1 = _seed({"a": False, "b": True}, {"a": True, "b": True})   # net +0.5
    s2 = _seed({"a": True, "b": True}, {"a": False, "b": True})   # net -0.5
    agg = aggregate_paired_multiseed([s1, s2], baseline_key="baseline",
                                     treatment_key="treatment")
    assert agg["treatment_net"]["all_seeds_positive"] is False
    assert agg["escapes_noise"] is False


def test_zero_effect_does_not_escape():
    # Identical arms -> no discordant pairs, net 0 -> within noise.
    items = {f"i{j}": (j % 2 == 0) for j in range(10)}
    seeds = [_seed(dict(items), dict(items)) for _ in range(2)]
    agg = aggregate_paired_multiseed(seeds, baseline_key="baseline",
                                     treatment_key="treatment")
    assert agg["item_level"]["discordant"] == 0
    assert agg["escapes_noise"] is False


def test_report_shape_has_arm_means_and_net():
    seeds = [_seed({"a": False}, {"a": True})]
    agg = aggregate_paired_multiseed(seeds, baseline_key="baseline",
                                     treatment_key="treatment")
    assert {"n_seeds", "baseline", "treatment", "treatment_net", "item_level",
            "escapes_noise"} <= agg.keys()
    assert "mean" in agg["baseline"] and "per_seed" in agg["treatment"]
    assert "sign_test_p" in agg["item_level"]
