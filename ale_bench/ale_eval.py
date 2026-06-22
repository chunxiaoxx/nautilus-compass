"""compass ALE-Bench scorer · wraps ale_bench public_eval into an rsi_two_arm eval_fn.

齿轮⑤/③ 旁支 → 胜负手燃料线(ALE 连续分·非饱和)。eval_fn 跑在 T4 ALE env
(需 ale_bench 1.5.0 + cpp23 判题镜像 · /workdir 须 1777 · 见 docs)。

设计 = effect 注入(start_fn)· 与 V5 `ale_fuel_batch.py` 的 strong_fn/doubao_fn 注入
风格一致(anchor#5 不另造)。单测注 fake session 无需 live ale_bench;live 标定走 T4。

契约(给 V5 接 rsi_two_arm `run_two_arm`):
    eval_fn(candidate_code, problem_id) -> {"reward": float, "feedback": str}
reward = ALE public overall_absolute_score 原值(同题 two_arm 比 ΔScore turn-over-turn·
原始尺度即可·不做跨题归一·YAGNI)。rejected/invalid -> REJECTED_REWARD。
"""
from __future__ import annotations

from typing import Any, Callable

# rejected/invalid 解的 reward。two_arm 同题内比较·越高越好·AHC 有效输出绝对分 > 0。
REJECTED_REWARD: float = 0.0


def score_solution(
    code: str,
    problem_id: str,
    *,
    language: str = "cpp23",
    start_fn: Callable[..., Any] | None = None,
    lite_version: bool = False,
    num_workers: int = 2,
) -> dict:
    """跑 `code` 过 ALE-Bench public_eval · 返 {"score","rejected","raw"}。

    start_fn 注入(默认 ale_bench.start)· 单测注 fake。session 必 close(资源)。
    lite_version=False:ahc 题 lite 子集多缺(实测 ahc001 lite not found·full 可用)。
    """
    if start_fn is None:  # pragma: no cover - live path (T4 only)
        import ale_bench

        start_fn = ale_bench.start
    session = start_fn(problem_id, lite_version=lite_version, num_workers=num_workers)
    try:
        result = session.public_eval(code, language)
        score = float(getattr(result, "overall_absolute_score", 0.0) or 0.0)
        # AHC 有效输出绝对分 > 0;<= 0 视作 rejected/WA/RE(live 标定 REJECTED 哨兵后可精化)。
        rejected = score <= 0.0
        return {"score": score, "rejected": rejected, "raw": result}
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass


def eval_fn(
    candidate: str,
    problem_id: str,
    *,
    language: str = "cpp23",
    start_fn: Callable[..., Any] | None = None,
    lite_version: bool = False,
    num_workers: int = 2,
) -> dict:
    """rsi_two_arm 兼容 eval_fn:candidate code -> {"reward": float, "feedback": str}。"""
    r = score_solution(
        candidate,
        problem_id,
        language=language,
        start_fn=start_fn,
        lite_version=lite_version,
        num_workers=num_workers,
    )
    if r["rejected"]:
        return {
            "reward": REJECTED_REWARD,
            "feedback": (
                f"Solution rejected/invalid on {problem_id} "
                f"(public absolute score <= 0). Check output format / runtime errors / TLE."
            ),
        }
    return {
        "reward": r["score"],
        "feedback": (
            f"ALE public absolute score = {r['score']:.1f} on {problem_id}. "
            f"Higher is better; iterate the heuristic to raise it."
        ),
    }


def task_family(problem_id: str) -> str:
    """fleet 记忆 family 键(W1/W2 grounding 按 family 分组)。"""
    return f"ale_ahc_{problem_id}"
