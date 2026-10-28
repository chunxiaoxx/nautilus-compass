"""W6 RSI soul 半边 · grounding probe 度量 harness(可证伪仪器).

control(无注入)vs grounded(有注入)同批两臂 → pass@k delta + 符号检验 → escapes_noise。
薄 adapter·复用 escape_noise_stats.aggregate_paired_multiseed + benchmark_verifier.pass_at_k。
诚实判据:escapes_noise=True 才认 grounding 有效;平/降 = 退回纯 FDE。
"""
import math

from grounding_probe import (
    build_seed_record, grounding_probe,
    build_reward_seed, grounding_probe_continuous,
    grounding_probe_twosample,
)


def test_build_seed_record_computes_pass_at_1_per_arm():
    rec = build_seed_record(
        control_items={"taskA": False, "taskB": False},
        grounded_items={"taskA": True, "taskB": False},
    )
    assert rec["control"]["pass_at_1"] == 0.0
    assert rec["grounded"]["pass_at_1"] == 0.5
    assert rec["control"]["items"] == {"taskA": False, "taskB": False}


def test_grounding_probe_grounded_clean_win_escapes_noise():
    # 3 seeds · grounded 每题每 seed 都赢 control → 应 escapes_noise
    seeds = [
        build_seed_record({"t1": False, "t2": False}, {"t1": True, "t2": True}),
        build_seed_record({"t1": False, "t2": False}, {"t1": True, "t2": True}),
        build_seed_record({"t1": False, "t2": False}, {"t1": True, "t2": True}),
    ]
    report = grounding_probe(seeds)
    assert report["escapes_noise"] is True
    assert report["treatment"]["key"] == "grounded"
    assert report["item_level"]["treatment_wins"] == 6
    assert report["item_level"]["baseline_wins"] == 0


def test_grounding_probe_no_delta_does_not_escape():
    seeds = [
        build_seed_record({"t1": True, "t2": False}, {"t1": True, "t2": False}),
        build_seed_record({"t1": True, "t2": False}, {"t1": True, "t2": False}),
    ]
    report = grounding_probe(seeds)
    assert report["escapes_noise"] is False
    assert report["item_level"]["discordant"] == 0


def test_grounding_probe_grounded_worse_does_not_escape():
    seeds = [
        build_seed_record({"t1": True, "t2": True}, {"t1": False, "t2": False}),
        build_seed_record({"t1": True, "t2": True}, {"t1": False, "t2": False}),
    ]
    report = grounding_probe(seeds)
    assert report["escapes_noise"] is False          # grounded 更差·net 负
    assert report["treatment_net"]["mean"] < 0


# ── 连续 ΔReward(A 簇 benchmark 客观打分·比 binary 高功效·RSI 首验度量)──

def test_build_reward_seed_keeps_reward_items():
    rec = build_reward_seed({"t1": 0.1, "t2": 0.2}, {"t1": 0.3, "t2": 0.25})
    assert rec["control"]["items"] == {"t1": 0.1, "t2": 0.2}
    assert rec["grounded"]["items"] == {"t1": 0.3, "t2": 0.25}


def test_grounding_probe_continuous_grounded_higher_escapes():
    # grounded reward 每题每 seed 都高于 control → ΔReward>0·escapes
    seeds = [
        build_reward_seed({"t1": 0.1, "t2": 0.2}, {"t1": 0.3, "t2": 0.4}),
        build_reward_seed({"t1": 0.1, "t2": 0.2}, {"t1": 0.35, "t2": 0.45}),
        build_reward_seed({"t1": 0.1, "t2": 0.2}, {"t1": 0.32, "t2": 0.42}),
    ]
    rep = grounding_probe_continuous(seeds)
    assert rep["escapes_noise"] is True
    assert rep["delta_reward"]["mean"] > 0
    assert rep["item_level"]["grounded_wins"] == 6
    assert rep["item_level"]["control_wins"] == 0


def test_grounding_probe_continuous_no_effect_does_not_escape():
    seeds = [
        build_reward_seed({"t1": 0.2}, {"t1": 0.2}),
        build_reward_seed({"t1": 0.2}, {"t1": 0.2}),
    ]
    rep = grounding_probe_continuous(seeds)
    assert rep["escapes_noise"] is False
    assert rep["delta_reward"]["mean"] == 0.0
    assert rep["item_level"]["discordant"] == 0


def test_grounding_probe_continuous_grounded_worse_does_not_escape():
    seeds = [
        build_reward_seed({"t1": 0.5, "t2": 0.5}, {"t1": 0.2, "t2": 0.1}),
        build_reward_seed({"t1": 0.5, "t2": 0.5}, {"t1": 0.25, "t2": 0.15}),
    ]
    rep = grounding_probe_continuous(seeds)
    assert rep["escapes_noise"] is False
    assert rep["delta_reward"]["mean"] < 0


# ── 两样本 ΔReward(1 题·N 裸 vs N grounded·精确置换检验·RSI 首验真形状)──

def test_twosample_grounded_clearly_higher_escapes():
    bare = [0.20, 0.21, 0.19, 0.22, 0.20]
    grounded = [0.40, 0.42, 0.41, 0.39, 0.43]
    rep = grounding_probe_twosample(bare, grounded)
    assert rep["delta_reward"] > 0
    assert rep["escapes_noise"] is True
    assert rep["p_value"] < 0.05
    assert math.isclose(rep["bare_mean"], sum(bare) / 5, rel_tol=1e-9)
    assert math.isclose(rep["grounded_mean"], sum(grounded) / 5, rel_tol=1e-9)


def test_twosample_no_separation_does_not_escape():
    rep = grounding_probe_twosample([0.3, 0.3, 0.3], [0.3, 0.3, 0.3])
    assert rep["delta_reward"] == 0.0
    assert rep["escapes_noise"] is False
    assert rep["p_value"] == 1.0


def test_twosample_grounded_worse_does_not_escape():
    rep = grounding_probe_twosample([0.5, 0.5, 0.5], [0.1, 0.1, 0.1])
    assert rep["delta_reward"] < 0
    assert rep["escapes_noise"] is False


def test_twosample_overlap_small_n_not_significant():
    # ΔReward>0 但 N=2/臂·C(4,2)=6 置换达不到 p<0.05 → 不 escape(诚实)
    rep = grounding_probe_twosample([0.2, 0.5], [0.3, 0.6])
    assert rep["delta_reward"] > 0
    assert rep["escapes_noise"] is False
    assert rep["p_value"] > 0.05
