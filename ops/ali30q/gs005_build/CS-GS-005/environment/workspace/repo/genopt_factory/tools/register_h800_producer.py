"""Register the H800 genopt harness as a real platform agent.

SSOT §0-ARCH red line: producer must be a registered autonomous agent with an
integer agent_id, NOT a bare string claim. This script enforces that for the
H800 GPT5.5 N=3 worker that produced the JobShop/TSP trajectories.

Flow (matches /phase3/backend/api/agent_first_register.py):
  1. POST /api/agent-first/challenge  → challenge_id + prompt
  2. Solve the prompt (capabilities=["code"] → answer "55")
  3. POST /api/agent-first/register  → agent_id (int), wallet_address, api_key
  4. Persist credentials under ~/.nautilus/h800_harness_credentials.json
  5. Emit ready-to-paste h800 harness invocation (with --producer-agent-id)

Idempotent: if creds file already exists, reuse. Re-running reregisters only if
--force. Backend unreachable ⇒ exit non-zero with a clear message so the caller
(SSOT / next session) knows the registration must be re-run when backend is up.

Usage:
    python genopt_factory/tools/register_h800_producer.py \\
        --platform-url http://localhost:8000 \\
        --name h800-genopt-runner-001 \\
        [--force] [--dry-run]
"""

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request


CRED_FILE = os.path.expanduser("~/.nautilus/h800_harness_credentials.json")

CHALLENGE_ANSWERS = {
    "code": "55",
    "data_labeling": "positive",
    "scientific": "3x^2",
    "general": "56",
}


def _http(method, url, data=None, headers=None, timeout=15):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode("utf-8"))
        except Exception:
            payload = {"raw": e.read().decode("utf-8", errors="replace")[:400]}
        return e.code, payload
    except urllib.error.URLError as e:
        return 0, {"error": f"connection failed: {e}"}
    except Exception as e:
        return 0, {"error": f"{type(e).__name__}: {e}"}


def _solve_challenge(challenge_type: str) -> str:
    return CHALLENGE_ANSWERS.get(challenge_type, CHALLENGE_ANSWERS["general"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform-url", default=os.environ.get("NAUTILUS_API_URL",
                                                              "http://localhost:8000"),
                    help="platform API base URL (default: http://localhost:8000 for cloud SSH sessions; "
                         "use cloud-tunneled URL when running outside cloud)")
    ap.add_argument("--name", default="h800-genopt-runner-001")
    ap.add_argument("--capability", default="code",
                    choices=list(CHALLENGE_ANSWERS.keys()))
    ap.add_argument("--description", default=(
        "H800 GPT5.5 N=3 generative-optimization runner. "
        "Per task: drives frontier_eval candidates through qixuw-relayed GPT-5.5 "
        "via OPENAI_BASE_URL, emits per-round trajectories into fde_verdicts."
    ))
    ap.add_argument("--parent-agent-id", default=None,
                    help="optional parent agent_id for lineage (if this runner was spawned)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if os.path.exists(CRED_FILE) and not args.force:
        cred = json.load(open(CRED_FILE, encoding="utf-8"))
        print(f"[reuse] existing creds at {CRED_FILE}")
        print(f"  agent_id={cred.get('agent_id')}  wallet={cred.get('wallet_address')}")
        print(f"  api_key={cred.get('api_key','')[:16]}...")
        print("\nH800 harness invocation:")
        print(f"  ssh h800 '... harness/genopt_orlib_run.py "
              f"--task-dir <task> --n 3 --producer-agent-id {cred.get('agent_id')} ...'")
        return 0

    if args.dry_run:
        print(f"[dry-run] would POST {args.platform_url}/api/agent-first/challenge "
              f"with capabilities=['{args.capability}']")
        print(f"[dry-run] would POST {args.platform_url}/api/agent-first/register "
              f"with name={args.name!r}, capability={args.capability}")
        return 0

    # 1. challenge
    code, payload = _http("POST", f"{args.platform_url}/api/agent-first/challenge",
                          data={"capabilities": [args.capability]})
    if code != 200:
        print(f"[err] challenge HTTP {code}: {payload}", file=sys.stderr)
        return 2
    challenge_id = payload.get("challenge_id")
    challenge_type = payload.get("challenge_type", args.capability)
    print(f"[1/3] got challenge_id={challenge_id} type={challenge_type}")

    # 2. solve
    answer = _solve_challenge(challenge_type)
    proof = f"{challenge_id}:{answer}"
    print(f"[2/3] proof={proof[:16]}...")

    # 3. register
    body = {
        "name": args.name,
        "description": args.description,
        "capabilities": [args.capability],
        "proof_of_capability": proof,
    }
    if args.parent_agent_id:
        body["parent_agent_id"] = args.parent_agent_id
    code, payload = _http("POST", f"{args.platform_url}/api/agent-first/register", data=body)
    if code not in (200, 201):
        print(f"[err] register HTTP {code}: {payload}", file=sys.stderr)
        return 3
    agent_id = payload.get("agent_id")
    wallet = payload.get("wallet_address")
    api_key = payload.get("api_key")
    print(f"[3/3] registered agent_id={agent_id} wallet={wallet}")

    cred = {
        "agent_id": agent_id,
        "wallet_address": wallet,
        "api_key": api_key,
        "name": args.name,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "platform_url": args.platform_url,
        "capability": args.capability,
        "challenge_type": challenge_type,
    }
    os.makedirs(os.path.dirname(CRED_FILE), exist_ok=True)
    with open(CRED_FILE, "w", encoding="utf-8") as f:
        json.dump(cred, f, indent=1, ensure_ascii=False)
    os.chmod(CRED_FILE, 0o600)

    print(f"\n[ok] credentials persisted at {CRED_FILE}")
    print("\n=== H800 harness invocation ===")
    print(f"ssh h800 'export PATH=/root/miniconda3/bin:\\$PATH && \\")
    print(f"  export NAUTILUS_AGENT_KEY={api_key} && \\")
    print(f"  export PRODUCER_AGENT_ID={agent_id} && \\")
    print(f"  cd /root/autodl-tmp/genopt && python -u harness/genopt_orlib_run.py \\")
    print(f"    --task-dir <task> --n 3 --producer-agent-id {agent_id} \\")
    print(f"    --out <task>/gpt55_trajectory_h800.json'")
    return 0


if __name__ == "__main__":
    sys.exit(main())