"""N=3 round improvement loop for tiled_matmul PoC.

Per user 7/4 settings.json disclosure:
  model_provider = "OpenAI"
  base_url = "https://v2.qixuw.com"
  wire_api = "responses"          # NOT chat/completions
  model = "gpt-5.5"
  reasoning_effort = "xhigh"
  disable_response_storage = true # sends `x-no-store: true`

Direct connection (no proxy nesting per user 7/4 instruction):
  1. Try Qixuw /v1/responses with x-no-store: true (matches user settings)
  2. If Qixuw unreachable, fall back to MiniMax-M3 direct
  3. Last-resort stub fallback

Run from Computing/KernelEngineering/tiled_matmul_v1_001/.
Set MINIMAX_API_KEY in env (already in ~/.claude/settings.json)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KEY_QIXUW = os.environ.get(
    "OPENAI_API_KEY",
    "sk-c16301d1475dc595011320892cac17cd23d58d92d19a308668bf04b1878c84c8",
)
KEY_MINIMAX = os.environ.get("MINIMAX_API_KEY", "")
QIXUW_BASE = "https://v2.qixuw.com"  # user-provided base_url
QIXUW_WIRE = "responses"             # user-provided wire_api (not chat/completions)
MODEL = "gpt-5.5"                    # user-provided model
REASONING_EFFORT = "xhigh"           # user-provided effort
MINIMAX_BASE = "https://api.minimax.chat/v1/text/chatcompletion_v2"
MODEL_MINIMAX = "MiniMax-M3"
ROOT = Path(__file__).resolve().parent
TASK_MD = (ROOT / "Task.md").read_text(encoding="utf-8")
INSTANCES = json.loads((ROOT / "data" / "instances.json").read_text(encoding="utf-8"))


def _post_json(url: str, body: dict, headers: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def call_qixuw_gpt55(prompt: str, timeout: int = 180) -> str:
    """Hit qixuw /v1/responses per user-provided wire_api setting.

    Headers include x-no-store: true (disable_response_storage).
    """
    base = QIXUW_BASE.rstrip("/")
    path = f"/{QIXUW_WIRE}"
    url = base + path
    data = _post_json(
        url,
        {
            "model": MODEL,
            "input": prompt,
            "reasoning_effort": REASONING_EFFORT,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY_QIXUW}",
            "x-no-store": "true",
        },
        timeout,
    )
    # /v1/responses schema: output array with content[].text
    if "output" in data and data["output"]:
        out = data["output"]
        if isinstance(out, list):
            for item in out:
                if item.get("type") == "message":
                    for c in item.get("content", []):
                        if c.get("type") == "output_text":
                            return c.get("text", "")
        elif isinstance(out, dict):
            return out.get("text", "") or out.get("content", "")
    # Fallback: scan for any text field
    if "text" in data:
        return data["text"]
    if "output_text" in data:
        return data["output_text"]
    return json.dumps(data)


def call_minimax_m3(prompt: str, timeout: int = 180) -> str:
    data = _post_json(
        MINIMAX_BASE,
        {
            "model": MODEL_MINIMAX,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4000,
            "temperature": 0.2,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY_MINIMAX}",
        },
        timeout,
    )
    return data["choices"][0]["message"]["content"]


def call_gpt55(prompt: str, timeout: int = 180) -> tuple[str, str]:
    """Returns (content, source_label). source_label in {qixuw, minimax}."""
    try:
        return call_qixuw_gpt55(prompt, timeout), "qixuw"
    except Exception as e:
        print(f"[qixuw {QIXUW_BASE}/{QIXUW_WIRE} failed: {type(e).__name__}: {str(e)[:200]}; falling back to minimax-m3]")
    return call_minimax_m3(prompt, timeout), "minimax-m3"


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

CRITICAL: the function MUST be named exactly `def matmul(A, B)`. Do NOT rename to matmul_blocked / matmul_tiled / multiply. The verifier imports `candidate.matmul` by exact name. If you write a helper, also add at the end of your code: `matmul = <your_function_name>` so the verifier finds it.
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

Return ONLY a python code block. Function name MUST be exactly `def matmul(A, B)`.
"""
    else:
        base += """
Provide a Python implementation of `def matmul(A, B)` using block tiling. Return ONLY a python code block. Function name MUST be exactly `matmul`.
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
        response = ""
        source = "none"
        try:
            response, source = call_gpt55(prompt, timeout=180)
        except Exception as e:
            print(f"[round {k}] all providers failed: {e}")
            response = FALLBACK_CODE
            source = "fallback-stub"
        code = extract_code(response)
        # Sanity: must define `def matmul(`. If not, attempt to add `matmul = <first def>`
        if "def matmul(" not in code:
            # Heuristic: find first `def <name>(A, B)` and add `matmul = <name>` alias
            import re
            m = re.search(r"^def\s+(\w+)\s*\(\s*A\s*,\s*B\b", code, re.M)
            if m and m.group(1) != "matmul":
                code = code + f"\nmatmul = {m.group(1)}\n"
                print(f"[round {k}] {source}: aliased {m.group(1)} -> matmul")
            else:
                print(f"[round {k}] {source}: response lacks `def matmul(` and no alias found, using baseline (no overwrite)")
                eval_res = evaluate_candidate(
                    (ROOT / "baseline" / "init.py").read_text(encoding="utf-8"),
                    f"r{k}",
                )
                score = eval_res["metrics"].get("combined_score", 0.0)
                trajectory["rounds"].append({
                    "round": k,
                    "kind": source + "-no-matmul",
                    "score": score,
                    "model_response_tail": response[-300:],
                    "metrics": eval_res["metrics"],
                })
                print(f"[round {k}] {source}-no-matmul score={score:.4f}")
                if score > trajectory["best_score"]:
                    trajectory["best_score"] = score
                    trajectory["best_round"] = k
                    prev = {"score": score}
                continue
        eval_res = evaluate_candidate(code, f"r{k}")
        score = eval_res["metrics"].get("combined_score", 0.0)
        trajectory["rounds"].append({
            "round": k,
            "kind": source,
            "score": score,
            "model_response_tail": response[-300:],
            "metrics": eval_res["metrics"],
        })
        print(f"[round {k}] {source} score={score:.4f}")
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
