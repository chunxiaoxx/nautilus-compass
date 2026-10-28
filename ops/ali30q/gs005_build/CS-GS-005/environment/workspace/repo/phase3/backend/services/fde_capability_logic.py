"""FDE 能力归因纯逻辑(2026-06-22)· 无 DB/models 依赖 → poller 进程可 import。

verify-side 能力回写拆两层:本模块=纯归因逻辑(verify result→格式合规三态+skill_tag),
poller(vendored 无 models/utils)import 这里 derive 后 POST 给服务端端点;服务端
(api/fde_capability)做 DB upsert。镜像 verdict_fn 的 HTTP 架构(poller 是瘦客户端)。

capability(格式合规)≠ quality(正确性方差·V5 RSI turf)。
"""
from __future__ import annotations

from typing import Optional

from services.fde_bench_poll import parse_t3_spec  # 纯函数(仅 json/typing)

# producer 责任的格式失败(产非 diff / 空产出 / 无实质产出)
_FORMAT_FAIL_MARKERS = (
    "non-diff",
    "need unified diff",
    "no solution code",
    "has no solution",
    "no patch",
    "not substantive",
)
# infra/配置失败(verifier 自身·非 producer 责任)→ 不归因
_INFRA_MARKERS = (
    "no report",
    "harness",
    "gpu_eval",
    "not parsed",
    "timeout",
    "ssh",
    "no verifier",
    "verifier_inline",
    "bench",
)


def classify_format(result: dict) -> Optional[bool]:
    """verify result → 格式合规三态。

    True  = 合规(verifier 跑成·diff 可解析·含 partial / patch-not-applied)。
    False = 格式失败(producer 产非 diff / 空产出 = 失败 attempt·拉低合规率)。
    None  = infra/配置失败(非 producer 责任·不归因·不计 attempt)。
    """
    if result.get("ok") is True:
        return True
    reason = (result.get("reason") or "").lower()
    if any(m in reason for m in _FORMAT_FAIL_MARKERS):
        return False
    if any(m in reason for m in _INFRA_MARKERS):
        return None
    # ok=False 且 reason 不明 → 保守:不归因(不冤枉 producer)
    return None


def _skill_for(spec: dict) -> tuple[str, str]:
    """(task_type, skill_tag)· skill_tag = 能力名(V5 读端按它路由)。"""
    if spec.get("swe_instance_id"):
        return (str(spec.get("bench_family") or "swe"), "swe-unified-diff")
    if spec.get("kb_problem_id") is not None:
        return ("kernelbench", "kernelbench-kernel")
    return ("t3-bench", str(spec.get("kind") or "code-fix"))


def derive_capability(task: dict, result: dict) -> Optional[dict]:
    """从 (task, result) 推能力归因。纯函数。

    无 claimed_by(无主)或 infra 失败 → None(不写)。
    """
    agent_id = task.get("claimed_by")
    if not agent_id:
        return None
    fmt = classify_format(result)
    if fmt is None:
        return None
    spec = parse_t3_spec(task) or {}
    task_type, skill_tag = _skill_for(spec)
    return {
        "agent_id": str(agent_id),
        "task_type": task_type,
        "skill_tag": skill_tag,
        "format_ok": bool(fmt),
        "score": float(result.get("reward") or 0.0),
        "bounty_id": task.get("task_uid"),
    }
