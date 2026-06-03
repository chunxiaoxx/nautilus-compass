"""Pull cloud-emitted PoI candidates to the local cache so the local reconciler
(which can credit local memory files) can settle them.

  ssh cloud cat <cloud poi_candidates.jsonl>  ->  dedup-merge into local cache
  ->  run ops/poi_reconcile_cron.py (tunnels to DB, MEMORY_ROOT = local memory)

Why local: the cited memory files live on this Windows host (indexed by the
local 9876 BGE daemon via reverse tunnel). cumulative_impact must be written to
those local files for recall boost_top_k to use it · a cloud-side reconciler
can't reach them. So candidates are emitted on cloud, pulled here, settled here.

Idempotent · safe to schedule. NO LLM.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Cloud candidate file · /var/lib/compass/poi is the compass.service ReadWritePath
# (ProtectHome=read-only blocks /home/ubuntu/compass · see patch_v14_recall_poi_candidate).
CLOUD_FILE = os.environ.get(
    "COMPASS_CLOUD_POI_FILE", "/var/lib/compass/poi/poi_candidates.jsonl")
SSH_HOST = os.environ.get("COMPASS_SOUL_SSH_HOST", "cloud")
LOCAL_CACHE = Path(os.environ.get(
    "COMPASS_POI_CACHE_DIR",
    str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache")))
CANDIDATE_NAME = "poi_candidates.jsonl"


def merge_candidate_lines(existing, incoming):
    """Order-preserving union of JSONL lines (existing first), blanks dropped,
    deduped on stripped content."""
    seen = set()
    out = []
    for line in list(existing) + list(incoming):
        s = line.strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def fetch_cloud_lines() -> list:
    """ssh cat the cloud candidate file · returns [] if absent/unreachable."""
    try:
        out = subprocess.run(
            ["ssh", SSH_HOST, f"cat {CLOUD_FILE} 2>/dev/null || true"],
            capture_output=True, text=True, timeout=30)
        return out.stdout.splitlines()
    except Exception as e:
        sys.stderr.write(f"cloud pull failed · {type(e).__name__}: {str(e)[:160]}\n")
        return []


def main() -> int:
    LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
    local_path = LOCAL_CACHE / CANDIDATE_NAME
    existing = local_path.read_text(encoding="utf-8").splitlines() if local_path.exists() else []
    incoming = fetch_cloud_lines()
    merged = merge_candidate_lines(existing, incoming)
    added = len(merged) - len([l for l in existing if l.strip()])
    local_path.write_text("\n".join(merged) + ("\n" if merged else ""), encoding="utf-8")
    print(f"pulled {len(incoming)} cloud lines · +{added} new · total {len(merged)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
