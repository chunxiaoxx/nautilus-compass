"""compass LIVE-state 自省 (B2) · 答"哪些功能在生产真跑 vs 只是 dormant code".

近一月最硬盲区 = "code complete != live"(v2.3 全代码+测试完成·生产 0 激活)。
每条 probe 是一个可执行命令 + 期望值 · 输出 live/dormant/error · 永不抛。
跑法: python ops/live_state_check.py  (或 import report())

判据约定:
  expect ">N" → probe 输出是整数且 > N  (如 grep -c 命中计数)
  expect "<literal>" → probe 输出 strip 后 == 字面量  (如 systemctl is-active → "active")
"""
import subprocess

# 每个被宣称的功能必须有一条可执行 live 判据 · 加新功能就在这登记(配 B1 价值门)。
FEATURES = [
    {"name": "tier_promotion_timer",
     "probe": ["systemctl", "is-active", "compass-tier-promotion.timer"], "expect": "active"},
    {"name": "l2_distill_timer",
     "probe": ["systemctl", "is-active", "compass-l2-distill.timer"], "expect": "active"},
    {"name": "daemon_reinforce",
     "probe": ["grep", "-c", "COMPASS_NO_REINFORCE", "recall.py"], "expect": ">0"},
    {"name": "daemon_tier_weight",
     "probe": ["grep", "-c", "COMPASS_PROD_TIER_WEIGHT", "daemon.py"], "expect": ">0"},
]


def check_feature_live(feature):
    """Run one feature's probe · return {name, live, status, actual}. NEVER raises."""
    try:
        out = subprocess.run(
            feature["probe"], capture_output=True, text=True, timeout=10
        )
        actual = (out.stdout or "").strip()
        exp = str(feature["expect"])
        if exp.startswith(">"):
            live = actual.isdigit() and int(actual) > int(exp[1:])
        elif exp.startswith("<") and not exp[1:2].isalpha():
            live = actual.isdigit() and int(actual) < int(exp[1:])
        else:
            live = actual == exp
        return {
            "name": feature["name"],
            "live": bool(live),
            "status": "live" if live else "dormant",
            "actual": actual,
        }
    except Exception as e:
        return {
            "name": feature["name"],
            "live": False,
            "status": "error",
            "actual": repr(e),
        }


def report():
    """Run every FEATURE probe · return list of result dicts."""
    return [check_feature_live(f) for f in FEATURES]


if __name__ == "__main__":
    import json

    rep = report()
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    live_n = sum(1 for r in rep if r["live"])
    print(f"\nLIVE {live_n}/{len(rep)} features · dormant/error = code-complete-but-not-running")
