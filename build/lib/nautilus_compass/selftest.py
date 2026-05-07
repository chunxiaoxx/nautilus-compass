#!/usr/bin/env python3
"""V5 Memory Plugin 端到端自测 · 跑完输出 PASS/FAIL 表."""
import json
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

PLUGIN_USER = Path.home() / ".claude" / "plugins" / "nautilus-compass"
# CI / dev · fall back to the script's own directory when the user-level
# plugin install hasn't happened yet (eg. fresh clone, no pip install).
PLUGIN = PLUGIN_USER if PLUGIN_USER.exists() else Path(__file__).resolve().parent


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
section("Test 1 · BGE daemon 召回 (--bge mode)")
t0 = time.time()
out1 = run_hook("V5 治理 11 天 · 飞轮真转吗 · stake fulfilled", bge=True)
t1 = time.time()
print(f"  耗时: {t1-t0:.2f}s (daemon warm 应 < 5s · cold ~120s)")
results.append(assert_in("BGE-bge-small-zh", out1, "BGE 召回真启用"))
results.append(assert_in("score=", out1, "cosine score 真输出"))
results.append((t1 - t0 < 30, f"daemon warm < 30s · 实测 {t1-t0:.2f}s"))


# ── Test 2 · v0.3 反锚点 alert ──
section("Test 2 · Drift detection 反锚点 alert")
out2 = run_hook("我用 12 天前的 memory 倒批今天判断 · 不验证就声称完成", bge=True)
results.append(assert_in("⚠️ 偏向反锚点", out2, "反锚点 alert 触发"))
results.append(assert_in("用 12d old memory 倒批", out2, "命中正确反锚点"))


# ── Test 3 · 正常 query 不误触发 ──
section("Test 3 · 正常 query 不误触发 alert")
out3 = run_hook("继续推 v0.4 strategy store")
neg_alert = "⚠️ 偏向反锚点" in out3
results.append((not neg_alert, f"正常 query 无误 alert (alert={neg_alert})"))


# ── Test 4 · 时间戳分组逻辑 ──
section("Test 4 · 时间戳分组")
out4 = run_hook("V5")    # 短 query · 无 BGE 召回时回 metadata 模式
# BGE 模式下也有 + 24h 内其他 memory · 检查 fresh + old 都识别
fresh_present = "1d old" in out1 or "h old" in out1
old_present = "1mo old" in out1 or "13d old" in out1
results.append((fresh_present, f"时间戳显示 fresh memory (1d/h old): {fresh_present}"))
results.append((old_present, f"时间戳显示 old memory (1mo/13d): {old_present}"))


# ── Test 5 · anchors.json mtime cache 失效 ──
section("Test 5 · anchors cache by mtime")
anchor_pkl = PLUGIN / ".cache" / "anchors.pkl"
results.append((anchor_pkl.exists(), f"anchors.pkl 已 cache: {anchor_pkl.exists()}"))
embed_cache_dir_files = list((PLUGIN / ".cache").glob("*.pkl"))
results.append((len(embed_cache_dir_files) >= 2, f"cache 文件 ≥ 2 (anchors + memory): {len(embed_cache_dir_files)}"))


# ── 最终汇总 ──
section("汇总")
passed = sum(1 for r in results if (r[0] if isinstance(r, tuple) else r))
total = len(results)
print(f"\n  PASS: {passed}/{total}")
if passed == total:
    print(f"\n  ✅ V5 Memory Plugin v0.3 端到端全 PASS · 真在工作")
    sys.exit(0)
else:
    print(f"\n  ⚠️ {total-passed} 项失败 · 见上")
    sys.exit(1)
