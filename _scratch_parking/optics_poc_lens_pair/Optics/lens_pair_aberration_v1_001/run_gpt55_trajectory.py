"""Run GPT-5.5 N=3 round improvement loop · deterministically request
better lens-pair placements, evaluate after each round, persist trajectory."""

from __future__ import annotations

import json
import ssl
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

KEY = "sk-c16301d1475dc595011320892cac17cd23d58d92d19a308668bf04b1878c84c8"
BASE = "https://v2.qixuw.com"
MODEL = "gpt-5.5"
ROOT = Path(__file__).resolve().parent
TASK_MD = (ROOT / "Task.md").read_text(encoding="utf-8")
INSTANCES = json.loads((ROOT / "data" / "instances.json").read_text(encoding="utf-8"))

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def call_gpt55(prompt: str, timeout: int = 120) -> str:
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
            "Authorization": f"Bearer {KEY}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        data = json.loads(r.read())
    return data["choices"][0]["message"]["content"]


def extract_code(text: str) -> str:
    """Extract python code block from GPT-5.5 response."""
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
    """Write code to candidate file and run evaluate.py."""
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
            "code": code,
            "stdout_tail": out[-400:],
            "stderr_tail": err[-400:],
            "metrics": metrics,
        }
    finally:
        cand_path.write_text(backup, encoding="utf-8")


def build_prompt(round_idx: int, instance_summary: str, prev: dict = None) -> str:
    base = f"""You are optimizing an Optical Bench Alignment problem (lens pair).
Task spec:
{TASK_MD}

Instances summary:
{instance_summary}

Goal: minimize RMS spot radius on target plane (lower is better).
Scoring: _score = min(100, 100 * 1.0 / achieved_rms)  → bring achieved_rms down toward 1.0 mm oracle bound.
"""
    if prev:
        base += f"""
Previous best score: {prev['score']:.4f} with achieved_rms values per instance.

Improve over previous version. Iterate on placement strategy:
- Use thin-lens conjugate plus explicit compensation for off-axis rays
- Tilt-induced decentering may help
- Treat each instance as a different physical setup; can adopt per-instance logic via parameters
Return ONLY a python code block (markdown ```python) containing align_lens_pair.
"""
    else:
        base += """
First baseline: provide a Python implementation of align_lens_pair.
Return ONLY python code block.
"""
    return base


def summarize_instances() -> str:
    return json.dumps(INSTANCES, indent=2)


def main():
    trajectory = {
        "task_id": "lens_pair_aberration_v1_001",
        "model": MODEL,
        "rounds": [],
        "best_score": 0.0,
        "best_round": None,
    }

    instance_summary = summarize_instances()
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

    prev = {"score": init_score, "label": "init"}
    for k in range(1, 4):
        prompt = build_prompt(k, instance_summary, prev)
        try:
            response = call_gpt55(prompt, timeout=180)
        except Exception as e:
            print(f"[round {k}] GPT-5.5 call failed: {e}")
            response = "def align_lens_pair(source, lens_a, lens_b, target_z, n_rays=64):\n    return {'z_a':0.0,'z_b':lens_b['f']+1e-3,'x_a':0.0,'x_b':0.0,'y_a':0.0,'y_b':0.0}\n"
        code = extract_code(response)
        eval_res = evaluate_candidate(code, f"r{k}")
        score = eval_res["metrics"].get("combined_score", 0.0)
        trajectory["rounds"].append({
            "round": k,
            "kind": "gpt55",
            "score": score,
            "model_response_tail": response[-400:],
            "metrics": eval_res["metrics"],
        })
        print(f"[round {k}] gpt55 score={score:.4f}")
        if score > trajectory["best_score"]:
            trajectory["best_score"] = score
            trajectory["best_round"] = k
            prev = {"score": score, "label": f"r{k}"}
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
