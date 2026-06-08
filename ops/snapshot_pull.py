"""snapshot_pull — T4 GPU daemon pulls the PoI credit snapshot from the CPU server.

Phase 0 Task 3 of the cloud-substrate plan. The authoritative PoI credit table
lives in postgres on the CPU server; `regen_poi_snapshot.sh` (cron) dumps it to
`/var/lib/compass/poi/poi_credit_snapshot.json`. The T4 daemon does NOT talk to
postgres — it reads a local snapshot the v14 boost mtime-reloads. This script
pulls that snapshot down atomically (scp to .tmp, then os.replace) so the boost
never sees a half-written file.

  pull_snapshot(remote_host, remote_path, local_path)   # cron on T4, e.g. every 10min

CLI:
  python snapshot_pull.py --host ubuntu@cpu \
      --remote /var/lib/compass/poi/poi_credit_snapshot.json \
      --local /var/lib/compass/poi/poi_credit_snapshot.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def _default_runner(cmd: list[str]) -> int:
    return subprocess.run(cmd).returncode


def pull_snapshot(remote_host, remote_path, local_path, runner=None) -> int:
    """scp remote snapshot to a .tmp sibling, then atomically replace local_path.

    Returns the scp return code. On failure the existing local_path is untouched.
    """
    runner = runner or _default_runner
    tmp = local_path + ".tmp"
    parent = os.path.dirname(local_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    cmd = ["scp", "-q", f"{remote_host}:{remote_path}", tmp]
    rc = runner(cmd)
    if rc != 0:
        if os.path.exists(tmp):
            os.remove(tmp)
        return rc
    os.replace(tmp, local_path)  # atomic on POSIX & Windows
    return 0


def load_snapshot(local_path) -> dict:
    """Load the snapshot as {memory_key: cumulative_impact}. Missing/invalid -> {}."""
    try:
        with open(local_path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True)
    ap.add_argument("--remote", default="/var/lib/compass/poi/poi_credit_snapshot.json")
    ap.add_argument("--local", default="/var/lib/compass/poi/poi_credit_snapshot.json")
    args = ap.parse_args()
    rc = pull_snapshot(args.host, args.remote, args.local)
    if rc == 0:
        print(f"pulled snapshot: {len(load_snapshot(args.local))} keys -> {args.local}")
    else:
        print(f"snapshot pull failed (rc={rc}); kept existing", file=sys.stderr)
    sys.exit(rc)


if __name__ == "__main__":
    main()
