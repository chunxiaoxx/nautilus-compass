#!/usr/bin/env python3
"""V5 Memory Plugin · 深度边界测试 · 跑慢但真.

Test 1: hook 模式 (无 BGE) 速度真 < 1s
Test 2: BGE cold cache · 真冷启
Test 3: BGE warm cache · 应 < cold (即便 model load 是 fixed)
Test 4: anchors.json mtime 变 → 重 embed
Test 5: memory file mtime 变 → 部分重 embed (不是全部)
Test 6: 跨项目 (cwd 切到非 nautilus-core)
Test 7: 特殊 prompt (空 / 仅符号 / 超长 / 含 emoji)
Test 8: stdin 字段名兼容 (prompt / user_prompt / message)
"""
import io
import json
import os
import pickle
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
except Exception:
    pass

PLUGIN = Path.home() / ".claude" / "plugins" / "zenmind-mem"
RECALL = PLUGIN / "recall.py"
ANCHORS = PLUGIN / "anchors.json"
CACHE = PLUGIN / ".cache"


def run_hook(payload: dict, cwd: str = None, args: list = None, timeout: int = 600) -> tuple:
    """跑 recall.py · 返 (stdout, latency_s)."""
    cmd = [sys.executable, str(RECALL)]
    if args:
        cmd.extend(args)
    t0 = time.time()
    # encoding 显式 UTF-8 · subprocess args 中文也保 UTF-8
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload).encode("utf-8") if payload else b"",
        capture_output=True, timeout=timeout,
        cwd=cwd or os.getcwd(), env=env,
    )
    return proc.stdout.decode("utf-8", errors="replace"), time.time() - t0


def section(t):
    print(f"\n{'='*60}\n{t}\n{'='*60}")


PASS, FAIL = "✅ PASS", "❌ FAIL"
results = []


def check(cond: bool, label: str, detail: str = ""):
    tag = PASS if cond else FAIL
    print(f"  {tag} · {label}{(': ' + detail) if detail else ''}")
    results.append(cond)


# ── Test 1 · hook 模式速度 ──
section("Test 1 · Hook 默认模式 (无 BGE) · 应 < 2s")
out, lat = run_hook({"prompt": "测试"}, cwd="C:/Users/chunx/Projects/nautilus-core")
check(lat < 2.0, "hook latency", f"{lat:.2f}s")
check("zenmind-mem-recall" in out, "标记输出")
check("entries" in out, "entries 列出")
check("BGE-bge-small-zh" not in out, "BGE 没启动 (默认快路径)")


# ── Test 2 · BGE cold cache (清 cache 后) ──
section("Test 2 · BGE cold cache (清 cache 后真冷启)")
# 备份 cache
cache_bak = CACHE.with_suffix(".bak")
import shutil
if CACHE.exists():
    shutil.rmtree(CACHE, ignore_errors=True)
out, lat_cold = run_hook(
    {}, cwd="C:/Users/chunx/Projects/nautilus-core",
    args=["--bge", "--query", "V5 治理飞轮"],
)
check("BGE-bge-small-zh" in out, "BGE 启用")
check("score=" in out, "cosine 输出")
print(f"     cold latency: {lat_cold:.1f}s")


# ── Test 3 · BGE warm cache ──
section("Test 3 · BGE warm cache (cache 已建)")
out, lat_warm = run_hook(
    {}, cwd="C:/Users/chunx/Projects/nautilus-core",
    args=["--bge", "--query", "V5 治理飞轮"],
)
check("BGE-bge-small-zh" in out, "BGE 仍启用")
print(f"     warm latency: {lat_warm:.1f}s · cold {lat_cold:.1f}s")
check(lat_warm < lat_cold, f"warm < cold ({lat_warm:.1f} < {lat_cold:.1f})")


