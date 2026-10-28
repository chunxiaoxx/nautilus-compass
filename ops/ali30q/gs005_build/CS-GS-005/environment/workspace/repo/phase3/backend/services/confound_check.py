"""confound-check 旁注(2026-06-23·V5 confound-check 观测原则落地·纯逻辑)。

元教训:任何 KILLED/失败 verdict 信之前先过 confound-check——4 次都差点误判"机制死",
全是 env/config 伪装(adapter没存/seq截断/进程死/prompt-skew)。本模块把这条 check
结构化成各阶段守卫顺手填的旁注·conductor pulse 汇聚 surface。不建新监控系统(anchor #5)。
"""
from __future__ import annotations

_MIN_SOLUTION_CHARS = 10   # 解非空下限(短于此 = 空解/拒答 artifact)


def eval_confound_checks(row: dict) -> dict:
    """eval per_task 行 → confound 旁注({check: {ok, note}})。

    - adapter_effective:distilled 解 ≠ base 解(长度不同)= adapter 真加载
      (distilled_len==base_len 逐字符相同 = adapter 没存 bug·2026-06-22 真案例)。
    - solution_nonempty:distilled 解非空非纯语法崩(长度 > 下限)。
    """
    base_len = int(row.get("base_len") or 0)
    dist_len = int(row.get("distilled_len") or 0)
    adapter_ok = dist_len != base_len
    nonempty_ok = dist_len >= _MIN_SOLUTION_CHARS
    return {
        "adapter_effective": {
            "ok": adapter_ok,
            "note": "" if adapter_ok else f"distilled_len==base_len={base_len}(adapter 可能没生效)"},
        "solution_nonempty": {
            "ok": nonempty_ok,
            "note": "" if nonempty_ok else f"distilled 解仅 {dist_len} 字符(空解/拒答 artifact)"},
    }


def token_truncate_flags(records: list[dict], max_seq: int = 4096,
                         chars_per_tok: float = 3.48) -> list[dict]:
    """燃料 records → 截断风险标记(训练前过滤超长题·防 seq 截解尾 artifact)。

    prob_tok + sol_tok > max_seq → 解尾在训练时被截(ahc008 6170>4096 真案例)。
    chars_per_tok=3.48 对齐 V5 token 剖析口径。
    """
    flags = []
    for r in records:
        prob = r.get("problem_statement") or r.get("input") or ""
        sol = r.get("strong_solution") or r.get("output") or ""
        tok = (len(prob) + len(sol)) / chars_per_tok
        flags.append({
            "task_id": r.get("task_id"),
            "tok": round(tok),
            "truncate_risk": tok > max_seq,
        })
    return flags


def unresolved_confounds(eval_result: dict) -> list[str]:
    """eval 结果 → 未排除的 confound 列表(conductor pulse 用·KILLED 旁注)。

    任何 per_task 行的 confound_checks 有 ok=False → 该 verdict 不可信(先排 confound)。
    返回 ``["<task_id>:<check>", ...]``。
    """
    out = []
    for row in eval_result.get("per_task", []) or []:
        tid = row.get("task_id", "?")
        for name, c in (row.get("confound_checks") or {}).items():
            if not c.get("ok", True):
                out.append(f"{tid}:{name}")
    return out
