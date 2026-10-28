#!/usr/bin/env python3
"""Path B(correctness-binary RSI)verifier 核 — 纯逻辑(2026-06-18·节点4 首砖)。

KernelBench speedup-RSI 证负后的 redirect:reward = 测试通过数(离散·无计时噪声·
fail→pass 是真梯度)。本模块只做纯逻辑(解析 pytest 输出 + 抽 grounded 记忆 + reward 判定），
repo-clone/apply-patch/run-pytest 的 effect 层后续片(走 GPU/容器·R3 时不建）。

判据(替 raw speedup·无需噪声门=离散）:
  reward = n_passed。rsi_improved = turn2_passed > turn1_passed(整数比较·确定）。

设计见 docs/PATH_B_RSI_CORRECTNESS_BINARY_DESIGN_20260618.md。
"""
from __future__ import annotations

import re

# pytest 末行 summary:"=== 5 passed, 3 failed, 1 error in 2.3s ===" 等
# 🔴 用 [ \t]+ 不用 \s+：\s 含换行会把 "got 4\nERROR ..." 跨行误匹配成 error 计数。
_SUMMARY = re.compile(
    r"(?:(\d+)[ \t]+passed)|(?:(\d+)[ \t]+failed)|(?:(\d+)[ \t]+error)", re.IGNORECASE)
# 失败行:"FAILED tests/test_x.py::test_foo - AssertionError: ..."
_FAILED_LINE = re.compile(r"^(?:FAILED|ERROR)\s+(\S+)(?:\s+-\s+(.*))?$", re.MULTILINE)


def parse_pytest_summary(stdout: str) -> dict:
    """pytest stdout → {passed,failed,errored}。无 summary → 全 0 + ok=False。"""
    passed = failed = errored = 0
    found = False
    for m in _SUMMARY.finditer(stdout):
        found = True
        if m.group(1):
            passed = int(m.group(1))
        elif m.group(2):
            failed = int(m.group(2))
        elif m.group(3):
            errored = int(m.group(3))
    return {"passed": passed, "failed": failed, "errored": errored, "parsed": found}


def extract_failed_tests(stdout: str, max_n: int = 8) -> list[dict]:
    """抽 FAILED/ERROR 行 → [{test, reason}]。喂 grounded 记忆(真实失败·非泛化）。"""
    out = []
    for m in _FAILED_LINE.finditer(stdout):
        out.append({"test": m.group(1), "reason": (m.group(2) or "").strip()})
        if len(out) >= max_n:
            break
    return out


def swe_reward(summary: dict) -> int | None:
    """reward = 通过数。未 parse 到(编译/import 崩)→ None(诚实·不计 0 混入梯度）。"""
    if not summary.get("parsed"):
        return None
    return summary["passed"]


def rsi_improved(turn1_passed: int | None, turn2_passed: int | None) -> bool:
    """离散判据:turn-2 通过数 > turn-1。无噪声门(整数确定）。None 不算改进。"""
    if turn1_passed is None or turn2_passed is None:
        return False
    return turn2_passed > turn1_passed


_FAIL_HDR = re.compile(r"^=+\s*FAILURES\s*=+\s*$", re.MULTILINE)
_SECTION_END = re.compile(
    r"^=+\s*(?:warnings summary|short test summary info)\s*=+\s*$", re.MULTILINE)


def extract_failures_section(stdout: str, max_chars: int = 4000) -> str:
    """抓 pytest `= FAILURES =` 到 warnings/summary 之间的真实 traceback 段。

    这是 turn-2 最关键的 grounded 记忆:断言 expected vs got + 触发输入 + 行号。
    只抓 FAILED 摘要行(extract_failed_tests）拿不到 WHY·此段拿得到。无该段 → ""。
    """
    m = _FAIL_HDR.search(stdout)
    if not m:
        return ""
    start = m.start()
    end_m = _SECTION_END.search(stdout, m.end())
    end = end_m.start() if end_m else len(stdout)
    sec = stdout[start:end].strip()
    if len(sec) > max_chars:
        sec = sec[:max_chars] + "\n...(truncated)"
    return sec


def build_swe_memory(patch: str, summary: dict, fails: list[dict],
                     traceback_text: str = "") -> str:
    """从 turn-1 patch + 其失败测试抽 grounded 记忆,注入 turn-2 prompt。

    Grounded:① turn-1 真实测试结果(通过/失败数）② 具体失败测试名 + 报错
    ③ turn-1 patch 原文。让 turn-2 针对性修 fail→pass(这是 KernelBench 缺的梯度）。
    """
    fail_lines = "\n".join(
        "- %s%s" % (f["test"], (" — " + f["reason"]) if f["reason"] else "")
        for f in fails) or "(no per-test failure lines captured)"
    tb = ("\n\nThe exact failure output (assertion expected-vs-got, the triggering input, "
          "and the line) — use this to target the fix precisely:\n```\n%s\n```\n"
          % traceback_text.strip()) if traceback_text.strip() else ""
    return (
        "\n\n## Prior verified attempt (memory from a previous round)\n"
        "A previous patch was applied and the test suite was run. Result:\n"
        "- passed: %d · failed: %d · errored: %d\n\n"
        "These specific tests FAILED — fix them while keeping the passing ones green:\n"
        "%s%s\n\n"
        "Here is that prior patch. Produce an improved patch that makes MORE tests pass "
        "(target the failing tests above) without breaking the passing ones.\n\n"
        "```diff\n%s\n```\n"
        % (summary.get("passed", 0), summary.get("failed", 0),
           summary.get("errored", 0), fail_lines, tb, patch.strip()))