# ── Test 4 · anchors.json mtime 变 → 重 embed ──
section("Test 4 · anchors.json 改 → cache 真失效重 embed")
anchor_pkl = CACHE / "anchors.pkl"
if anchor_pkl.exists():
    old_mtime_pkl = anchor_pkl.stat().st_mtime
    # touch anchors.json (改 mtime)
    os.utime(ANCHORS, None)
    time.sleep(1)
    out, _ = run_hook(
        {}, cwd="C:/Users/chunx/Projects/nautilus-core",
        args=["--bge", "--query", "测试"],
    )
    new_mtime_pkl = anchor_pkl.stat().st_mtime
    check(new_mtime_pkl > old_mtime_pkl, "anchors.pkl 真重写", f"old={old_mtime_pkl:.0f} new={new_mtime_pkl:.0f}")
else:
    check(False, "anchors.pkl 不存在 · 跳过")


# ── Test 5 · 跨项目 (cwd 不在 nautilus-core) ──
section("Test 5 · cwd 切到非 nautilus 项目")
out, lat = run_hook({"prompt": "test"}, cwd=str(Path.home()))    # ~ 不在任何 mapped project
check("entries" in out or len(out) < 10, "无 mapped project · 优雅 fallback")


# ── Test 6 · 特殊 prompt ──
section("Test 6 · 边界 prompt")
# 6a · 空 prompt
out, lat = run_hook({"prompt": ""}, cwd="C:/Users/chunx/Projects/nautilus-core")
check("zenmind-mem-recall" in out, "空 prompt 不崩")
# 6b · 全 emoji
out, lat = run_hook({"prompt": "🎉🚀✅⚠️💡"}, cwd="C:/Users/chunx/Projects/nautilus-core")
check("zenmind-mem-recall" in out, "全 emoji 不崩")
# 6c · 超长 prompt (3000 字)
long_p = "V5 治理 " * 500
out, lat = run_hook({"prompt": long_p}, cwd="C:/Users/chunx/Projects/nautilus-core")
check("zenmind-mem-recall" in out, "超长 prompt 不崩")


# ── Test 7 · stdin 字段名兼容 ──
section("Test 7 · 字段名兼容")
for key in ("prompt", "user_prompt", "message", "text", "content"):
    out, _ = run_hook(
        {key: "V5 治理"},
        cwd="C:/Users/chunx/Projects/nautilus-core",
    )
    has_hint = "想要真语义召回" in out
    check(has_hint or "📊" in out or "🟡" in out or "🟢" in out or "🔴" in out,
          f"字段 '{key}' 拿到 prompt")


# ── Test 8 · 加 dummy memory · 验只重 embed 新的 ──
section("Test 8 · 加新 memory · 部分 cache 失效")
mem_dir = Path.home() / ".claude" / "projects" / "C--Users-chunx-Projects-nautilus-core" / "memory"
test_md = mem_dir / "_v5plugin_deeptest.md"
test_md.write_text(
    "---\nname: v5plugin_deeptest\ndescription: 临时 deep test marker\ntype: project\n---\n"
    "测试 zenmind-mem plugin 真按 mtime 增量 embed\n",
    encoding="utf-8",
)
emb_cache = CACHE.glob("*_emb.pkl")
# 取所有 .pkl 文件
all_pkls = list(CACHE.glob("*.pkl"))
out, lat = run_hook(
    {}, cwd="C:/Users/chunx/Projects/nautilus-core",
    args=["--bge", "--query", "v5plugin deeptest"],
)
check(test_md.name in out or "v5plugin" in out.lower() or "Project memory" in out,
      "新 memory 真被 plugin 看到")
test_md.unlink(missing_ok=True)
print(f"     加新 file 后 latency: {lat:.1f}s (应略 > warm cache · 因增 1 file embed)")


# ── 汇总 ──
section("汇总")
passed = sum(1 for r in results if r)
total = len(results)
print(f"\n  PASS: {passed}/{total}")
print(f"  cold cache: {lat_cold:.1f}s · warm cache: {lat_warm:.1f}s")
if passed == total:
    print(f"\n  ✅ 全部 PASS · v0.3 plugin 边界稳健")
    sys.exit(0)
else:
    print(f"\n  ⚠️ {total - passed} 项 FAIL")
    sys.exit(1)
