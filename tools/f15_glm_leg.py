#!/usr/bin/env python3
"""F15 meta-judge · glm 腿:verdict 样本抽取 + glm 复判(queue #12 备料件)。

F15 口径(GOALS_20260930):verdict 5% × 三供应商复判,考官面 SLA 一项。
本脚本=glm 腿(coding plan 宿主 glm-5.3-flash,子进程配方与
rejudge_subprocess_judge.py 同款:清代理+显式输出格式)。

纪律:
- 抽样名单先冻结(seed 固定,sha16 落 manifest)——预注册纪律,开跑前可审计
- 默认 dry-run 只出名单;--go 才调 API(额度窗口到即跑)
- --judge-log 接判分器 verdict log(S1 影子期上线后无缝切生产源)

用法:
  python tools/f15_glm_leg.py --dry-run        # 备好:名单+sha 冻结
  python tools/f15_glm_leg.py --go             # 额度窗口内实跑
  python tools/f15_glm_leg.py --agree          # 读数:一致率表
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "runtime" / "verdict_corpus" / "split_test.jsonl"  # 判分语料本源
# (anchor_v0.jsonl 是锚点视图 schema 不同;test 折=判分器三门读数同折,可直接对照。
#  F15 定义=verdict 5%;本腿先行 test 折全量 145(>5% 下限 73),verdict log 上线后回归)
WORK = ROOT / "runtime" / "f15"
MANIFEST = WORK / "glm_leg_manifest.json"
OUT = WORK / "glm_leg_verdicts.jsonl"
SEED = 20261002
BATCH = 5    # 32K 命令行上限(rejudge 实测同因)
MODEL = ""   # 空=宿主默认 glm-5.3-flash(rejudge 同款)

LABELS = ("pass", "fail", "insufficient_evidence")

PROMPT_TMPL = """You are an independent meta-judge re-grading a verification
verdict. For each item: given the criteria, the submitted artifact, and the
official reference, decide pass / fail / insufficient_evidence. Evidence not
present in the item = insufficient_evidence, do not guess.

Output STRICTLY one JSON object per line, format:
{{"id": "<id>", "verdict": "pass" | "fail" | "insufficient_evidence", "reason": "<one short sentence>"}}

Items:
{items}"""


def sample_text(s: dict) -> str:  # 与 train_judge_lora.py 同款口径
    a = s.get("artifact", {})
    parts = [f"criteria: {s.get('criteria_ref', '')[:120]}"]
    for k in ("question", "response", "model_answer", "official_truth",
              "answer_gold", "reason", "rationale"):
        if a.get(k) is not None:
            parts.append(f"{k}: {str(a[k])[:400]}")
    return "\n".join(parts)[:1500]


def item_block(r: dict) -> str:
    return f"- id: {r['id']}\n  {sample_text(r)}"


def freeze_manifest() -> dict:
    rows = [json.loads(l) for l in
            SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    picked = sorted(rows, key=lambda r: r["id"])  # test 折全量,无抽样
    blob = "".join(r["id"] + "\n" for r in picked).encode()
    man = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": SRC.name,
           "sampling": "test-fold full(145)", "seed": SEED,
           "n_picked": len(picked),
           "ids_sha16": hashlib.sha256(blob).hexdigest()[:16],
           "ids": [r["id"] for r in picked]}
    WORK.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    (WORK / "glm_leg_sample.json").write_text(
        json.dumps(picked, ensure_ascii=False), encoding="utf-8")
    return man


def run_batch(rows: list) -> list:
    prompt = PROMPT_TMPL.format(items="\n".join(item_block(r) for r in rows))
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
        if line.startswith("{") and '"verdict"' in line:
            try:
                o = json.loads(line)
                if o.get("verdict") in LABELS:
                    out.append(o)
            except json.JSONDecodeError:
                continue
    if not out:
        print(f"    [diag] rc={r.returncode} stdout_head={(r.stdout or '')[:150]!r} "
              f"stderr_head={(r.stderr or '')[:150]!r}", file=sys.stderr)
    return out


def go() -> int:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = json.loads((WORK / "glm_leg_sample.json").read_text(encoding="utf-8"))
    got_ids = {json.loads(l)["id"] for l in
               OUT.read_text(encoding="utf-8").splitlines() if l.strip()} \
        if OUT.exists() else set()
    todo = [r for r in rows if r["id"] not in got_ids]
    print(f"[go] manifest n={man['n_picked']} sha16={man['ids_sha16']} "
          f"done={len(got_ids)} todo={len(todo)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("a", encoding="utf-8") as f:
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            for v in run_batch(batch):
                v["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                f.write(json.dumps(v, ensure_ascii=False) + "\n")
            f.flush()
            print(f"    batch {i // BATCH + 1}: +{len(batch)} "
                  f"({min(i + BATCH, len(todo))}/{len(todo)})")
    print(f"[go] verdicts → {OUT}")
    return 0


def agree() -> int:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    truth = {}
    for l in SRC.read_text(encoding="utf-8").splitlines():
        if l.strip():
            r = json.loads(l)
            truth[r["id"]] = r.get("truth_label")
    vs = [json.loads(l) for l in
          OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
    n = agree_n = 0
    conf = {"pass": 0, "fail": 0, "insufficient_evidence": 0, "other": 0}
    for v in vs:
        t = truth.get(v["id"])
        if t not in LABELS:
            continue
        n += 1
        g = v.get("verdict")
        conf[g if g in LABELS else "other"] += 1
        if g == t:
            agree_n += 1
    print(f"[agree] n={n}/{man['n_picked']} (manifest sha16={man['ids_sha16']})")
    print(f"  glm vs truth_label 一致率: {agree_n / n:.3f}" if n else
          "  尚无读数(--go 未跑或输出为空)")
    print(f"  glm 三态分布: {json.dumps(conf, ensure_ascii=False)}")
    print("  注:F15 全口径=对判分器 verdict 复判(--judge-log 上线后同名单复用);"
          "当前读数为 glm 腿对 truth 的独立一致率,可作该腿校准参考")
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="冻结名单不调 API")
    p.add_argument("--go", action="store_true", help="实跑(烧 glm 额度)")
    p.add_argument("--agree", action="store_true", help="读数")
    a = p.parse_args()
    if a.dry_run or not any((a.dry_run, a.go, a.agree)):
        man = freeze_manifest()
        print(f"[dry-run] source={man['source']} {man['sampling']} "
              f"sha16={man['ids_sha16']}")
        print(f"  manifest → {MANIFEST}")
        print(f"  额度窗口到即:python tools/f15_glm_leg.py --go")
    if a.go:
        if not MANIFEST.exists():
            freeze_manifest()
        return go()
    if a.agree:
        return agree()
    return 0


if __name__ == "__main__":
    sys.exit(main())
