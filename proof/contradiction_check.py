"""B5 · 写入时 cross-frame 矛盾检测.

本 session 亲踩: 我把 soul 权威入站的 "valid_rate 0→0.22 在涨" 写成 memory 里的
"valid_rate 0.22→0 掉"(方向写反)·compass 照单全收没拦。本模块 = 写记忆前的轻量
矛盾闸: 新结论与近期权威入站在"同一指标、相反数字方向"上冲突 → flag(只警告·不阻止写)。
纯字符串/数字启发·无 LLM·永不抛。高精度优先(只 flag 高置信的数字箭头反向)。
"""
import re

# 关注的可测指标(出现在新结论 + 近期入站两边才比对)
METRICS = (
    "valid_rate", "win_rate", "uplift", "reward",
    "cumulative_impact", "pass@", "recall", "reinforce", "score",
)

# 数字箭头: a <connector> b · 长 connector 在前(避免被单字'到'截断)
_ARROW = re.compile(
    r"(\d[\d.]*)\s*(?:涨到|跌到|掉到|降到|升到|→|->|=>|到)\s*(\d[\d.]*)"
)


def _arrow_dir(text):
    """返回首个数字箭头的方向: 'up'/'down'/None (b>a=up·b<a=down)。"""
    m = _ARROW.search(text or "")
    if not m:
        return None
    try:
        a, b = float(m.group(1)), float(m.group(2))
    except (TypeError, ValueError):
        return None
    if b > a:
        return "up"
    if b < a:
        return "down"
    return None


def _metrics_in(text):
    low = (text or "").lower()
    return {mt for mt in METRICS if mt in low}


def check_contradiction(new_text, recent_texts):
    """新结论 vs 近期权威入站 · 同指标相反方向 → 返回 warning 列表(空=无矛盾)。永不抛。"""
    warns = []
    try:
        new_dir = _arrow_dir(new_text)
        if new_dir is None:
            return []
        new_metrics = _metrics_in(new_text)
        if not new_metrics:
            return []
        for rt in (recent_texts or []):
            shared = new_metrics & _metrics_in(rt)
            if not shared:
                continue
            r_dir = _arrow_dir(rt)
            if r_dir is None:
                continue
            if r_dir != new_dir:
                metric = sorted(shared)[0]
                warns.append(
                    f"⚠️ 矛盾: 你写 {metric} 方向={new_dir}·但近期权威入站说 {r_dir} "
                    f"(来源片段: '{rt[:60]}')。写前核对——本 session 曾把 valid_rate 0→0.22 读反。"
                )
    except Exception:
        return []
    return warns
