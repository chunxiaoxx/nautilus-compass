#!/usr/bin/env bash
set -euo pipefail
export PATH=/root/miniconda3/bin:$PATH
export OPENAI_BASE_URL=https://v2.qixuw.com/v1
export OPENAI_API_KEY=<redacted_key_last4=c84c8>

cd /root/autodl-tmp/genopt || exit 1

TASK_DIR="/root/autodl-tmp/genopt/factory/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001"
OUT="${TASK_DIR}/gpt55_trajectory_h800_daemon.json"

/root/miniconda3/bin/python -u - <<PYEOF
import json, os, sys, time, urllib.request, urllib.error, re, subprocess, tempfile, shutil

TASK_DIR = "${TASK_DIR}"
OUT = "${OUT}"

URL_BASE = os.environ["OPENAI_BASE_URL"]
KEY = os.environ["OPENAI_API_KEY"]
TASK_MD = open(f"{TASK_DIR}/Task.md").read()

def call_chat(prompt, max_retries=5):
    body = json.dumps({
        "model": "gpt-5.5",
        "messages": [{"role":"user","content":prompt}],
        "max_tokens": 30000,
        "temperature": 0.5,
    }).encode("utf-8")
    delay = 2
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                URL_BASE + "/chat/completions",
                data=body, method="POST",
                headers={"Content-Type":"application/json","Authorization":"Bearer "+KEY},
            )
            t0 = time.monotonic()
            with urllib.request.urlopen(req, timeout=600) as r:
                payload = json.loads(r.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"], time.monotonic()-t0, payload, None
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            err = f"{type(e).__name__}: {e}"
            time.sleep(delay)
            delay = min(delay*2, 30)
    return "", 0.0, None, err

def extract_code(t):
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", t, flags=re.DOTALL)
    return max(blocks, key=len) if blocks else None

def run_verifier(code_or_path, is_path=False):
    """Run the existing evaluate.py with cwd=TASK_DIR so metrics.json lands there."""
    cand = code_or_path if is_path else f"{TASK_DIR}/_tmp_cand.py"
    if not is_path:
        with open(cand, "w") as f: f.write(code_or_path)
    try:
        p = subprocess.run(
            ["/root/miniconda3/bin/python", f"{TASK_DIR}/verification/evaluate.py",
             "--benchmark-dir", TASK_DIR, "--candidate", cand],
            capture_output=True, text=True, timeout=600,
            cwd=TASK_DIR,  # metrics.json lands here
        )
        m_path = f"{TASK_DIR}/metrics.json"
        if os.path.exists(m_path):
            return json.load(open(m_path)), p.stdout[-500:], p.stderr[-500:]
        return None, p.stdout[-500:], p.stderr[-500:]
    finally:
        if not is_path and os.path.exists(cand):
            os.remove(cand)

# Seed
init = open(f"{TASK_DIR}/baseline/init.py").read()
print("[seed] evaluating baseline", flush=True)
seed_metrics, _, _ = run_verifier(init)
seed_score = seed_metrics.get("combined_score", 0) if seed_metrics else 0
print(f"[seed] score={seed_score}", flush=True)

best_code = init
best_score = seed_score
rounds = []

for k in range(1, 4):
    print(f"[round {k}] asking gpt-5.5...", flush=True)
    prompt = (f"Task (Task.md):\n{TASK_MD[:3000]}\n\nCurrent best solve_instance code:\n```python\n{best_code}\n```\n\n"
              f"Latest combined_score={best_score}/100. Optimize. Output ONE ```python``` block.")
    text, dt, payload, err = call_chat(prompt)
    if err:
        rounds.append({"round": k, "error": err, "dt": dt})
        print(f"[round {k}] call failed: {err}", flush=True)
        continue
    code = extract_code(text)
    if not code:
        rounds.append({"round": k, "error": "no_code", "dt": dt})
        print(f"[round {k}] no code", flush=True)
        continue
    metrics, so, se = run_verifier(code)
    if metrics and metrics.get("valid", 0) > 0:
        s = metrics["combined_score"]
        if s > best_score:
            best_score = s
            best_code = code
        rounds.append({"round": k, "score": s, "valid": metrics["valid"], "dt": dt})
        print(f"[round {k}] score={s} elapsed={dt:.1f}s", flush=True)
    else:
        rounds.append({"round": k, "error": "infeasible", "stderr": se[-300:], "dt": dt})
        print(f"[round {k}] infeasible", flush=True)

gap = max(0.0, (best_score - seed_score) / 100.0)
diff = "Easy" if gap >= 0.6 else "Medium" if gap >= 0.3 else "Hard" if gap >= 0.1 else "Rejected"
result = {
    "task_id":"jobshop_orlib_v1_001_daemon","model":"gpt-5.5",
    "seed_score": seed_score, "best_score": best_score, "gap_closed": gap,
    "difficulty_bucket": diff, "n": 3, "rounds": rounds,
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
with open(OUT, "w") as f:
    json.dump(result, f, indent=1, ensure_ascii=False)
print(f"[done] best={best_score} gap={gap} -> {OUT}", flush=True)
PYEOF
