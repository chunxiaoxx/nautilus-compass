"""幂等 apply · P0 shadow drift 遥测(2026-05-27 · study compass-value-study 验证)。

背景:study 证生产 should_alert(neg_cos≥0.538 OR)在工具调用流 29% alert / ~10% precision
(90% 误报)。v2 = rule_alert(危险命令正则) OR drift_score < 阈值 · 全量 alert ~0.4%。
本脚本把 v2 作为 SHADOW(只记 verification_log 比对 · 不 enforce · should_alert 不变 · R1-R5 护栏不动)
wire 进 daemon.py。

为何是脚本而非直接 commit:本改动落地时 daemon.py 正有未提交的 v2.1.0 在途重构(P4-P9+BM25),
同文件无法只 commit shadow 这一 hunk。脚本 = 可追溯 + 可重放(用户在干净 base 上跑一次即 wire)。

幂等:若 daemon.py 已含 _shadow_rule_alert 则 noop。
用法:python ops/apply_p0_shadow.py
"""
from __future__ import annotations
from pathlib import Path

DAEMON = Path(__file__).resolve().parent.parent / "daemon.py"

ANCHOR = 'NEG_ANCHOR_HIT_THRESHOLD = float(os.environ.get("ZMM_NEG_HIT_THRESHOLD", "0.538"))\n'

SHADOW_BLOCK = '''
# ─── v2 shadow drift detector (2026-05-27 · study-validated · SHADOW ONLY · 不 enforce · R1 护栏不变) ───
ZMM_DRIFT_V2_THRESH = float(os.environ.get("ZMM_DRIFT_V2_THRESH", "-0.07"))
import re as _re_v2
_V2_RULES = [
    _re_v2.compile(r"\\brm\\s+-[a-z]*r[a-z]*\\b"),
    _re_v2.compile(r"git\\s+push\\b.*(--force\\b|\\s-f\\b)"),
    _re_v2.compile(r"git\\s+reset\\s+--hard"),
    _re_v2.compile(r"git\\s+clean\\s+-[a-z]*[fdx]"),
    _re_v2.compile(r"taskkill\\b.*/IM\\b", _re_v2.I),
    _re_v2.compile(r"\\b(killall|pkill)\\b"),
    _re_v2.compile(r"\\b(DROP\\s+(DATABASE|TABLE)|TRUNCATE\\s+TABLE?)\\b", _re_v2.I),
    _re_v2.compile(r"DELETE\\s+FROM\\b(?!.*\\bWHERE\\b)", _re_v2.I | _re_v2.S),
    _re_v2.compile(r"chmod\\s+(-R\\s+)?777\\b"),
    _re_v2.compile(r"\\bsk-[A-Za-z0-9]{16,}"),
    _re_v2.compile(r"(api[_-]?key|password|secret|token)\\s*[=:]\\s*[\\"\\'][^\\"\\'\\s]{12,}[\\"\\']", _re_v2.I),
]
_V2_SAFE_RM = _re_v2.compile(
    r"(node_modules|/dist\\b|\\bdist\\b|/build\\b|\\.cache|__pycache__|\\.tmp\\b|/tmp/|\\.swc\\b|\\.tgz|\\.tar|"
    r"\\.zip|\\.log\\b|\\.lock\\b|package-lock|\\.npmrc|hf_stage|\\.next\\b|\\.turbo|coverage|\\.pytest_cache|\\.mypy_cache)",
    _re_v2.I)
_V2_SAFE_KILL = _re_v2.compile(r"(killall|pkill)\\b[^\\n;|&]*?-f\\s+\\S*(/|\\.py|\\.js|\\.sh|\\.cjs)\\S*", _re_v2.I)
_V2_META = _re_v2.compile(r"^(Edit|Write|Read|MultiEdit):.*(rule_drift|dangerous-commands|_V2_RULES|_RULES)", _re_v2.I)


def _shadow_rule_alert(query: str) -> bool:
    """SHADOW · rule-based 危险动作检测(faithful to compass-value-study/lib/rule_drift.py)。"""
    q = query or ""
    if _V2_META.search(q):
        return False
    for i, rx in enumerate(_V2_RULES):
        if rx.search(q):
            if i == 0 and _V2_SAFE_RM.search(q):
                continue
            if i == 5 and _V2_SAFE_KILL.search(q):
                continue
            return True
    return False

'''

LOG_ANCHOR = '''            "drift_score": (result.get("drift") or {}).get("score"),
            "drift_alert": (result.get("drift") or {}).get("should_alert"),
        }'''

LOG_REPLACE = '''            "drift_score": (result.get("drift") or {}).get("score"),
            "drift_alert": (result.get("drift") or {}).get("should_alert"),
            # v2 shadow (SHADOW ONLY · 不 enforce · 比对用 · 详见 _shadow_rule_alert)
            "rule_hit": _shadow_rule_alert(query),
            "drift_alert_v2": bool(
                _shadow_rule_alert(query)
                or (((result.get("drift") or {}).get("score") or 0) < ZMM_DRIFT_V2_THRESH)),
        }'''


def main() -> int:
    text = DAEMON.read_text(encoding="utf-8")
    if "_shadow_rule_alert" in text:
        print("[OK] already applied (noop)")
        return 0
    if ANCHOR not in text:
        print("[FAIL] anchor (NEG_ANCHOR_HIT_THRESHOLD) not found - daemon.py changed - wire manually")
        return 1
    if LOG_ANCHOR not in text:
        print("[FAIL] verification_log anchor not found - wire 2 fields manually")
        return 1
    text = text.replace(ANCHOR, ANCHOR + SHADOW_BLOCK, 1)
    text = text.replace(LOG_ANCHOR, LOG_REPLACE, 1)
    DAEMON.write_text(text, encoding="utf-8")
    print("[OK] applied - restart daemon (daemon.py stop + daemon_start.sh); verification_log will carry rule_hit/drift_alert_v2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
