---
name: orgfuel-ORGG-bd1a184167d7debc-73e9a0e131
description: "判读档判例 2026-06-03-p5-v14-poi-emission · Task 5: Pull I/O + re"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-bd1a184167d7debc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission · Task 5: Pull I/O + reconcile runner + Windows scheduled task
## Task 5: Pull I/O + reconcile runner + Windows scheduled task

**Files:**
- Modify: `ops/pull_cloud_candidates.py` (add `fetch_cloud_lines` + `main`)
- Create: `C:/Users/chunx/.cache/compass/run-poi-reconcile.cmd` (wrapper)

**Step 1: Add I/O + main to `ops/pull_cloud_candidates.py`**

```python
def fetch_cloud_lines() -> list:
    """ssh cat the cloud candidate file · returns [] if absent/unreachable."""
    try:
        out = subprocess.run(
            ["ssh", SSH_HOST, f"cat {CLOUD_FILE} 2>/dev/null || true"],
            capture_output=True, text=True, timeout=30)
        return out.stdout.splitlines()
    except Exception as e:
        sys.stderr.write(f"cloud pull failed · {type(e).
