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
from pathlib import Path

KEY_QIXUW = os.environ.get("OPENAI_API_KEY", "")  # 必须经 env 传入 · 不硬编码(空则回退 MiniMax/stub)
KEY_MINIMAX = os.environ.get("MINIMAX_API_KEY", "")
QIXUW_BASE = "https://v2.qixuw.com"  # user-provided base_url
QIXUW_WIRE = "chat/completions"     # 7/5 cloud probe confirmed: /v1/responses returns 502, /v1/chat/completions is the live endpoint
MODEL = "gpt-5.5"                    # user-provided model
REASONING_EFFORT = "xhigh"           # user-provided effort
MINIMAX_BASE = "https://api.minimax.chat/v1/text/chatcompletion_v2"
MODEL_MINIMAX = "MiniMax-M3"
ROOT = Path(__file__).resolve().parent
TASK_MD = (ROOT / "Task.md").read_text(encoding="utf-8")
INSTANCES = json.loads((ROOT / "data" / "instances.json").read_text(encoding="utf-8"))


def _post_json(url: str, body: dict, headers: dict, timeout: int = 60) -> dict:
    # 7/5 fix: use requests library (certifi bundle bundled automatically) to
    # bypass Windows CRYPTO_E_REVOKED on qixuw chain. certifi ships fresh
    # Sectigo R46 root; urllib's ssl.create_default_context pulls from Windows
    # cert pool which retains revoked Comodo AAA root → handshake fails.
    import requests
    r = requests.post(url, headers=headers, json=body, timeout=timeout)
    r.raise_for_status()
    return r.json()


def call_qixuw_gpt55(prompt: str, timeout: int = 180) -> str:
    """Hit qixuw /v1/chat/completions + reasoning_effort=xhigh.

    7/5 cloud SSH probe confirmed: /v1/responses returns 502; chat/completions is the
    live endpoint. x-no-store: true is forwarded (disable_response_storage=true).
    """
    base = QIXUW_BASE.rstrip("/")
    path = f"/{QIXUW_WIRE}"
    url = base + path
    data = _post_json(
        url,
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "reasoning_effort": REASONING_EFFORT,
            "max_tokens": 4000,
        },
        {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {KEY_QIXUW}",
            "x-no-store": "true",
        },
        timeout,
    )
    # /v1/chat/completions schema: choices[0].message.content
    if "choices" in data and data["choices"]:
        choice = data["choices"][0]
        msg = choice.get("message", {})
        content = msg.get("content", "")
        if content:
            return content
    # Fallback: scan for any text field
    if "text" in data:
        return data["text"]
    if "content" in data and isinstance(data["content"], str):
        return data["content"]
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
    # MiniMax-M3 (the model running this session, per user 7/4 disclosure)
    # returns empty content for verbose/long prompts; keep this ULTRA short.
    # ~200 chars max so the model reliably returns code.
    base = "Write Python: def matmul(A, B) returning {\"C\": [[float]], \"elapsed_s\": float}. Pure stdlib, beats naive triple-loop. Function name MUST be exactly `matmul`. Return ONLY a python code block."
    if prev:
        base += f" Previous score {prev['score']:.2f}; improve with block tiling or ikj reorder."
    return base


def main():
    trajectory = {
        "task_id": "tiled_matmul_v1_001",
        "model": MODEL,
        # B9 fix: honest metadata (was: "model": "gpt-5.5 | minimax-m3 (fallback)" string)
        "provider_chain": ["qixuw", "minimax-m3"],
        "provider_status": {
            "qixuw": {
                "base_url": QIXUW_BASE,
                "wire_api": QIXUW_WIRE,
                "status": "unreachable (HTTP 502 Upstream access forbidden — provider dead, out of compass tur per commit 0042245 RED test 2026-07-04T11:15)",
            },
            "minimax-m3": {
                "base_url": MINIMAX_BASE,
                "status": "live; returns empty content for prompts >1KB (per direct probe 2026-07-04)",
            },
        },
        "valid_gpt55_run": False,  # 0/3 rounds actually ran on qixuw GPT-5.5
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
                print(f"[round {k}] {source}: response lacks `def matmul(`; using init_score (no overwrite, no re-eval)")
                # B6 fix: no-matmul baseline must use init_score directly, not re-evaluate
                # (re-evaluate introduces elapsed_s noise that fakes improvement)
                score = init_score
                trajectory["rounds"].append({
                    "round": k,
                    "kind": source + "-no-matmul",
                    "score": score,
                    "model_response_tail": response[-300:] or "(empty response)",
                    "metrics": {},  # empty = honest (no real evaluation happened)
                })
                print(f"[round {k}] {source}-no-matmul score={score:.4f} (=init, honest)")
                # NOTE: do NOT update best_score from no-matmul round (would shadow real model round)
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

    # B5 fix: gap_closed ratio uses init_score as denominator (combined_score ~2 is not 0-100 scale)
    trajectory["gap_closed"] = (trajectory["best_score"] - init_score) / max(init_score, 0.1)
    trajectory["difficulty"] = (
        "Easy" if trajectory["gap_closed"] >= 0.5 else
        "Medium" if trajectory["gap_closed"] >= 0.2 else
        "Hard" if trajectory["gap_closed"] >= 0.1 else "Rejected"
    )

    out = ROOT / "gpt55_trajectory.json"
    out.write_text(json.dumps(trajectory, indent=2), encoding="utf-8")
    print(f"\nbest_score={trajectory['best_score']:.4f} at round {trajectory['best_round']}")
    print(f"gap_closed={trajectory['gap_closed']:.4f} → difficulty={trajectory['difficulty']}")


if __name__ == "__main__":
    main()
