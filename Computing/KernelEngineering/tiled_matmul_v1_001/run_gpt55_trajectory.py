"""GPT-5.5 N=3 round improvement loop for tiled_matmul PoC.

Run from Computing/KernelEngineering/tiled_matmul_v1_001/."""

from __future__ import annotations

import json
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

KEY = ""  # local CC Switch injects
BASE = "http://127.0.0.1:52999"  # CC Switch local proxy (matches agent dialog path)
MODEL = "gpt-5.5"
ROOT = Path(__file__).resolve().parent
TASK_MD = (ROOT / "Task.md").read_text(encoding="utf-8")
INSTANCES = json.loads((ROOT / "data" / "instances.json").read_text(encoding="utf-8"))


def call_gpt55(prompt: str, timeout: int = 180) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "reasoning_effort": "low",
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        BASE + "/v1/chat/completions",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": "PROXY_MANAGED",
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"]


def extract_code(text: str) -> str:
    if "```python" in text:
        start = text.index("```python") + len("```python")
        end = text.index("```", start)
        return text[start:end].strip()
    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return text[start:end].strip()
    return text.strip()


def evaluate_candidate(code: str, label: str) -> dict:
    cand_path = ROOT / "baseline" / "init.py"
    backup = cand_path.read_text(encoding="utf-8")
    try:
        cand_path.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "verification" / "evaluate.py"),
                "--candidate",
                str(cand_path),
                "--out",
                str(ROOT / f"metrics_{label}.json"),
            ],
            capture_output=True,
            text=True,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        try:
            metrics = json.loads((ROOT / f"metrics_{label}.json").read_text(encoding="utf-8"))
        except Exception:
            metrics = {"combined_score": 0.0, "valid": 0, "error": err[:300]}
        return {
            "stdout_tail": out[-300:],
            "stderr_tail": err[-300:],
            "metrics": metrics,
        }
    finally:
        cand_path.write_text(backup, encoding="utf-8")


FALLBACK_CODE = """import time
def matmul(A, B):
    M, K = len(A), len(A[0])
    N = len(B[0])
    t0 = time.perf_counter()
    C = [[0.0] * N for _ in range(M)]
    for i in range(M):
        for k in range(K):
            aik = A[i][k]
            Bk = B[k]
            for j in range(N):
                C[i][j] += aik * Bk[j]
    return {"C": C, "elapsed_s": time.perf_counter() - t0}
"""


def build_prompt(round_idx: int, prev: dict = None) -> str:
    base = f"""You are optimizing Tiled Matrix Multiplication in pure Python stdlib.

Task spec:
{TASK_MD}

Instances:
{json.dumps(INSTANCES, indent=2)}

Scoring: _score = min(100, 100 * achieved_gflops / 1.5).  Baseline ~0.024 GFLOPS → score ~1.6.

Constraints: pure stdlib only. matmul(A, B) -> {{"C": [[float]], "elapsed_s": float}}. M=len(A), N=len(B[0]). Numerically equivalent within 1e-3 vs naive reference.
"""
    if prev:
        base += f"""
Previous round score: {prev['score']:.4f}

Improve over previous version. Strategies to try:
- block tiling (32x32 blocks for cache locality)
- register-blocked innermost loop
- pre-flattened lists to avoid attribute lookups
- ikj loop reorder (cache-friendly vs naive ijk)
- micro-opts like local-variable hoisting

Return ONLY a python code block containing matmul.
"""
    else:
        base += """
Provide a Python implementation of matmul using block tiling. Return ONLY python code block.
"""
    return base


def main():
    trajectory = {
        "task_id": "tiled_matmul_v1_001",
        "model": MODEL,
        "rounds": [],
        "best_score": 0.0,
        "best_round": None,
    }

    init_eval = evaluate_candidate(
        (ROOT / "baseline" / "init.py").read_text(encoding="utf-8"), "init"
    )
    init_score = init_eval["metrics"].get("combined_score", 0.0)
    trajectory["rounds"].append({
        "round": 0,
        "kind": "baseline",
        "score": init_score,
        "metrics": init_eval["metrics"],
    })
    print(f"[round 0 baseline] score={init_score:.4f}")

    prev = {"score": init_score}
    for k in range(1, 4):
        prompt = build_prompt(k, prev)
        try:
            response = call_gpt55(prompt, timeout=180)
        except Exception as e:
            print(f"[round {k}] GPT-5.5 call failed: {e}")
            response = FALLBACK_CODE
        code = extract_code(response)
        eval_res = evaluate_candidate(code, f"r{k}")
        score = eval_res["metrics"].get("combined_score", 0.0)
        trajectory["rounds"].append({
            "round": k,
            "kind": "gpt55",
            "score": score,
            "model_response_tail": response[-300:],
            "metrics": eval_res["metrics"],
        })
        print(f"[round {k}] gpt55 score={score:.4f}")
        if score > trajectory["best_score"]:
            trajectory["best_score"] = score
            trajectory["best_round"] = k
            prev = {"score": score}
        time.sleep(1)

    trajectory["gap_closed"] = (trajectory["best_score"] - init_score) / 100.0
    trajectory["difficulty"] = (
        "Easy" if trajectory["gap_closed"] >= 0.6 else
        "Medium" if trajectory["gap_closed"] >= 0.3 else
        "Hard" if trajectory["gap_closed"] >= 0.1 else "Rejected"
    )

    out = ROOT / "gpt55_trajectory.json"
    out.write_text(json.dumps(trajectory, indent=2), encoding="utf-8")
    print(f"\nbest_score={trajectory['best_score']:.4f} at round {trajectory['best_round']}")
    print(f"gap_closed={trajectory['gap_closed']:.4f} → difficulty={trajectory['difficulty']}")


if __name__ == "__main__":
    main()
