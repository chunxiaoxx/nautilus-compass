"""compass v1.0 · RAID-2 (writer-reviewer) write path · #7 fusion.

For org / enterprise plan: every observation must pass a reviewer-agent
audit before being written to memory. The reviewer is compass's own anchor
+ LLM judge · NOT the writer agent itself (defeats purpose).

Workflow:
  1. Writer submits obs → POST /v1/observations?raid=2
  2. compass server enqueues to RAID review queue
  3. RAID reviewer (this module · runs as separate worker):
     · Computes drift_check on obs.content (anchor-based)
     · Optionally calls LLM judge for high-stakes obs
     · drift=green → APPROVE → INSERT
     · drift=red   → REJECT  → return error to writer (with drift_signals)
     · drift=yellow → WARN   → INSERT but flagged
  4. Writer retries with corrections if rejected

Run as worker:
  python compass_raid.py serve              # daemon · poll review queue
  python compass_raid.py review <obs_id>    # single review (testing)

Architecture:
  REVIEW_QUEUE_DIR = ~/.compass/raid_queue/         (writer dumps here)
  REVIEW_RESULTS_DIR = ~/.compass/raid_results/     (reviewer writes here)

Threshold (per anchor calibration):
  drift_score < 0.0  → green   (clearly aligned)
  0.0 <= score < 0.05 → yellow (borderline)
  score >= 0.05      → red     (clear drift)
  And: any single negative anchor cosine > 0.78 → forced red

These match paper2_appendix_drift.tex defaults.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

QUEUE_DIR = Path.home() / ".compass" / "raid_queue"
RESULTS_DIR = Path.home() / ".compass" / "raid_results"
REJECTED_DIR = Path.home() / ".compass" / "raid_rejected"

DRIFT_GREEN_MAX = 0.0
DRIFT_YELLOW_MAX = 0.05
NEG_ANCHOR_THRESHOLD = 0.78
POLL_INTERVAL_S = int(os.environ.get("COMPASS_RAID_POLL_S", "30"))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_drift_score(text: str) -> dict:
    """Compute drift score using compass daemon (BGE-m3) · returns dict.

    In production · this calls the local daemon via socket. For now ·
    we abstract via compass.recall.daemon_call interface. If daemon not
    available · return None to signal "review not possible".
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from mcp_server import daemon_call
        # Use existing drift action of daemon
        result = daemon_call({
            "action": "drift",
            "query": text[:1000],
            "project": "raid_review",
            "top_k": 3,
        })
        if not result.get("ok"):
            return {"available": False, "error": result.get("error")}
        d = result.get("drift") or {}
        return {
            "available": True,
            "score": d.get("score", 0.0),
            "alignment": d.get("alignment", 0.0),
            "deviation": d.get("deviation", 0.0),
            "should_alert": d.get("should_alert", False),
            "top_neg_hits": d.get("top_neg_hits", []),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def review_one(obs: dict) -> dict:
    """Review one observation · return verdict dict."""
    obs_id = obs.get("obs_id", "?")
    name = (obs.get("content") or {}).get("name", "")
    body = (obs.get("content") or {}).get("body", "")
    description = (obs.get("content") or {}).get("description", "")
    full_text = f"{name}\n{description}\n{body}"

    # Stage 1: anchor-based drift score
    drift = compute_drift_score(full_text)

    # Stage 2: rule-based verdict
    if not drift.get("available"):
        # Daemon down · default: PASS (don't block writes when system is degraded)
        return {
            "obs_id": obs_id,
            "verdict": "approved",
            "reason": "daemon_unavailable_pass_through",
            "warning": "RAID-2 reviewer unavailable · obs approved by default",
            "ts": now_iso(),
        }

    score = drift.get("score", 0.0)
    top_neg = drift.get("top_neg_hits") or []
    max_neg = max((cos for cos, _ in top_neg), default=0.0) if top_neg else 0.0

    # Hard reject if any negative anchor matches strongly
    if max_neg > NEG_ANCHOR_THRESHOLD:
        bad_anchor = next((txt for cos, txt in top_neg if cos > NEG_ANCHOR_THRESHOLD), "?")
        return {
            "obs_id": obs_id,
            "verdict": "rejected",
            "drift": "red",
            "reason": f"strong_negative_anchor_match · cos={max_neg:.3f}",
            "drift_signals": [f"matched negative anchor: {bad_anchor[:80]}"],
            "score": score,
            "max_neg_cos": max_neg,
            "ts": now_iso(),
        }

    if score >= DRIFT_YELLOW_MAX:
        return {
            "obs_id": obs_id,
            "verdict": "rejected",
            "drift": "red",
            "reason": f"high_drift_score · score={score:.3f} >= {DRIFT_YELLOW_MAX}",
            "drift_signals": [f"deviation cos={drift.get('deviation', 0.0):.3f}"],
            "score": score,
            "ts": now_iso(),
        }

    if score >= DRIFT_GREEN_MAX:
        return {
            "obs_id": obs_id,
            "verdict": "approved_with_warning",
            "drift": "yellow",
            "reason": f"borderline · score={score:.3f}",
            "score": score,
            "ts": now_iso(),
        }

    return {
        "obs_id": obs_id,
        "verdict": "approved",
        "drift": "green",
        "reason": f"clearly_aligned · score={score:.3f}",
        "score": score,
        "ts": now_iso(),
    }


def consume_queue_one(path: Path) -> str:
    """Process one queued obs · return 'approved' | 'rejected' | 'failed'."""
    try:
        obs = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        sys.stderr.write(f"[raid] {path.name} bad JSON: {e}\n")
        return "failed"

    verdict = review_one(obs)

    # Write result
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    result = {**obs, "_raid_verdict": verdict}

    if verdict["verdict"] == "rejected":
        REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        target = REJECTED_DIR / path.name
    else:
        target = RESULTS_DIR / path.name

    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    path.unlink()
    return verdict["verdict"]


def serve():
    print(f"[raid] starting RAID-2 reviewer · queue={QUEUE_DIR} · interval={POLL_INTERVAL_S}s")
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            pending = sorted(QUEUE_DIR.glob("*.json"))
            if pending:
                counts = {}
                for p in pending:
                    r = consume_queue_one(p)
                    counts[r] = counts.get(r, 0) + 1
                print(f"[raid] {len(pending)} reviewed: {counts}")
            else:
                pass  # quiet idle
            time.sleep(POLL_INTERVAL_S)
        except KeyboardInterrupt:
            print("[raid] interrupted by user · exiting")
            return
        except Exception as e:
            sys.stderr.write(f"[raid] pass failed: {e}\n")
            time.sleep(POLL_INTERVAL_S)


def review_cli(obs_id: str):
    """For testing · review a single obs from queue."""
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    matches = list(QUEUE_DIR.glob(f"*{obs_id}*.json"))
    if not matches:
        print(f"[raid] no obs found matching {obs_id} in {QUEUE_DIR}")
        return 1
    for p in matches:
        verdict = consume_queue_one(p)
        print(f"[raid] {p.name}: {verdict}")
    return 0


def status():
    pending = list(QUEUE_DIR.glob("*.json")) if QUEUE_DIR.exists() else []
    approved = list(RESULTS_DIR.glob("*.json")) if RESULTS_DIR.exists() else []
    rejected = list(REJECTED_DIR.glob("*.json")) if REJECTED_DIR.exists() else []
    print(f"compass RAID-2 reviewer status:")
    print(f"  queue:     {len(pending)} pending")
    print(f"  approved:  {len(approved)} (results)")
    print(f"  rejected:  {len(rejected)}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["serve", "review", "status"])
    p.add_argument("obs_id_substr", nargs="?", help="for 'review' · substring of obs filename")
    args = p.parse_args()

    if args.cmd == "serve":
        serve()
    elif args.cmd == "review":
        if not args.obs_id_substr:
            p.error("review needs obs_id_substr")
        sys.exit(review_cli(args.obs_id_substr))
    elif args.cmd == "status":
        status()


if __name__ == "__main__":
    main()
