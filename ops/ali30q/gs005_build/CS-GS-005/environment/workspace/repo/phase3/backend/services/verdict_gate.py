"""verdict-gate:鬼打墙真解的第一个**硬门**(2026-06-25)。

背景(用户 6/25):我们反复犯同样的错·像鬼打墙。真根因=所有机制(anchor/anti-pattern
memory/confound 铁律/R1-R5)都是**软的**=注入 prompt 的被动 context·靠模型自我监控应用。
本 session 整天代价就是反复在测量没闭环时下 KILL/PROVEN 结论(KILL->正->稀疏·n=12 小样本)。

此模块把"过早下强结论"从软提醒升级成 **code-enforced 门**:runner 在输出 KILL/PROVEN 前
必须过此门;缺 enforcement artifact 就 BLOCK/降级。不靠"我提醒自己"(anchor #6)·靠代码。

强结论(KILLED/PROVEN)放行的硬条件:
- 必须带 confound-check artifact(confound_checked=True)。
- n_samples >= min_n(小样本强制降级 INCONCLUSIVE·治"4 次 KILLED 全 confound·n 太少")。
- PROVEN 额外须异框验证(cross_frame_verified=True·有偏的自己不能给自己判分·soul verify V5 雏形普世化)。
"""
from __future__ import annotations

STRONG_VERDICTS = ("KILLED", "PROVEN")


def gate_verdict(
    verdict: str,
    *,
    confound_checked: bool,
    n_samples: int = 0,
    min_n: int = 12,
    cross_frame_verified: bool = False,
) -> dict:
    """硬门:决定一个 verdict 能否被发出。

    返回 {allowed: bool, verdict: str, reason: str}:
    - allowed=False:runner 必须 BLOCK(补 enforcement artifact 再来)·不得发出原强结论。
    - allowed=True 且 verdict 被改成 INCONCLUSIVE:小样本降级(诚实·非杀非证)。
    - allowed=True 且 verdict 不变:放行。
    非强结论(INCONCLUSIVE 等)直接放行(探索期不卡)。
    """
    v = (verdict or "").upper()
    if v not in STRONG_VERDICTS:
        return {"allowed": True, "verdict": verdict, "reason": "非强结论·不门控(探索期允许)"}

    # 硬条件 1:强结论必须先核 confound(本 session 教训:0/KILL 先核 confound 是铁律)
    if not confound_checked:
        return {
            "allowed": False,
            "verdict": "BLOCKED_NEEDS_CONFOUND_CHECK",
            "reason": f"{v} 须带 confound-check artifact 才可发出·先核 confound(adapter/截断/进程/prompt-skew/方向)",
        }

    # 硬条件 2:小样本强制降级(治反复在 n 太小时当真负/真正)
    if n_samples < min_n:
        return {
            "allowed": True,
            "verdict": "INCONCLUSIVE",
            "reason": f"n={n_samples} < min_n={min_n}·样本太小不足以下强结论·降级 INCONCLUSIVE(补料/扩样本再判)",
        }

    # 硬条件 3:PROVEN 须异框验证(有偏的自己不能给自己判正·异框 verify)
    if v == "PROVEN" and not cross_frame_verified:
        return {
            "allowed": False,
            "verdict": "BLOCKED_NEEDS_CROSS_FRAME",
            "reason": "PROVEN 须异框验证(cross_frame_verified)·做 claim 的同一有偏模型不能给自己判正",
        }

    return {"allowed": True, "verdict": v, "reason": "硬门通过(confound 已核·n 足·异框已验)"}
