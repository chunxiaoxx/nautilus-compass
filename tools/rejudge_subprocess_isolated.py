#!/usr/bin/env python3
"""rejudge 抽样层 · 隔离重跑版(J5 技术隔离,非声明级)。

首跑教训(9/30):子进程是完整 agent,给了 2 题 prompt 却自主读取任务文件
判完全部 50 题——能力范围超出预期;同仓源表(arm_a_rows_rejudged.json 含
judge_raw)对它可读,"盲"沦为声明级。本版:临时目录只放 sample_tasks_50.json,
子进程 cwd=临时目录,prompt 用相对路径——judge 信息物理不可达。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "runtime" / "rejudge_check" / "sample_tasks_50.json"
OUT = ROOT / "runtime" / "rejudge_check" / "sample_verdicts.json"

PROMPT = """You are an independent grader. The file sample_tasks_50.json in the
current directory contains 50 items, each with {qid, question, truth,
model_answer}. For EVERY item, decide whether the model_answer is semantically
correct with respect to the question and the official truth. Paraphrase,
synonyms, and numeric/word-form equivalence (e.g. 'five' == '5') count as
CORRECT. An answer with no substantive content (error strings) is INCORRECT.

Read that file and grade all 50. Output STRICTLY one JSON object per line, no
code fences, no preamble:
{"qid": "...", "verdict": "CORRECT" | "INCORRECT", "reason": "<short>"}
"""


def main():
    tmp = Path(tempfile.mkdtemp(prefix="rejudge_blind_"))
    try:
        shutil.copy(TASKS, tmp / "sample_tasks_50.json")
        claude_bin = shutil.which("claude") or shutil.which("claude.cmd")
        env = {k: v for k, v in os.environ.items()
               if k.upper() not in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")}
        env["NO_PROXY"] = "*"
        r = subprocess.run([claude_bin, "-p", PROMPT, "--output-format", "text"],
                           capture_output=True, text=True, timeout=900,
                           env=env, encoding="utf-8", cwd=str(tmp))
        raw = ROOT / "runtime" / "rejudge_check" / "raw_subprocess_out.txt"
        raw.write_text(r.stdout or "", encoding="utf-8")  # J6 原样落盘
        out = []
        # 解析三策略:①裸行 JSON ②```json 块内行 ③首个 JSON 数组整体
        text = r.stdout or ""
        lines = [ln.strip().rstrip(",") for ln in text.splitlines()]
        for ln in lines:
            if ln.startswith("{") and '"qid"' in ln:
                try:
                    out.append(json.loads(ln))
                    continue
                except json.JSONDecodeError:
                    pass
        if len(out) < 50:
            m = re.search(r"\[\s*\{.*\"qid\".*\}\s*\]", text, re.S)
            if m:
                try:
                    arr = json.loads(m.group(0))
                    out = arr if isinstance(arr, list) else out
                except json.JSONDecodeError:
                    pass
        if len(out) < 50:  # ③再试 ```json 围栏内任意逐行
            fence = re.findall(r"```(?:json)?\s*(.*?)```", text, re.S)
            for blk in fence:
                for ln in blk.splitlines():
                    ln = ln.strip().rstrip(",")
                    if ln.startswith("{") and '"qid"' in ln:
                        try:
                            out.append(json.loads(ln))
                        except json.JSONDecodeError:
                            continue
        print(f"[isolated] rc={r.returncode} 判定 {len(out)} 条 "
              f"(stdout {len(r.stdout or '')}B)")
        if not out:
            print("[diag]", (r.stdout or "")[:300])
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print(f"[done] 写入 {OUT.name}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
