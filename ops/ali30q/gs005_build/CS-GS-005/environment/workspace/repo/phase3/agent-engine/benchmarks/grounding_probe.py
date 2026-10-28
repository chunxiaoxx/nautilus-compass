"""W6 RSI soul 半边 · grounding probe 度量 harness.

control(无 grounding 注入)vs grounded(有注入)同批两臂逐次成败 → escapes_noise 判据。
**薄 adapter** —— 配对符号检验 + escapes_noise 逻辑全复用 escape_noise_stats(anchor#5),
pass@1 复用 benchmark_verifier。本模块只把 grounding control/grounded 结果整形成
aggregate_paired_multiseed 吃的 seed_record,再委托。

可证伪判据(诚实):escapes_noise=True(grounded net>0 且每 seed 正 且 sign_p<0.05)才认
RSI grounding 有效;平/降 → 退回纯 FDE,不自欺(design_20260605 红线)。
"""
from __future__ import annotations

from itertools import combinations
from typing import Dict, List

from escape_noise_stats import aggregate_paired_multiseed, binom_sign_test
from benchmark_verifier import pass_at_k_from_results

CONTROL = "control"
GROUNDED = "grounded"


def _mean(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _sample_std(xs) -> float:
    xs = list(xs)
    n = len(xs)
    if n < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5


def build_seed_record(control_items: Dict[str, bool],
                      grounded_items: Dict[str, bool]) -> Dict:
    """构造一个 seed 的配对记录(control vs grounded).

    items = {task_uid(或 attempt_id): pass_bool}。pass_at_1 复用无偏估计量。
    """
    return {
        CONTROL: {"pass_at_1": pass_at_k_from_results(control_items.values(), 1),
                  "items": dict(control_items)},
        GROUNDED: {"pass_at_1": pass_at_k_from_results(grounded_items.values(), 1),
                   "items": dict(grounded_items)},
    }


def grounding_probe(seed_records: List[Dict]) -> Dict:
    """N seeds 的 control/grounded 两臂 → escape-the-noise verdict(委托复用层)."""
    return aggregate_paired_multiseed(seed_records, CONTROL, GROUNDED)


# ── 连续 ΔReward(A 簇 benchmark 客观打分·比 binary 高功效)──
# A 簇(AutoLab/KernelBench)是连续 reward。RSI 首验度量 grounded−裸 的连续 ΔReward
# 比二值化更高统计功效(不丢 0.1 vs 0.45 的差)。保守门同 escape_noise_stats:
# net_mean>0 且每 seed 正 且 配对符号检验 p<0.05 才 escapes_noise(cnt_c3:ΔReward
# 升 PoI fuel 只在 escapes_noise=True·不给噪声印币)。

def build_reward_seed(control_rewards: Dict[str, float],
                      grounded_rewards: Dict[str, float]) -> Dict:
    """构造一个 seed 的连续 reward 配对记录·items = {task_uid: reward_float}."""
    return {
        CONTROL: {"items": dict(control_rewards)},
        GROUNDED: {"items": dict(grounded_rewards)},
    }


def grounding_probe_continuous(seed_records: List[Dict]) -> Dict:
    """control vs grounded 连续 reward 配对 → ΔReward + 符号检验 + escapes_noise.

    每 (seed, task) 配对 delta = grounded_reward − control_reward。聚合:总体
    ΔReward 均值/标准差 + 每 seed 净 delta + 配对符号检验(delta 符号)。
    escapes_noise = ΔReward 均值>0 且每 seed 净>0 且 sign_p<0.05(保守·诚实判据)。
    """
    per_seed_net: List[float] = []
    wins = losses = ties = 0
    all_deltas: List[float] = []
    for s in seed_records:
        ci = s[CONTROL]["items"]
        gi = s[GROUNDED]["items"]
        deltas: List[float] = []
        for iid, cr in ci.items():
            gr = gi.get(iid)
            if gr is None:
                continue
            d = gr - cr
            deltas.append(d)
            all_deltas.append(d)
            if d > 0:
                wins += 1
            elif d < 0:
                losses += 1
            else:
                ties += 1
        per_seed_net.append(_mean(deltas))
    sign_p = binom_sign_test(wins, losses)
    net_mean = _mean(all_deltas)
    all_pos = bool(per_seed_net) and all(d > 0 for d in per_seed_net)
    escapes = bool(net_mean > 0 and all_pos and sign_p < 0.05)
    return {
        "n_seeds": len(seed_records),
        "delta_reward": {
            "mean": net_mean,
            "std": _sample_std(all_deltas),
            "per_seed_net": per_seed_net,
        },
        "item_level": {
            "grounded_wins": wins,
            "control_wins": losses,
            "ties": ties,
            "discordant": wins + losses,
            "sign_test_p": sign_p,
        },
        "escapes_noise": escapes,
    }


# ── 两样本 ΔReward(1 题·N 独立裸候选 vs N 独立 grounded 候选)──
# RSI 首验真形状:单题(radix_sort)两臂各 N 个【独立】候选 → 无配对假设 →
# 两样本而非配对检验。grounding_probe_continuous(配对)用在这里会虚假配对·统计错。
# 显著性 = 精确置换检验(打乱臂标签·纯函数·确定性·小 N 精确枚举·无 scipy/随机)。
# 单边(grounded 更好):p = 置换后 ΔReward ≥ 实测 的比例。escapes_noise = ΔReward>0
# 且 p<0.05(cnt_c3:只 escapes 才升 PoI fuel·不给噪声印币)。

_PERM_EXACT_CAP = 200_000  # C(nb+ng, ng) 超此用全枚举仍可控(N 小·候选 eval 贵)


def grounding_probe_twosample(bare_rewards, grounded_rewards) -> Dict:
    """N 裸 reward vs N grounded reward(同一题)→ ΔReward + 置换检验 + escapes_noise."""
    bare = [float(x) for x in bare_rewards]
    grounded = [float(x) for x in grounded_rewards]
    nb, ng = len(bare), len(grounded)
    bare_mean, grounded_mean = _mean(bare), _mean(grounded)
    observed = grounded_mean - bare_mean

    pooled = bare + grounded
    n = nb + ng
    total = count = 0
    # 精确置换:枚举所有把 ng 个分到 grounded 臂的方式·比较 mean 差 ≥ 实测。
    for combo in combinations(range(n), ng):
        gset = set(combo)
        g = [pooled[i] for i in gset]
        b = [pooled[i] for i in range(n) if i not in gset]
        diff = _mean(g) - _mean(b)
        total += 1
        if diff >= observed - 1e-12:  # ≥ 实测(含浮点容差)
            count += 1
    p_value = count / total if total else 1.0
    escapes = bool(observed > 0 and p_value < 0.05)
    return {
        "delta_reward": observed,
        "bare_mean": bare_mean,
        "grounded_mean": grounded_mean,
        "n_bare": nb,
        "n_grounded": ng,
        "p_value": p_value,
        "n_permutations": total,
        "escapes_noise": escapes,
    }
