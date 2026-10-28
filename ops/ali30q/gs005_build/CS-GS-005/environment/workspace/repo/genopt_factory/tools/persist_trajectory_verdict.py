"""Persist a GPT5.5 N=3 trajectory into the fde_verdicts table.

Each trajectory row carries:
  - task_uid          (e.g. genopt_or_jobshop_orlib_v1_001_20260702)
  - verdict_id        (uuid-derived, unique)
  - source            (e.g. 'h800-genopt-runner-<id>' = the registered producer agent_id)
  - overall_pass      (True if valid=1 in trajectory AND difficulty != 'Rejected')
  - score             (best_score from trajectory)
  - items             (per-round metrics + extracted_code, as JSONB)
  - artifacts         (trajectory path + reference path + GPT5.5 prompt previews, as JSONB)

Idempotent: ON CONFLICT (verdict_id) DO NOTHING. Re-running is safe.

Usage:
    python genopt_factory/tools/persist_trajectory_verdict.py \\
        --task-dir genopt_factory/tasks/OR/JobShop/jobshop_orlib_v1_001 \\
        --trajectory gpt55_trajectory.json \\
        --producer-agent-id <int> \\
        --platform-url http://localhost:8000
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid


def _http(method, url, data=None, headers=None, timeout=20):
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", required=True)
    ap.add_argument("--trajectory", required=True,
                    help="path to GPT5.5 N=3 trajectory JSON (relative to task_dir or absolute)")
    ap.add_argument("--producer-agent-id", type=int, required=True)
    ap.add_argument("--platform-url", default=os.environ.get("NAUTILUS_API_URL",
                                                              "http://localhost:8000"))
    ap.add_argument("--api-key", default=os.environ.get("NAUTILUS_AGENT_KEY", ""))
    ap.add_argument("--source", default=None,
                    help="verdict.source 覆盖(默认 h800-genopt-runner-<id> · "
                         "cloud 跑点请传 cloud-genopt-runner-<id> 如实记录)")
    args = ap.parse_args()

    task_dir = os.path.abspath(args.task_dir)
    traj_path = args.trajectory
    if not os.path.isabs(traj_path):
        traj_path = os.path.join(task_dir, traj_path)
    if not os.path.isfile(traj_path):
        print(f"[err] trajectory not found: {traj_path}", file=sys.stderr)
        return 1

    with open(traj_path, encoding="utf-8") as f:
        t = json.load(f)

    start = t.get("seed_score", t.get("start_score"))
    best = t.get("best_score")
    gap = t.get("gap_closed")
    diff = t.get("difficulty") or t.get("difficulty_bucket") or "Rejected"
    valid = any(r.get("metrics", {}).get("valid", 0) > 0
                for r in t.get("rounds", [])) and bool(t.get("seed_valid", 1))
    overall_pass = (valid and diff != "Rejected" and gap is not None and gap > 0.0)

    task_uid = None
    meta_path = os.path.join(task_dir, "frontier_eval", "delivery_metadata.txt")
    if os.path.isfile(meta_path):
        for line in open(meta_path, encoding="utf-8"):
            if line.startswith("task_uid:"):
                task_uid = line.split(":", 1)[1].strip()
                break
    if not task_uid:
        task_uid = "genopt_" + os.path.basename(task_dir.rstrip("/"))

    verdict_id = f"verdict-genopt-{task_uid}-{args.producer_agent_id}-{uuid.uuid4().hex[:8]}"

    items = []
    for r in t.get("rounds", []):
        m = r.get("metrics") or {}
        items.append({
            "round": r.get("round"),
            "score": m.get("combined_score"),
            "valid": m.get("valid"),
            "elapsed_s": r.get("elapsed"),
            "error": m.get("error") or r.get("error"),
            "extracted_code_preview": (r.get("source_preview") or "")[:200],
        })

    artifacts = {
        "trajectory_path": os.path.relpath(traj_path, task_dir),
        "task_dir": os.path.basename(task_dir.rstrip("/")),
        "producer_agent_id": args.producer_agent_id,
        "model": t.get("model"),
        "n_rounds": t.get("n"),
        "reference_path": "reference/solve.py",
    }

    body = {
        "verdict_id": verdict_id,
        "task_uid": task_uid,
        "source": args.source or f"h800-genopt-runner-{args.producer_agent_id}",
        "checklist_uid": None,
        "overall_pass": bool(overall_pass),
        "veto_failed": False,
        "score": float(best) if best is not None else 0.0,
        "items": items,
        "artifacts": artifacts,
        # extra: feed the SSOT break-self-loop channel
        "external_verified": False,  # set True only after soul canonical verify
    }

    args.dry_run = os.environ.get("DRY_RUN") == "1"
    if args.dry_run:
        print("[dry-run] would POST /api/platform/fde/verdict with:")
        print(json.dumps(body, indent=1, ensure_ascii=False)[:1500])
        return 0

    headers = {}
    if args.api_key:
        headers["X-Agent-Key"] = args.api_key
    code, payload = _http("POST", f"{args.platform_url}/api/platform/fde/verdict",
                          data=body, headers=headers)
    if code in (200, 201):
        print(f"[ok] persisted verdict_id={verdict_id}")
        print(f"  task_uid={task_uid}  score={body['score']}  overall_pass={body['overall_pass']}")
    else:
        print(f"[err] persist HTTP {code}: {payload}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())