#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10/11 终检脚本 v1(2026-10-08 固化,承 R339 预演 9/10 + R340 三口径修正)。

三口径判据(状态≠内容≠可用,逐点并列):
  A. HTTP 状态码(仅可达性)
  B. 内容锚(页面关键字符串,内容级)
  C. 活数据源(SPA 页读 JSON 端点而非渲染后 DOM——R339 WARN 根因修正)
可选:--render 用 Chrome headless 验 SPA 渲染后 DOM(R349 配方)。

用法:
  python runtime/loop/final_check.py            # 10 点快检(A+B+C)
  python runtime/loop/final_check.py --render   # 追加渲染口径(data/compass 两 SPA)
退出码:0=全 PASS / 1=有 WARN / 2=有 FAIL
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = "https://nautilus.social"
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"

# (名称, URL, 内容锚列表)——锚=内容级判据,缺一即 WARN
POINTS = [
    ("榜页", f"{BASE}/leaderboard.html",
     ["26.7", "16.7", "sha16", "caveat"]),
    ("受理入口", f"{BASE}/intake.html",
     ["L1", "L2", "L3", "SLA"]),
    ("判据披露", f"{BASE}/criteria/",
     ["判据", "预注册"]),
    ("判读卡状态页", f"{BASE}/status.html",
     ["judge_status", "fetch"]),
    ("registry 仪表", f"{BASE}/registry.html",
     ["fetch('/corpus_stats.json')"]),
    ("管道页", f"{BASE}/pipeline.html",
     ["管道", "pipeline"]),
    ("compass 子域", "https://compass.nautilus.social/",
     ["NACRE", "LongMemEval"]),
    ("HF 判分模型", "https://huggingface.co/nautilus-compass/nacre-judge-v1",
     ["nacre-judge"]),
    ("HF 元基准", "https://huggingface.co/datasets/nautilus-compass/caliber-bench-v0",
     ["caliber-bench"]),
]

# 活数据源(SPA 异步数字不在静态 HTML 里,读 JSON 正本)
LIVE = [
    ("语料计数", f"{BASE}/corpus_stats.json",
     lambda d: int(d.get("merged_unique_by_qid", 0)) >= 2200),
    ("判读状态 API", f"{BASE}/api/judge_status?id=nautilus-l1-0001",
     lambda d: d.get("ok") is True and d.get("criteria_sha16") == "b81eca8436887785"),
]

RENDER_POINTS = [
    ("data 站渲染", "https://data.nautilus.social/",
     ["验货", "PASS", "判据"]),
]


def curl(url: str, timeout: int = 20) -> tuple[int, str]:
    r = subprocess.run(["curl", "-s", "--max-time", str(timeout), "-w", "\n%{http_code}", url],
                       capture_output=True, text=True, timeout=timeout + 10)
    body, _, code = r.stdout.rpartition("\n")
    return int(code or 0), body


def check_point(name: str, url: str, anchors: list[str]) -> str:
    code, body = curl(url)
    if code != 200:
        return f"FAIL {name}: HTTP {code}"
    missing = [a for a in anchors if a not in body]
    if missing:
        return f"WARN {name}: 200 但内容锚缺失 {missing}"
    return f"PASS {name}"


def check_live(name: str, url: str, predicate) -> str:
    try:
        code, body = curl(url)
        d = json.loads(body)
        if predicate(d):
            return f"PASS {name}(活数据: {json.dumps(d, ensure_ascii=False)[:90]})"
        return f"FAIL {name}: 数据不满足判据 {json.dumps(d, ensure_ascii=False)[:120]}"
    except Exception as e:
        return f"FAIL {name}: {type(e).__name__} {e}"


def check_render(name: str, url: str, anchors: list[str]) -> str:
    if not Path(CHROME).exists():
        return f"WARN {name}: Chrome 不在预期路径,渲染口径跳过"
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--dump-dom",
                        f"--virtual-time-budget=15000", url],
                       capture_output=True, timeout=60)
    dom = r.stdout.decode(errors="replace")
    missing = [a for a in anchors if a not in dom]
    if len(dom) < 5000:
        return f"FAIL {name}: 渲染后仅 {len(dom)}B(疑似壳)"
    if missing:
        return f"WARN {name}: 渲染 {len(dom)}B 但锚缺失 {missing}"
    return f"PASS {name}(渲染 {len(dom)}B)"


def main() -> int:
    results = []
    for name, url, anchors in POINTS:
        results.append(check_point(name, url, anchors))
    for name, url, pred in LIVE:
        results.append(check_live(name, url, pred))
    if "--render" in sys.argv:
        for name, url, anchors in RENDER_POINTS:
            results.append(check_render(name, url, anchors))

    n_pass = sum(1 for r in results if r.startswith("PASS"))
    n_warn = sum(1 for r in results if r.startswith("WARN"))
    n_fail = sum(1 for r in results if r.startswith("FAIL"))
    for r in results:
        print(r)
    print(f"\n=== 终检快检: {n_pass} PASS / {n_warn} WARN / {n_fail} FAIL ===")
    return 2 if n_fail else (1 if n_warn else 0)


if __name__ == "__main__":
    raise SystemExit(main())
