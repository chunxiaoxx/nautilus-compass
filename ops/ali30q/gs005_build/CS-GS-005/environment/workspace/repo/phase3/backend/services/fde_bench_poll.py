"""第3类(RSI 飞轮)确定性 verify poller · produced → bench_eval reward → verdict-bus.

第3类 ≠ 第1/2类 QC. consumer/agent produce 出的修复代码经 compass 的 bench_eval.py
(确定性 G 门·非 LLM judge)判 reward 1.0/0.0 → 写 verdict-bus(source='compass/bench_eval')
→ task settled → PoI eligible. 这是 RSI 飞轮缺的一环:没有它, consumer 产出无 reward
信号、棘轮不转(soul checklist 不该判第3类·门口径不同).

镜像 services/fde_scorer_poll.py(纯核心 + 注入 seam):produced-task 读、bench_eval
执行(fde_bench_verify)、verdict POST 都注入, 编排核心可纯单测、无 HTTP/子进程.
fail-soft: 一道题失败不中断整批.

诚实(compass 6/15 交付强调):`ok=False`(verifier 自身失败·bench 缺失/超时/输出非
JSON)≠ 合法 reward 0(「跑通但没过」). 前者**不写 verdict**(否则棘轮被误判的 0 污染)、
标 errored 待重试; 后者写 reward 0 verdict(棘轮需要这个 0 信号).
"""
from __future__ import annotations

import json
from typing import Callable, Iterable, Protocol


class ProducedTaskSource(Protocol):
    """读 produced FDE 任务(platform-binding seam).

    每个 task 是 dict, 至少含 ``task_uid``; 第3类还含 ``description``(打包 JSON·
    fde_class==3)与 ``output``(produce 出的修复代码, POST /report 持久化).
    """

    def list_produced_tasks(self) -> Iterable[dict]:  # pragma: no cover - protocol
        ...


def parse_t3_spec(task: dict) -> dict | None:
    """从 task['description'] 解出第3类 spec JSON; 解不出(非 JSON)→ None."""
    desc = task.get("description")
    if not isinstance(desc, str) or not desc.strip():
        return None
    try:
        spec = json.loads(desc)
    except (ValueError, TypeError):
        return None
    return spec if isinstance(spec, dict) else None


def is_t3_bench_task(task: dict) -> bool:
    """第3类确定性 verify 任务 = description 打包 JSON 且 ``fde_class == 3``.

    第1/2类 human 题(description 是 QC-style JSON·无 fde_class)→ False, 留给 soul
    scorer. 口径分流: bench poller 只碰确定性可验的第3类.
    """
    spec = parse_t3_spec(task)
    return bool(spec) and spec.get("fde_class") == 3


def build_bench_verdict_body(task: dict, result: dict) -> dict:
    """bench_eval reward → POST /verdict body(匹配 ingest _REQUIRED).

    verdict_id 以**产出代码 hash**为键(``bench|{task_uid}|{sol_hash}``):同一题不同
    produce 版本 = 不同 verdict(per-version 棘轮·与 fresh-uid-per-version 惯例一致),
    同一产出重判则 ingest 幂等. source='compass/bench_eval'(确定性外部 fitness).
    """
    task_uid = task["task_uid"]
    sol_hash = result.get("sol_hash") or "default"
    passed = bool(result.get("passed"))
    return {
        "verdict_id": f"bench|{task_uid}|{sol_hash}",
        "task_uid": task_uid,
        "source": "compass/bench_eval",
        "overall_pass": passed,
        "veto_failed": False,
        "score": float(result.get("reward", 0.0)),
        "items": [],
        "artifacts": {
            "kind": "t3_deterministic_bench",
            "n_pass": result.get("n_pass"),
            "n_total": result.get("n_total"),
            "reason": result.get("reason", ""),
            "bench": result.get("bench"),
            "sol_hash": sol_hash,
        },
    }


def poll_and_verify(
    source: ProducedTaskSource,
    verify_fn: Callable[[dict], dict],
    verdict_fn: Callable[[dict], object],
    already_verified: Iterable[str] | None = None,
    capability_fn: Callable[[dict, dict], None] | None = None,
) -> dict:
    """读 produced 任务 → 跑 bench_eval(确定性)→ POST verdict. fail-soft per task.

    Args:
        source: produced-task 读 seam(``list_produced_tasks()``).
        verify_fn: ``task -> result``. 注入(包 fde_bench_verify: 从 description 取
            bench_eval, 从 output 取产出代码, 写临时文件, 跑子进程, 返
            ``{reward, passed, ok, n_pass, n_total, reason, bench, sol_hash}``).
        verdict_fn: POST 一个 verdict body(POST /api/platform/fde/verdict 包装).
        already_verified: 已写过 compass/bench_eval verdict 的 task_uid(跨轮幂等优化).
        capability_fn: 可选 ``(task, result) -> None``. 拿到 verify result 即调(覆盖
            verified + 格式失败两路·单写点)· verify-side 能力回写(producer claimed_by
            的格式合规/质量分 → platform_agent_capability_stats·V5 路由读端). fail-soft:
            内部已吞异常·这里再兜一层·能力写绝不影响 verify/verdict 主链.

    Returns:
        ``{"verified": [uid…], "skipped": [uid…], "errored": [uid…], "failed": [uid…]}``.
        - verified: 写了 verdict(含合法 reward 0).
        - errored: verifier 自身失败(ok=False)→ 不写 verdict·**不入 seen**·下轮重试.
        - failed: verify_fn/verdict_fn 抛异常(fail-soft).
    """
    seen = set(already_verified or ())
    verified: list[str] = []
    skipped: list[str] = []
    errored: list[str] = []
    failed: list[str] = []

    for task in source.list_produced_tasks():
        uid = task.get("task_uid")
        if not uid or uid in seen:
            skipped.append(uid)
            continue
        if not is_t3_bench_task(task):
            # 非第3类(human 第1/2类)→ 留给 soul scorer, bench poller 不碰.
            skipped.append(uid)
            seen.add(uid)
            continue
        if task.get("output") in (None, "", {}, []):
            # produced 但没产出可验 → skip(不发空 verdict).
            skipped.append(uid)
            seen.add(uid)
            continue
        try:
            result = verify_fn(task)
        except Exception:  # fail-soft: 一道题 verify 崩了不中断整批
            failed.append(uid)
            seen.add(uid)
            continue
        if capability_fn is not None:
            # verify-side 能力回写(单写点·覆盖 verified + 格式失败·infra 失败由
            # derive 判 None 不归因). fail-soft: 绝不影响 verdict 主链.
            try:
                capability_fn(task, result)
            except Exception:  # noqa: BLE001
                pass
        if not result.get("ok"):
            # verifier 自身失败 ≠ 合法 reward 0 → 不写 verdict·不入 seen·可重试.
            errored.append(uid)
            continue
        try:
            verdict_fn(build_bench_verdict_body(task, result))
        except Exception:  # fail-soft: verdict POST 失败
            failed.append(uid)
            seen.add(uid)
            continue
        verified.append(uid)
        seen.add(uid)

    return {"verified": verified, "skipped": skipped, "errored": errored, "failed": failed}
