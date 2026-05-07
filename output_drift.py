"""compass v0.9 · assistant 输出侧 drift 检测.

补齐 v0.8 之前的盲区 · UserPromptSubmit / PostToolUse hook 只监控
输入和工具调用 · assistant 自己说的话不监控. 本模块在 stop_hook
里取本次 session 的 assistant 回复序列 · 按 embedding 漂移打分.

检测维度(全部黑盒 · 不读模型内部):
  1. 语言漂移 · 用户讲 zh · assistant 第 k 轮切 en → 报警
  2. 风格漂移 · 首轮简洁 · 第 k 轮冗长 markdown → 报警
  3. 人格漂移 · cos(r_k, r_0) < 0.6 · 越跑越偏 anchor → 报警

触发条件(在 stop_hook 尾部)：
  · session 长度 >= 5 回复
  · 任一维度超阈值 → 写 .cache/output_drift_log.jsonl
  · 同时 append 到 mid_session 告警流 · 下轮注入到 system prompt
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent
CACHE_DIR = PLUGIN_DIR / ".cache"
LOG_FILE = CACHE_DIR / "output_drift_log.jsonl"

# 阈值 · 偏保守 · 实测 7 天调
LANG_SWITCH_PCT = 0.35  # 相邻两轮 en/zh 比例差 > 35% → 报警
STYLE_LEN_RATIO = 3.0   # 第 k 轮长度 / 首轮中位数 > 3 → 冗长漂移
PERSONA_COS_MIN = 0.60  # cos(r_k, r_0) < 0.60 → 人格漂移


def detect_zh_en_ratio(text: str) -> float:
    """返回中文字符占比 · 0 = 全英 · 1 = 全中."""
    if not text:
        return 0.0
    zh = len(re.findall(r"[一-鿿]", text))
    en = len(re.findall(r"[A-Za-z]", text))
    total = zh + en
    return zh / total if total else 0.0


def check_language_drift(responses: list[str]) -> dict | None:
    """用户第一轮确立语言 · 后续 assistant 若切换 → 报警."""
    if len(responses) < 3:
        return None
    baseline = detect_zh_en_ratio(responses[0])
    for i, r in enumerate(responses[1:], 1):
        cur = detect_zh_en_ratio(r)
        if abs(cur - baseline) > LANG_SWITCH_PCT:
            return {
                "dim": "language",
                "first_turn_zh_ratio": round(baseline, 3),
                "drift_turn": i,
                "drift_zh_ratio": round(cur, 3),
                "severity": "high" if abs(cur - baseline) > 0.5 else "medium",
            }
    return None


def check_style_drift(responses: list[str]) -> dict | None:
    """首轮 3 回复的中位长度做 baseline · 后续不得 > 3× median."""
    if len(responses) < 5:
        return None
    lengths = [len(r) for r in responses]
    early = sorted(lengths[:3])
    baseline = early[len(early) // 2]
    for i, n in enumerate(lengths[3:], 3):
        if baseline > 0 and n / baseline > STYLE_LEN_RATIO:
            return {
                "dim": "style",
                "baseline_median_chars": baseline,
                "drift_turn": i,
                "drift_chars": n,
                "ratio": round(n / baseline, 2),
                "severity": "medium",
            }
    return None


def check_persona_drift(responses: list[str], embedder=None) -> dict | None:
    """cos(r_k, r_0) < 0.60 → 人格漂移 · 需要 embedder."""
    if len(responses) < 5 or embedder is None:
        return None
    try:
        emb_0 = embedder.encode(responses[0][:1500])
        import numpy as np
        for i, r in enumerate(responses[1:], 1):
            emb_k = embedder.encode(r[:1500])
            a = np.asarray(emb_0, dtype=float)
            b = np.asarray(emb_k, dtype=float)
            na, nb = (a @ a) ** 0.5, (b @ b) ** 0.5
            cos = float(a @ b / (na * nb)) if na and nb else 0.0
            if cos < PERSONA_COS_MIN:
                return {
                    "dim": "persona",
                    "baseline_turn": 0,
                    "drift_turn": i,
                    "cos_vs_first": round(cos, 3),
                    "severity": "high" if cos < 0.45 else "medium",
                }
    except Exception as e:
        return {"dim": "persona", "error": str(e)[:80]}
    return None


def check_all(responses: list[str], embedder=None) -> list[dict]:
    """跑三维检测 · 返回告警列表 · 空 = 健康."""
    alerts = []
    for fn in (check_language_drift, check_style_drift):
        a = fn(responses)
        if a:
            alerts.append(a)
    pa = check_persona_drift(responses, embedder)
    if pa:
        alerts.append(pa)
    return alerts


def log_drift(alerts: list[dict], session_id: str = "") -> None:
    if not alerts:
        return
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_id": session_id,
        "alerts": alerts,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    # 单元测试 · 不依赖 embedder
    samples = [
        "你好,我来帮你分析这个问题。需要看看代码结构。",
        "好的,先看文件。",
        "I'll help you with this. Let me check the code.",
        "Here is a very long detailed response " * 50,
    ]
    print("lang:", check_language_drift(samples))
    print("style:", check_style_drift(samples))
