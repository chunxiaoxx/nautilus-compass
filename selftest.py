#!/usr/bin/env python3
"""V5 Memory Plugin 端到端自测 · 跑完输出 PASS/FAIL 表."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

PLUGIN = Path(os.environ.get("COMPASS_SELFTEST_PLUGIN", Path(__file__).resolve().parent))


def run_hook(prompt: str, bge: bool = False) -> str:
    """模拟 Claude Code UserPromptSubmit hook 调用."""
    args = [sys.executable, str(PLUGIN / "recall.py")]
    if bge:
        args.extend(["--bge", "--query", prompt])
        proc = subprocess.run(args, capture_output=True, timeout=180)
    else:
        payload = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        proc = subprocess.run(
            args,
            input=payload.encode("utf-8"),
            capture_output=True, timeout=120,
        )
    return proc.stdout.decode("utf-8", errors="replace")


def section(title: str) -> None:
    print(f"\n{'='*60}\n{title}\n{'='*60}")


def assert_in(needle: str, hay: str, label: str) -> bool:
    ok = needle in hay
    tag = "✅ PASS" if ok else "❌ FAIL"
    print(f"  {tag} · {label}: {needle[:50]}")
    return ok


results = []


# ── Test 1 · v0.2/0.3.5 BGE daemon 召回 ──
section("Test 1 · BGE daemon recall (--bge mode)")
t0 = time.time()
out1 = run_hook("V5 governance loop · stake fulfilled", bge=True)
t1 = time.time()
print(f"  耗时: {t1-t0:.2f}s (daemon warm 应 < 5s · cold ~120s)")
results.append(assert_in("nautilus-compass v2.3.0", out1, "current plugin version"))
results.append((bool(re.search(r"BGE-bge-[\w.-]+", out1)), "BGE recall backend emitted"))
results.append(assert_in("score=", out1, "cosine score output"))
results.append((t1 - t0 < 30, f"daemon warm < 30s · 实测 {t1-t0:.2f}s"))


# ── Test 2 · v0.3 反锚点 alert ──
section("Test 2 · Drift detection block")
out2 = run_hook("Use stale memory to judge current work without verification", bge=True)
results.append(assert_in("[Persona drift", out2, "drift block emitted"))
results.append((bool(re.search(r"score=[+-]?\d+\.\d+", out2)), "drift score emitted"))
results.append(assert_in("时间戳 = 关键", out2, "timestamp warning emitted"))


# ── Test 3 · 正常 query 不误触发 ──
section("Test 3 · Normal query does not trigger red alert")
out3 = run_hook("继续推 v0.4 strategy store")
red_alert = "🔴 alert" in out3
results.append((not red_alert, f"normal query has no red alert (alert={red_alert})"))


# ── Test 4 · 时间戳分组逻辑 ──
section("Test 4 · 时间戳分组")
out4 = run_hook("V5")    # 短 query · 无 BGE 召回时回 metadata 模式
# BGE 模式下也有 + 24h 内其他 memory · 检查 fresh + old 都识别
timestamp_present = bool(re.search(r"\[\s*\d+\w?\s+old\]", out1))
results.append((timestamp_present, f"timestamp labels emitted: {timestamp_present}"))


# ── Test 5 · anchors.json mtime cache 失效 ──
section("Test 5 · Runtime assets")
results.append(((PLUGIN / "anchors.json").exists(), f"anchors.json exists: {(PLUGIN / 'anchors.json').exists()}"))
results.append(((PLUGIN / "recall.py").exists(), f"recall.py exists: {(PLUGIN / 'recall.py').exists()}"))


# ── 最终汇总 ──
section("汇总")
passed = sum(1 for r in results if (r[0] if isinstance(r, tuple) else r))
total = len(results)
print(f"\n  PASS: {passed}/{total}")
if passed == total:
    print(f"\n  ✅ nautilus-compass v2.3 selftest PASS")
    sys.exit(0)
else:
    print(f"\n  ⚠️ {total-passed} 项失败 · 见上")
    sys.exit(1)
