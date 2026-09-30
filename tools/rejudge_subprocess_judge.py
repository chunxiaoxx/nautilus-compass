#!/usr/bin/env python3
"""rejudge 抽样层:子进程 claude 盲判 50 题(J5:任务字段级排除 judge 信息)。

预注册:docs/metering/REJUDGE_RECOMPUTE_PREREG_20260930.md(修正#1 后名单
sha16=572d4cc73ff5db3e)。子进程配方=清代理+显式 model(bc1-launch-eve
20260926 验证过)。批量:每批 25 题,输出 JSON 行。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "runtime" / "rejudge_check" / "sample_tasks_50.json"
OUT = ROOT / "runtime" / "rejudge_check" / "sample_verdicts.json"
BATCH = 5  # Windows .CMD 命令行 32K 上限:25 题 prompt ~22K 贴顶秒退(实测),压到 5
MODEL = ""  # 空=用 CLI 默认(本机宿主 glm-5.3-flash;'haiku' 别名在自定义
            # model 路由下不存在,实测 unrecognized_model → 探针证伪留档)

PROMPT_TMPL = """You are an independent grader. For each item below, decide whether
the MODEL ANSWER is semantically correct with respect to the QUESTION and the
OFFICIAL TRUTH. Paraphrase, synonym, or equivalent numeric/word forms count as
CORRECT. Answer must be inside the answer text (not implied by omission).

Output STRICTLY one JSON object per line, format:
{{"qid": "<qid>", "verdict": "CORRECT" | "INCORRECT", "reason": "<one short sentence>"}}

Items:
{items}"""


def item_block(t: dict) -> str:
    return (f"- qid: {t['qid']}\n  question: {t['question'][:400]}\n"
            f"  official truth: {str(t['truth'])[:300]}\n"
            f"  model answer: {str(t['model_answer'])[:400]}")


def run_batch(tasks: list) -> list:
    prompt = PROMPT_TMPL.format(items="\n".join(item_block(t) for t in tasks))
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY")}
    env["NO_PROXY"] = "*"
    claude_bin = shutil.which("claude") or shutil.which("claude.cmd") or "claude"
    cmd = [claude_bin, "-p", prompt, "--output-format", "text"]
    if MODEL:
        cmd += ["--model", MODEL]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                       env=env, encoding="utf-8")
    out = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{") and '"qid"' in line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not out:
        print(f"    [diag] rc={r.returncode} stdout_head={(r.stdout or '')[:150]!r} "
              f"stderr_head={(r.stderr or '')[:150]!r}", file=sys.stderr)
    return out


def main():
    tasks = json.loads(TASKS.read_text(encoding="utf-8"))
    verdicts = []
    for i in range(0, len(tasks), BATCH):
        batch = tasks[i:i + BATCH]
        t0 = time.time()
        got = run_batch(batch)
        verdicts += got
        print(f"[batch {i//BATCH+1}] {len(batch)} 题 → {len(got)} 判定 "
              f"({time.time()-t0:.0f}s)", file=sys.stderr)
    OUT.write_text(json.dumps(verdicts, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"[done] {len(verdicts)}/{len(tasks)} 判定写入 sample_verdicts.json")


if __name__ == "__main__":
    main()
