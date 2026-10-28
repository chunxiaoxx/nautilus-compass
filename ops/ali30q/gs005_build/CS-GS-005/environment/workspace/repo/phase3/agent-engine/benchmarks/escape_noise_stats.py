"""Arm-agnostic escape-noise statistics for paired multi-seed benchmark arms.

Ported from the Phase-3 persona-consensus probe (Paradigm A, CLOSED) — same
proven logic, generalized from the hardcoded ``homogeneous`` / ``persona-diverse``
keys to arbitrary ``baseline_key`` / ``treatment_key`` so Probe 1 (arm1 vs arm3)
reuses it.

The statistical power for the "treatment − baseline" question lives in the PAIRED
item tally (same instances, both arms): with N×K paired observations a real edge
shows up as a lopsided win/loss split. The per-seed net mean/std is the
consistency check (are the K reps all positive, or does the sign flip?).

The ``escapes_noise`` gate is intentionally conservative: net mean > 0 AND every
seed individually positive (sign never flips) AND a significant lopsided item
tally. A True is a *signal*, not a proof — the human reads the distribution.
"""
from math import comb
from typing import Dict, List


def binom_sign_test(wins: int, losses: int) -> float:
    """Two-sided exact sign test p-value on discordant pairs.

    Null: among pairs where the two arms disagree, each is equally likely to
    favor either arm (p=0.5). Returns p in [0, 1]; 1.0 when there are no
    discordant pairs. Pure (no scipy). NOTE: pooling (seed, item) pairs treats
    them as independent — if an item is discordant the *same way* across seeds
    the p-value is anti-conservative, so it is read as supporting texture, not as
    the sole verdict (the per-seed net distribution is the independent check).
    """
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(comb(n, i) for i in range(k + 1)) * (0.5 ** n)
    return min(1.0, 2.0 * tail)


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _sample_std(xs: List[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / (n - 1)) ** 0.5


def aggregate_paired_multiseed(
    seed_records: List[Dict],
    baseline_key: str,
    treatment_key: str,
) -> Dict:
    """Aggregate K seeds of two paired arms into the escape-the-noise verdict.

    ``seed_records[i]`` = {
        baseline_key:  {"pass_at_1": float, "items": {instance_id: bool}},
        treatment_key: {"pass_at_1": float, "items": {instance_id: bool}},
    }

    Returns per-arm mean/std across seeds, the per-seed treatment-net distribution
    (mean/std/SEM/normal 95% CI), the pooled paired item tally + sign-test p, and
    an ``escapes_noise`` boolean (net_mean > 0 AND every seed positive AND
    sign_p < 0.05).
    """
    base = [s[baseline_key]["pass_at_1"] for s in seed_records]
    trt = [s[treatment_key]["pass_at_1"] for s in seed_records]
    net = [t - b for t, b in zip(trt, base)]

    treatment_wins = baseline_wins = both_pass = both_fail = 0
    for s in seed_records:
        bi = s[baseline_key]["items"]
        ti = s[treatment_key]["items"]
        for iid, bp in bi.items():
            tp = ti.get(iid)
            if tp is None:
                continue
            if tp and not bp:
                treatment_wins += 1
            elif bp and not tp:
                baseline_wins += 1
            elif bp and tp:
                both_pass += 1
            else:
                both_fail += 1

    sign_p = binom_sign_test(treatment_wins, baseline_wins)
    net_mean, net_std = _mean(net), _sample_std(net)
    k = len(seed_records)
    sem = net_std / (k ** 0.5) if k else 0.0
    all_positive = bool(net) and all(d > 0 for d in net)
    escapes = bool(net_mean > 0 and all_positive and sign_p < 0.05)

    return {
        "n_seeds": k,
        "baseline": {"key": baseline_key, "mean": _mean(base),
                     "std": _sample_std(base), "per_seed": base},
        "treatment": {"key": treatment_key, "mean": _mean(trt),
                      "std": _sample_std(trt), "per_seed": trt},
        "treatment_net": {
            "per_seed": net,
            "mean": net_mean,
            "std": net_std,
            "sem": sem,
            "ci95_normal": [net_mean - 1.96 * sem, net_mean + 1.96 * sem],
            "all_seeds_positive": all_positive,
        },
        "item_level": {
            "treatment_wins": treatment_wins,
            "baseline_wins": baseline_wins,
            "both_pass": both_pass,
            "both_fail": both_fail,
            "discordant": treatment_wins + baseline_wins,
            "sign_test_p": sign_p,
        },
        "escapes_noise": escapes,
    }
