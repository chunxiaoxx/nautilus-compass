#!/usr/bin/env python3
"""S-诊断 runner — p13 pass@k true_wall sprint(6/18·platform-soul turf）。

净新 orchestration（PoC `_tmp_patch/sdiag_poc.py` 的正式化·KernelBench 专用):
  1. 读官方构造的 p13 题面 prompt.txt（喂 doubao 的完整题面·含 ModelNew 指令）。
  2. doubao-seed-2.0-pro temp=1.0 采样 k 个候选 kernel（从 ```python 块抽）。
  3. 每候选 scp 到 GPU T4 box → kb_eval.sh（flock 互斥·guarded eval）→ result JSON。
  4. 聚合成 triage 契约 {n_samples,n_passed,n_correct_but_gated} → services.fde_triage 定桶。

判据（死口径·6/17 锁·compass ack）:
  true_wall（蒸馏候选）= pass@k correctness 通过数==0 且无洗门（n_passed==0 and n_correct_but_gated==0）。
  🔴 KernelBench 门方向：G2 = speedup >2× **快** 触发 suspect cap（反作弊），不是慢。
     correctness 过但被 G2 门拒 = n_correct_but_gated（洗门·非真墙）。

纯逻辑（extract_code/summarize_candidate_results）单测覆盖；网络+ssh 编排走 CLI 真跑。

用法（先 pilot 证管线再放 50·background 跑别前台 poll）:
  python -m services.fde_sdiagnose_run --level 2 --problem-id 13 --k 10 --out p13_pilot.json
env: ARK_API_KEY（本地 ~/.claude/.cache/.fde_api_secrets.env）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

# services.fde_triage 在同包；脚本直跑时补 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.fde_triage import classify_task  # noqa: E402

ARK_BASE = "https://ark.cn-beijing.volces.com/api/plan/v3"
BAILIAN_BASE_DEFAULT = "https://dashscope.aliyuncs.com/compatible-mode/v1"
GPU_HOST = "ubuntu@43.166.8.20"  # T4 box（🔴 非 .46）
GPU_PEM = "/tmp/gpu.pem"
GPU_REMOTE_DIR = "/mnt/datadisk0/fde_t3_harness/kb_selftest/sdiag"
KB_EVAL_SH = "/mnt/datadisk0/fde_t3_harness/kb_eval.sh"
# 🔴 T4 三方共用·compass daemon 常驻占 ~12 GiB → 大题型(p13 等）perf profiling 边界 OOM。
# expandable_segments 复用 PyTorch reserved-but-unallocated 碎片，实测把 p13 从 OOM 救回 pass。
KB_EVAL_ENV = "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"


# ───────────────────────── 纯逻辑（单测覆盖）─────────────────────────

_CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_code(text: str) -> str:
    """抽 doubao 输出里的 python 代码块。多块时优先含 ModelNew 的（常先示例后答案）。"""
    blocks = _CODE_BLOCK.findall(text)
    if not blocks:
        return text
    for b in blocks:
        if "ModelNew" in b:
            return b
    return blocks[-1]


def classify_candidate(r: dict) -> str:
    """单候选 kb_eval 结果 → passed / correct_but_gated / correctness_fail。

    对齐 GPU box triage_aggregate.classify_candidate（死口径）。
    """
    if r.get("pass_final") is True:
        return "passed"
    if r.get("pass_correct_raw") is True:  # G2 >2× suspect cap：correctness 过被门拒=洗门
        return "correct_but_gated"
    return "correctness_fail"


def summarize_candidate_results(results: list[dict]) -> dict:
    """聚合 per-candidate kb_eval 结果 → triage 契约 + 诚实计错。

    带 "error" 键（ark/eval 崩溃·没产出验证结果）的样本不计入分母（n_samples），
    只记 n_errored。诚实：pass@k 只统计真正跑出验证结论的样本。
    """
    counts = {"passed": 0, "correct_but_gated": 0, "correctness_fail": 0}
    n_errored = 0
    for r in results:
        if r.get("error"):
            n_errored += 1
            continue
        counts[classify_candidate(r)] += 1
    n_samples = sum(counts.values())
    return {
        "n_samples": n_samples,
        "n_passed": counts["passed"],
        "n_correct_but_gated": counts["correct_but_gated"],
        "n_correctness_fail": counts["correctness_fail"],
        "n_errored": n_errored,
    }


def parse_kb_eval_json(stdout: str) -> dict:
    """kb_eval 输出单个 pretty-print JSON → 取首 { 到末 }（🔴 别 splitlines[-1]）。"""
    s, e = stdout.find("{"), stdout.rfind("}")
    if s < 0 or e <= s:
        return {"error": "no_json", "raw_tail": stdout[-200:]}
    try:
        return json.loads(stdout[s:e + 1])
    except json.JSONDecodeError as ex:
        return {"error": "json_decode: %s" % ex, "raw_tail": stdout[-200:]}


# ───────────────────────── 集成（doubao + GPU ssh）─────────────────────────

def load_secrets() -> None:
    """加载本地密钥到 env（ARK + BAILIAN·已存在的不覆盖）。"""
    p = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if "=" not in line or line.startswith("#"):
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        if k in ("ARK_API_KEY", "BAILIAN_API_KEY", "BAILIAN_OPENAI_BASE",
                 "DASHSCOPE_API_KEY") and not os.environ.get(k):
            os.environ[k] = v.strip().strip('"').strip("'")


def load_ark_key() -> None:  # 兼容旧调用
    load_secrets()


def ark_complete(prompt: str, model="doubao-seed-2.0-pro", temp=1.0,
                 max_tokens=8000, timeout=240, retries=4) -> str:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": temp, "max_tokens": max_tokens}).encode("utf-8")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                ARK_BASE + "/chat/completions", data=body, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + os.environ["ARK_API_KEY"]})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"]
        except (urllib.error.URLError, ConnectionError, TimeoutError, json.JSONDecodeError) as ex:
            last = ex
            code = getattr(ex, "code", None)
            if code is not None and 400 <= code < 500 and code != 429:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("ark failed: %s" % last)


def bailian_complete(prompt: str, model="deepseek-v4-pro", temp=1.0,
                     max_tokens=24000, timeout=600, retries=4) -> str:
    """阿里云百炼 OpenAI 兼容 completer（强模型先解·S-分拣）。env: BAILIAN_API_KEY。"""
    base = os.environ.get("BAILIAN_OPENAI_BASE", BAILIAN_BASE_DEFAULT)
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": temp, "max_tokens": max_tokens}).encode("utf-8")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                base.rstrip("/") + "/chat/completions", data=body, method="POST",
                headers={"Content-Type": "application/json",
                         "Authorization": "Bearer " + os.environ["BAILIAN_API_KEY"]})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())["choices"][0]["message"]["content"]
        except (urllib.error.URLError, ConnectionError, TimeoutError, json.JSONDecodeError) as ex:
            last = ex
            code = getattr(ex, "code", None)
            if code is not None and 400 <= code < 500 and code != 429:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("bailian failed: %s" % last)


def get_completer(provider: str, model: str):
    """provider → (completer_fn, model)。纯派发。"""
    if provider == "ark":
        return (lambda p: ark_complete(p, model=model)), model
    if provider == "bailian":
        return (lambda p: bailian_complete(p, model=model)), model
    raise ValueError("unknown provider: %s" % provider)


def _ssh(*args, timeout=600):
    base = ["ssh", "-i", GPU_PEM, "-o", "ConnectTimeout=20",
            "-o", "StrictHostKeyChecking=no", GPU_HOST]
    return subprocess.run(base + list(args), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def gpu_eval_candidate(code: str, idx: int, level: int, problem_id: int) -> dict:
    """候选 scp 到 GPU → kb_eval.sh（flock 串行）→ 解析 stdout JSON。"""
    remote = "%s/cand_p%d_%d.py" % (GPU_REMOTE_DIR, problem_id, idx)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code)
        local = f.name
    try:
        _ssh("mkdir", "-p", GPU_REMOTE_DIR, timeout=60)
        scp = subprocess.run(
            ["scp", "-i", GPU_PEM, "-o", "ConnectTimeout=20", "-o", "StrictHostKeyChecking=no",
             local, "%s:%s" % (GPU_HOST, remote)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if scp.returncode != 0:
            return {"error": "scp_fail: %s" % scp.stderr[-200:]}
        # kb_eval.sh <level> <problem_id> <candidate.py>  → flock + guarded eval，stdout=单JSON
        # env 前缀注入 expandable_segments（共享 T4 内存紧张·防边界 OOM）
        r = _ssh("env", KB_EVAL_ENV, "bash", KB_EVAL_SH,
                 str(level), str(problem_id), remote, timeout=900)
        if not r.stdout.strip():
            return {"error": "kb_eval_empty: rc=%d %s" % (r.returncode, r.stderr[-200:])}
        return parse_kb_eval_json(r.stdout)
    except subprocess.TimeoutExpired:
        return {"error": "gpu_eval_timeout"}
    finally:
        try:
            os.unlink(local)
        except OSError:
            pass


def run(level: int, problem_id: int, k: int, prompt_path: str, out_path: str | None,
        provider: str = "ark", model: str = "doubao-seed-2.0-pro") -> dict:
    load_secrets()
    completer, model = get_completer(provider, model)
    prompt = open(prompt_path, encoding="utf-8").read()
    task_uid = "kb_l%d_p%d" % (level, problem_id)

    print("[sdiag] task=%s k=%d provider=%s model=%s temp=1.0 gpu=%s"
          % (task_uid, k, provider, model, GPU_HOST), flush=True)
    results = []
    for i in range(k):
        t0 = time.time()
        try:
            resp = completer(prompt)
            code = extract_code(resp)
        except Exception as ex:  # noqa: BLE001 — 采样失败诚实计错·不中断批次
            results.append({"error": "ark_error: %s" % ex})
            print("  [%d/%d] ark_error %s" % (i + 1, k, str(ex)[:80]), flush=True)
            continue
        res = gpu_eval_candidate(code, i, level, problem_id)
        results.append(res)
        cls = res.get("error") or classify_candidate(res)
        reason = res.get("reason", "")
        print("  [%d/%d] %s | %s | %.0fs"
              % (i + 1, k, cls, str(reason)[:70], time.time() - t0), flush=True)

    summ = summarize_candidate_results(results)
    verdict = classify_task({"task_uid": task_uid, **summ})
    report = {
        "task_uid": task_uid, "level": level, "problem_id": problem_id, "k": k,
        "provider": provider, "model": model,
        "summary": summ, "verdict": verdict, "raw_results": results,
    }
    print("\n=== S-诊断结果 p%d ===" % problem_id, flush=True)
    print("samples=%d passed=%d correct_but_gated=%d correctness_fail=%d errored=%d"
          % (summ["n_samples"], summ["n_passed"], summ["n_correct_but_gated"],
             summ["n_correctness_fail"], summ["n_errored"]), flush=True)
    print("桶: %s · 蒸馏候选=%s · %s"
          % (verdict["bucket"], verdict["distill_candidate"], verdict["reason"]), flush=True)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print("[sdiag] 写 %s" % out_path, flush=True)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", type=int, default=2)
    ap.add_argument("--problem-id", type=int, default=13)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--prompt", default=os.path.expanduser(
        "~/fde_t3_scratch/kernelbench/_sdiag/p13/prompt.txt"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--provider", default="ark", choices=["ark", "bailian"])
    ap.add_argument("--model", default="doubao-seed-2.0-pro")
    a = ap.parse_args()
    run(a.level, a.problem_id, a.k, a.prompt, a.out, a.provider, a.model)


if __name__ == "__main__":
    main()
