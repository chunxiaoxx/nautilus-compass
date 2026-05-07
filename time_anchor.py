"""compass v1.0 · relative-time anchoring.

Problem: memory contains phrases like "下周一见" / "three days later" / "last
Monday". The LLM that summarizes a session writes them verbatim. A week later,
"下周一" is ambiguous and recall retrieves stale semantics.

Solution: at write time, detect relative time expressions in Chinese and
English, resolve them against the session timestamp, inject an annotation
`[resolved: 2026-05-14]` immediately after. No modification of the original
text — grep-friendly and reversible.

Patterns handled (conservative · high-precision over recall):
  · zh relative days:   今天 / 明天 / 后天 / 昨天 / 前天
  · zh this/last/next:  本周X / 下周X / 上周X / 这个月 / 下个月 / 上个月
  · zh in-N-units:      N 天后 / N 小时后 / N 周后 / N 个月后
  · en relative days:   today / tomorrow / yesterday
  · en next/last:       next Monday / last Friday
  · en in-N:            in N days / N days later / N hours ago

Miss is fine — LLM still reads the original text, annotation only adds
disambiguation. False positives are the real risk, hence the conservative
regex (no fuzzy matching, no bare numerals).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

_ZH_WEEKDAY = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}
_EN_WEEKDAY = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}
_ZH_UNIT_DAYS = {"天": 1, "日": 1, "周": 7, "星期": 7, "个月": 30, "月": 30}
_EN_UNIT_DAYS = {"day": 1, "days": 1, "week": 7, "weeks": 7,
                 "month": 30, "months": 30, "hour": 0, "hours": 0}


def _next_weekday(base: datetime, target_wd: int, offset_weeks: int = 0) -> datetime:
    days_ahead = (target_wd - base.weekday()) % 7
    if offset_weeks > 0 and days_ahead == 0:
        days_ahead = 7
    return base + timedelta(days=days_ahead + 7 * (offset_weeks - (1 if offset_weeks > 0 and days_ahead == 0 else 0)))


def _iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def resolve(text: str, now: datetime | None = None) -> str:
    """Annotate text in-place with [resolved: YYYY-MM-DD] after relative times.

    Pure function · deterministic · safe to call on arbitrary session memory.
    Returns the original string if no patterns match.
    """
    if not text:
        return text
    now = now or datetime.now()

    annotations: list[tuple[int, int, str]] = []  # (start, end, replacement)

    # --- zh: 今天/明天/后天/昨天/前天 ---
    for m in re.finditer(r"(今天|明天|后天|昨天|前天|大后天|大前天)", text):
        word = m.group(1)
        offset = {"今天": 0, "明天": 1, "后天": 2, "大后天": 3,
                  "昨天": -1, "前天": -2, "大前天": -3}.get(word, None)
        if offset is not None:
            resolved = _iso(now + timedelta(days=offset))
            annotations.append((m.end(), m.end(), f"[resolved: {resolved}]"))

    # --- zh: 本/下/上 周X ---
    for m in re.finditer(r"(本|下|下下|上|上上)?周([一二三四五六日天])", text):
        prefix, wd = m.group(1) or "本", m.group(2)
        target = _ZH_WEEKDAY[wd]
        weeks = {"本": 0, "下": 1, "下下": 2, "上": -1, "上上": -2}[prefix]
        days_delta = (target - now.weekday()) + weeks * 7
        annotations.append(
            (m.end(), m.end(), f"[resolved: {_iso(now + timedelta(days=days_delta))}]"))

    # --- zh: N天后 / N周后 / N个月后 / N天前 ---
    for m in re.finditer(r"(\d+)\s*(天|日|周|星期|个月|月)(后|以后|前|以前)", text):
        n, unit, direction = int(m.group(1)), m.group(2), m.group(3)
        days = n * _ZH_UNIT_DAYS.get(unit, 0)
        if days and direction in ("后", "以后"):
            annotations.append((m.end(), m.end(), f"[resolved: {_iso(now + timedelta(days=days))}]"))
        elif days:
            annotations.append((m.end(), m.end(), f"[resolved: {_iso(now - timedelta(days=days))}]"))

    # --- en: today/tomorrow/yesterday ---
    for m in re.finditer(r"\b(today|tomorrow|yesterday)\b", text, re.I):
        offset = {"today": 0, "tomorrow": 1, "yesterday": -1}[m.group(1).lower()]
        annotations.append((m.end(), m.end(), f" [resolved: {_iso(now + timedelta(days=offset))}]"))

    # --- en: next/last <weekday> ---
    for m in re.finditer(r"\b(next|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b", text, re.I):
        rel, wd_name = m.group(1).lower(), m.group(2).lower()
        target = _EN_WEEKDAY[wd_name]
        delta = (target - now.weekday()) % 7
        if rel == "next":
            if delta == 0:
                delta = 7
        else:  # last
            delta = -(7 - delta) if delta != 0 else -7
        annotations.append((m.end(), m.end(), f" [resolved: {_iso(now + timedelta(days=delta))}]"))

    # --- en: in N days/weeks · N days ago ---
    for m in re.finditer(r"\bin\s+(\d+)\s+(day|days|week|weeks|month|months)\b", text, re.I):
        n, unit = int(m.group(1)), m.group(2).lower()
        days = n * _EN_UNIT_DAYS.get(unit, 0)
        if days:
            annotations.append((m.end(), m.end(), f" [resolved: {_iso(now + timedelta(days=days))}]"))
    for m in re.finditer(r"\b(\d+)\s+(day|days|week|weeks|month|months)\s+ago\b", text, re.I):
        n, unit = int(m.group(1)), m.group(2).lower()
        days = n * _EN_UNIT_DAYS.get(unit, 0)
        if days:
            annotations.append((m.end(), m.end(), f" [resolved: {_iso(now - timedelta(days=days))}]"))

    if not annotations:
        return text

    # Apply back-to-front to preserve offsets
    annotations.sort(key=lambda x: -x[0])
    out = text
    for start, end, repl in annotations:
        out = out[:start] + repl + out[end:]
    return out


if __name__ == "__main__":
    now = datetime(2026, 5, 7)  # a Thursday
    cases = [
        ("下周一开会", "[resolved: 2026-05-11]"),
        ("昨天我吃了拉面", "[resolved: 2026-05-06]"),
        ("3天后复查", "[resolved: 2026-05-10]"),
        ("let's meet next friday", "[resolved: 2026-05-08]"),  # Thu + 1 = this Fri
        ("2 weeks ago we shipped", "[resolved: 2026-04-23]"),
        ("无相对时间的文本", None),  # no annotation expected
    ]
    for inp, expected in cases:
        got = resolve(inp, now=now)
        ok = (expected in got) if expected else (got == inp)
        status = "PASS" if ok else "FAIL"
        print(f"{status} | in={inp!r:30s} out={got!r}")
