"""W-V soul benchmark verifier底座 — the compass-callable judging interface.

The 验证器 + 判分 the buyer named the "核心资产". Three layers, all pure + reusable:

  1. judge_trajectory(result, mode)  — normalize ONE solution trajectory → pass/fail.
       mode='resolve' (SWE-bench / code: did the test grader resolve it → bool)
       mode='rubric'  (FDE buyer task: checklist_scorer scored dict → overall_pass)
  2. pass_at_k(n, c, k)              — unbiased pass@k estimator (Chen et al. 2021).
  3. is_hard_for_model(c, n, max_pass) — 难倒标注 (buyer: doubao 2.0 pass ≤ 3/5 → hard).

aggregate_task() ties them: N trajectories for one task → {pass@k per k, hard flag}.
This is the layer compass benchmark env plugs into — it produces the trajectories
(running the agent against a reproduced bench), then calls aggregate_task to get the
pass@k report + 难倒 sample annotation. Pairs with escape_noise_stats (arm comparison)
and the W-D verdict-bus (RUBRIC trajectory judging via vtf harness/checklist_scorer).
"""
from __future__ import annotations

from math import comb
from typing import Iterable


def pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k estimator: 1 - C(n-c, k) / C(n, k) (Chen et al. 2021, Codex).

    n = total samples, c = number correct, k = the k in pass@k. If k > n it is
    clamped to n (you can only estimate pass@k with n samples). All-correct → 1.0,
    none-correct → 0.0.
    """
    if n <= 0:
        return 0.0
    k = min(k, n)
    if c <= 0:
        return 0.0
    if k == 1:
        return c / n  # exact pass@1 = pass-rate (avoids comb-subtraction float error)
    if n - c < k:
        # fewer than k failing samples → every k-subset contains a correct one.
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_at_k_from_results(results: Iterable, k: int) -> float:
    """pass@k from an iterable of truthy/falsy per-attempt outcomes."""
    res = list(results)
    n = len(res)
    c = sum(1 for r in res if r)
    return pass_at_k(n, c, k)


def judge_trajectory(result, *, mode: str, threshold: float = 0.5) -> dict:
    """Normalize one solution trajectory into {"pass": bool, ...}.

    mode='resolve': ``result`` is truthy/falsy (SWE-bench resolved / test passed).
    mode='rubric':  ``result`` is a checklist_scorer scored dict (overall_pass key).
    mode='score':   ``result`` is a continuous reward (float); pass = reward >=
                    ``threshold``. For AutoLab/KernelBench objective scoring, the
                    threshold is the buyer-calibrated frontier bar (compass passes
                    the leaderboard reference anchor, default 0.5 = 达强人类), not a
                    hardcoded value (cnt_c1 ruling). The raw reward is returned too
                    so aggregate_task can keep the continuous distribution.
    """
    if mode == "resolve":
        return {"pass": bool(result)}
    if mode == "rubric":
        d = result if isinstance(result, dict) else {}
        return {"pass": bool(d.get("overall_pass")),
                "veto_failed": bool(d.get("veto_failed")),
                "score": d.get("score")}
    if mode == "score":
        r = float(result)
        return {"pass": r >= threshold, "reward": r}
    raise ValueError(
        f"unknown judge mode: {mode!r} (expected 'resolve', 'rubric' or 'score')")


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


def is_hard_for_model(c: int, n: int, max_pass: int = 3) -> bool:
    """难倒标注: a task is hard if the model passes it at most ``max_pass`` times.

    Buyer criterion: doubao 2.0 跑5次正确≤3次 (pass ≤ 3/5) ⇒ 难倒 = the target sample.
    """
    return c <= max_pass


def aggregate_task(
    task_uid: str,
    trajectories: Iterable,
    *,
    mode: str = "resolve",
    k_values: Iterable[int] = (1,),
    max_pass: int = 3,
    threshold: float = 0.5,
) -> dict:
    """N trajectories for one task → per-task verdict the compass env consumes.

    Judges each trajectory (mode), counts correct, computes pass@k for each k, and
    flags 难倒. Returns a JSON-able dict (pass_at_k keyed by str(k) for portability).

    mode='score' additionally keeps the continuous reward distribution under
    ``reward_stats`` (mean/best/min/std/per_reward/threshold) — the finer
    difficulty+fitness signal that binary pass@k discards (cnt_c1: 双轮合一,
    same verdict-bus serves rubric and benchmark-score tracks).
    """
    judged = [judge_trajectory(t, mode=mode, threshold=threshold) for t in trajectories]
    passes = [j["pass"] for j in judged]
    n = len(passes)
    c = sum(1 for p in passes if p)
    out = {
        "task_uid": task_uid,
        "mode": mode,
        "n": n,
        "c": c,
        "pass_at_k": {str(k): pass_at_k(n, c, k) for k in k_values},
        "hard_for_model": is_hard_for_model(c, n, max_pass=max_pass),
        "per_attempt": passes,
    }
    if mode == "score":
        rewards = [j["reward"] for j in judged]
        out["reward_stats"] = {
            "mean": _mean(rewards),
            "best": max(rewards) if rewards else 0.0,
            "min": min(rewards) if rewards else 0.0,
            "std": _sample_std(rewards),
            "per_reward": rewards,
            "threshold": threshold,
        }
    return out
