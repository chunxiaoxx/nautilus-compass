---
name: orgfuel-ORGG-a04f7eaed1000114-725f9ef20b
description: "判读档判例 2026-06-24-durable-mcp-transport · Task 5: Watchdog / "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a04f7eaed1000114
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-durable-mcp-transport · Task 5: Watchdog / heartbeat (supervisor)
## Task 5: Watchdog / heartbeat (supervisor)

**Files:**
- Create: `mcp_durable/watchdog.py` + `ops/compass-mcp-watchdog.service`/`.timer` (template from `compass-mcp-tcp.service`)
- Test: `tests/mcp_durable/test_watchdog.py`

**Behaviour:** periodic `ping`→`pong` on the link (or TCP health probe of the daemon port); on K consecutive misses → restart the daemon unit (systemd) and log. Key insight (research §A4): checkpoint≠durable — a dead daemon needs external detection. Pure decision fn `should_restart(miss_count, threshold)` is the unit-tested core; the systemd wiring is ops.

**TDD:** `should_restart` truth table + a fake-clock heartbeat loop that flips to restart after K misses. Commit. (Deploy the time
