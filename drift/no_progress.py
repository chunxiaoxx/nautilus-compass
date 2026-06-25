"""B3 · no-progress 空转检测.

近一月最具体的 dogfood 痛点(本 session 亲踩 15 次): Stop-hook 在双轨全 gated 时逼出
重复的"idle·gated 无变化"·而 `feedback_loop_self_check_stop_when_repeating` memory 早记了
根因(产出强迫+元认知刹车缺失)却是 passive memory·没变成 active 机制。本模块 = 那把刹车:
连续 window 轮输出近乎相同且无新 tool 调用 → 主动 surface "你在空转·该停或问用户"。
同构 metamemory 的"无可靠 evidence"。纯字符串算术·无 LLM·永不抛。
"""
import re


def _normalize(text: str) -> str:
    """去标点/空白/大小写 · 留实质内容做相似比较."""
    t = (text or "").lower()
    t = re.sub(r"[\s··,.，。!?！？\-_、:;]+", "", t)
    return t


def detect_no_progress(recent_outputs, window: int = 3, made_tool_call: bool = False):
    """近 window 条输出近乎相同且无新 tool 调用 → stuck.

    Args:
        recent_outputs: 最近的 assistant 输出文本列表(时间序·末尾最新)。
        window: 看最近几条(默认 3)。
        made_tool_call: 本轮是否有新 tool 调用(有=有进展·不算空转)。
    Returns:
        {"stuck": bool, "repeats": int, "hint": str}
    """
    try:
        if made_tool_call:
            return {"stuck": False, "repeats": 0, "hint": ""}
        outs = [o for o in (recent_outputs or []) if o is not None]
        if len(outs) < window:
            return {"stuck": False, "repeats": 0, "hint": ""}
        tail = outs[-window:]
        norm = [_normalize(o) for o in tail]
        base = norm[-1]
        if not base:
            return {"stuck": False, "repeats": 0, "hint": ""}
        # 近乎相同 = 归一化后全等(已吸收空白/标点/大小写差)
        repeats = sum(1 for n in norm if n == base)
        stuck = repeats >= window
        hint = ""
        if stuck:
            hint = (f"⚠️ no-progress: 近 {repeats} 轮输出零新进展、无新 tool 调用。"
                    f"该停——surface 一个具体 blocker 或问用户,别再空转 poll/重述。")
        return {"stuck": stuck, "repeats": repeats, "hint": hint}
    except Exception:
        return {"stuck": False, "repeats": 0, "hint": ""}
