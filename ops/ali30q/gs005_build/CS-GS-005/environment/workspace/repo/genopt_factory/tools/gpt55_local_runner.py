"""GPT5.5 trajectory runner · eng 基准测试用(本机 driver 备援 / cloud 生产两用)。

TLS:默认 verify=True(cloud/生产路径)。qixuw cert 2025-09-23 被 Sectigo 吊销,
Windows schannel 硬拒 → 仅本机 driver 备援时加 --insecure 旁路 cert chain。

可复现性契约(2026-07-06 第二刀):每轮持久化完整解 source + sha256,best 解
另存 <out>.best_solution.py — soul canonical verify 靠它独立复现分数,
无完整解的轨迹永远过不了 external-verify。

用法:
    # 单测(验证本机可走 GPT5.5)
    python genopt_factory/tools/gpt55_local_runner.py --smoke

    # 跑 JobShop eng 真 trajectory(3 rounds)
    python genopt_factory/tools/gpt55_local_runner.py \
        --task-dir genopt_factory/tasks/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001 \
        --rounds 3 --model gpt-5.5 --out gpt55_local_trajectory.json

    # 跑 doubao fallback
    python genopt_factory/tools/gpt55_local_runner.py \
        --task-dir .../jobshop_orlib_v1_001 --rounds 3 --model doubao-seed-2-0-pro-260215

环境变量(可覆盖):
    OPENAI_BASE_URL = https://v2.qixuw.com/v1
    OPENAI_API_KEY  = sk-c16301d...  (或 ARK_API_KEY if model=doubao)
    OPENAI_BASE_URL_ARK = https://ark.cn-beijing.volces.com/api/v3

不建议生产路径使用 — 真生产走 cloud(Linux 软失败 OCSP)。
本 runner 仅 driver 备援 / 本机 eng PoC。
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

import requests
import urllib3

# 关掉 InsecureRequestWarning(verify=False 必触发)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def chat(url_base, key, model, prompt, max_retries=5, max_tokens=30000, temperature=0.5,
         timeout=600, tls_verify=True):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    # qixuw 支持 reasoning_effort, doubao 不支持(无此字段 server 忽略)
    if model.startswith("gpt-") or model.startswith("o"):
        body["reasoning_effort"] = "xhigh"
    delay = 2
    last_err = None
    for attempt in range(max_retries):
        try:
            t0 = time.monotonic()
            r = requests.post(
                url_base.rstrip("/") + "/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {key}"},
                verify=tls_verify,  # --insecure 时才旁路(qixuw cert REVOKED · 仅本机备援)
                timeout=timeout,
            )
            elapsed = time.monotonic() - t0
            if r.status_code != 200:
                raise RuntimeError(f"http {r.status_code}: {r.text[:200]}")
            payload = r.json()
            choice = (payload.get("choices") or [{}])[0]
            content = (choice.get("message") or {}).get("content")
            if not content:
                # 常见:reasoning 吃光 token(finish=length)或 relay 降级返回空
                raise RuntimeError(
                    f"empty content (finish={choice.get('finish_reason')}, "
                    f"msg_keys={list((choice.get('message') or {}).keys())}, "
                    f"usage={payload.get('usage')})")
            return content, elapsed, payload, None
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            print(f"[retry {attempt+1}/{max_retries}] {last_err}", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 30)
    return "", 0.0, None, last_err


def extract_code(text):
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, flags=re.DOTALL)
    return max(blocks, key=len) if blocks else None


def run_eval(task_dir, code_text):
    """跑 verifier evaluate.py 取 metric(接口 = --benchmark-dir/--candidate · cwd 读 metrics.json)。"""
    eval_py = os.path.join(task_dir, "verification", "evaluate.py")
    if not os.path.isfile(eval_py):
        return {"valid": 0, "error": "evaluate.py not found"}
    baseline = os.path.join(task_dir, "baseline", "init.py")
    # --baseline 只在该 verifier 声明了此参数时传(TSP/BinPack/Attention/QAOA 不认,传了必炸)。
    with open(eval_py, encoding="utf-8") as f:
        accepts_baseline = "--baseline" in f.read()
    with tempfile.TemporaryDirectory(prefix="gpt55_eval_") as td:
        code_path = os.path.join(td, "candidate.py")
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code_text)
        cmd = [sys.executable, eval_py, "--benchmark-dir", task_dir, "--candidate", code_path]
        if accepts_baseline and os.path.isfile(baseline):
            cmd += ["--baseline", baseline]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1200, cwd=td)
        except subprocess.TimeoutExpired:
            return {"valid": 0, "error": "evaluate.py timeout"}
        metrics_path = os.path.join(td, "metrics.json")
        if os.path.isfile(metrics_path):
            with open(metrics_path, encoding="utf-8") as f:
                return json.load(f)
        if result.returncode != 0:
            return {"valid": 0, "error": f"evaluate.py exit {result.returncode}: {result.stderr[:200]}"}
        try:
            return json.loads(result.stdout)
        except Exception:
            return {"valid": 0, "error": f"no metrics.json and stdout not json: {result.stdout[:200]}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", default=None)
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-tokens", type=int, default=30000)
    ap.add_argument("--temperature", type=float, default=0.5)
    ap.add_argument("--smoke", action="store_true", help="单测, 不跑 trajectory")
    ap.add_argument("--insecure", action="store_true",
                    help="verify=False 旁路 TLS(仅本机 driver 备援 · 生产路径禁用)")
    args = ap.parse_args()
    tls_verify = not args.insecure

    # 默认 doubao 走 ARK,其他走 qixuw
    if args.model.startswith("doubao-"):
        url_base = os.environ.get("OPENAI_BASE_URL_ARK", "https://ark.cn-beijing.volces.com/api/v3")
        key = os.environ.get("ARK_API_KEY", "")
    else:
        url_base = os.environ.get("OPENAI_BASE_URL", "https://v2.qixuw.com/v1")
        key = os.environ.get("OPENAI_API_KEY", "")

    if not key:
        print("[err] API key not set in env", file=sys.stderr)
        return 1

    if args.smoke:
        content, elapsed, payload, err = chat(
            url_base, key, args.model, "Reply only the word pong.", max_retries=2,
            max_tokens=8, tls_verify=tls_verify,
        )
        if err:
            print(f"[err] {err}", file=sys.stderr)
            return 1
        print(f"http=200 t={elapsed:.2f}s content={content}")
        print(f"reasoning_tokens={payload.get('usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens')}")
        return 0

    if not args.task_dir or not os.path.isdir(args.task_dir):
        print(f"[err] --task-dir required, got {args.task_dir}", file=sys.stderr)
        return 1

    task_dir = os.path.abspath(args.task_dir)
    task_md = open(os.path.join(task_dir, "Task.md"), encoding="utf-8").read()
    out_path = args.out or os.path.join(task_dir, f"{args.model.replace('-', '_').replace('.', '_')}_local_trajectory.json")

    print(f"[run] model={args.model} rounds={args.rounds} task_dir={task_dir}", file=sys.stderr)
    rounds = []
    best_score = 0.0
    best_code = None
    best_round = None
    # seed = 直接给 baseline/init.py 打分(不信任 task 目录里的历史 metrics.json —
    # 那可能是 reference 解的分)。grounded seed 是 gap_closed 的分母前提。
    baseline_path = os.path.join(task_dir, "baseline", "init.py")
    with open(baseline_path, encoding="utf-8") as f:
        baseline_code = f.read()
    print("[seed] scoring baseline ...", file=sys.stderr)
    seed_metric = run_eval(task_dir, baseline_code)
    seed_valid = 1 if seed_metric.get("valid", 0) else 0
    seed_score = seed_metric.get("combined_score", 0.0)
    best_score = seed_score
    print(f"[seed] score={seed_score} valid={seed_valid}", file=sys.stderr)

    for r in range(1, args.rounds + 1):
        prompt = (
            f"You are an optimization algorithm engineer.\n\n"
            f"# Task\n{task_md}\n\n"
            f"# Baseline score\n{seed_score}\n\n"
            f"# Round {r}/{args.rounds}\n"
            f"Improve over previous best={best_score:.2f}. "
            f"Return your solution as a single Python code block. Be self-contained. "
            f"Rules: pure Python 3 stdlib only; DETERMINISTIC (fix all random seeds, "
            f"no wall-clock-dependent stopping); keep the exact solve interface "
            f"specified in the task."
        )
        content, elapsed, payload, err = chat(
            url_base, key, args.model, prompt,
            max_retries=5, max_tokens=args.max_tokens, temperature=args.temperature,
            tls_verify=tls_verify,
        )
        if err:
            rounds.append({"round": r, "elapsed": elapsed, "metrics": {"valid": 0, "error": err}})
            continue
        code = extract_code(content)
        if not code:
            rounds.append({"round": r, "elapsed": elapsed, "metrics": {"valid": 0, "error": "no code block"}})
            continue
        metric = run_eval(task_dir, code)
        score = metric.get("combined_score", 0.0)
        if metric.get("valid", 0) > 0 and score > best_score:
            best_score = score
            best_code = code
            best_round = r
        rounds.append({
            "round": r,
            "elapsed": elapsed,
            "metrics": metric,
            "source": code,  # 完整解 · 可复现性的根
            "source_sha256": hashlib.sha256(code.encode("utf-8")).hexdigest(),
            "source_preview": code[:300],
            "error": metric.get("error"),
        })
        print(f"  r{r} score={score:.4f} valid={metric.get('valid')} elapsed={elapsed:.1f}s", file=sys.stderr)

    valid_rounds = [r for r in rounds if r.get("metrics", {}).get("valid", 0) > 0]
    # 买方 spec 口径:gap_closed = (best - seed) / 100 · Easy>=0.6(且 best<95)/
    # Medium 0.3-0.6 / Hard 0.1-0.3 / Rejected <0.1。
    gap_closed = max(0.0, (best_score - seed_score) / 100.0)
    if not valid_rounds:
        difficulty = "Rejected"
    elif gap_closed >= 0.6:
        difficulty = "Easy" if best_score < 95 else "Rejected(too easy: best>=95)"
    elif gap_closed >= 0.3:
        difficulty = "Medium"
    elif gap_closed >= 0.1:
        difficulty = "Hard"
    else:
        difficulty = "Rejected"

    # best 解另存独立文件 — soul canonical verify 的复现锚。
    best_sol_path = None
    if best_code is not None:
        best_sol_path = out_path + ".best_solution.py"
        with open(best_sol_path, "w", encoding="utf-8") as f:
            f.write(best_code)

    traj = {
        "model": args.model,
        "n": args.rounds,
        "seed_score": seed_score,
        "best_score": best_score,
        "gap_closed": round(gap_closed, 4),
        "difficulty": difficulty,
        "seed_valid": seed_valid,
        "valid": 1 if valid_rounds else 0,
        "rounds": rounds,
        "best_round": best_round,
        "best_round_source": best_code,  # 完整 · 不截断(可复现性契约)
        "best_solution_file": (os.path.basename(best_sol_path) if best_sol_path else None),
        "best_solution_sha256": (hashlib.sha256(best_code.encode("utf-8")).hexdigest()
                                 if best_code is not None else None),
        "task_dir": os.path.basename(task_dir.rstrip("/")),
        "produced_by": "gpt55_local_runner.py",
        "tls_insecure": bool(args.insecure),
        "cert_workaround": ("requests verify=False (qixuw cert REVOKED 2025-09-23)"
                            if args.insecure else None),
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(traj, f, ensure_ascii=False, indent=2)
    print(f"[ok] wrote {out_path} gap_closed={gap_closed:.4f} difficulty={difficulty}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())