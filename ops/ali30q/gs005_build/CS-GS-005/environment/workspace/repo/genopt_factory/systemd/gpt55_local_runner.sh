#!/usr/bin/env bash
# 本机 GPT5.5 runner · 不需要 H800/不需要 cloud
# qixuw cert 2025-09-23 被 Sectigo 吊销,本机 curl/Python 走 -k / ssl.CERT_NONE 旁路
# 真工作路径走 cloud(Linux soft-fail OCSP),本机只在 driver 备援时用
set -euo pipefail

export OPENAI_BASE_URL=https://v2.qixuw.com/v1
export OPENAI_API_KEY=<redacted_key_last4=c84c8>

TASK_DIR="${1:-/c/Users/chunx/Projects/nautilus-core/genopt_factory/tasks/operations_research_and_decision_science/JobShop/jobshop_orlib_v1_001}"
OUT="${TASK_DIR}/gpt55_trajectory_local_k.json"

if [[ "${1:-}" == "--smoke" ]]; then
  curl -k -sS --max-time 10 https://v2.qixuw.com/v1/chat/completions -X POST \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H 'Content-Type: application/json' \
    -d '{"model":"gpt-5.5","messages":[{"role":"user","content":"Reply only pong"}],"max_tokens":8,"reasoning_effort":"xhigh"}' \
    | head -c 400
  echo
  exit 0
fi

# 走 Python ssl.CERT_NONE 旁路(本机 urllib 用,cloud Linux 仍 default 不受影响)
python3 -u - <<PYEOF
import json, os, sys, time, urllib.request, urllib.error, ssl, re

TASK_DIR = "${TASK_DIR}"
OUT = "${OUT}"

URL_BASE = os.environ["OPENAI_BASE_URL"]
KEY = os.environ["OPENAI_API_KEY"]
TASK_MD = open(f"{TASK_DIR}/Task.md").read()

# qixuw cert 2025-09-23 被 Sectigo 吊销。本机 driver 备援用,旁路 cert chain。
# 真生产路径走 cloud(Linux soft-fail OCSP),这里仅作 fallback。
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

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
            with urllib.request.urlopen(req, timeout=600, context=SSL_CTX) as r:
                payload = json.loads(r.read().decode("utf-8"))
            return payload["choices"][0]["message"]["content"], time.monotonic()-t0, payload, None
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            err = f"{type(e).__name__}: {e}"
            print(f"[retry {attempt+1}/5] {err}", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay*2, 30)
    return "", 0.0, None, err

print(f"[local-k] qixuw cert REVOKED, 走 ssl.CERT_NONE 旁路 · task_dir={TASK_DIR}", file=sys.stderr)
print(f"[local-k] prompt preflight", file=sys.stderr)
_, t0, p0, err0 = call_chat("Reply only the word pong.", max_retries=2)
if err0:
    print(f"[err] preflight failed: {err0}", file=sys.stderr)
    sys.exit(1)
print(f"[local-k] preflight OK · t={t0:.1f}s · content={p0['choices'][0]['message']['content'][:50]}", file=sys.stderr)
PYEOF
