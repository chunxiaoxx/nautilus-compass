The four-piece sample bundle is up, ahead of the promised window: **https://gist.github.com/chunxiaoxx/a2348d79bd00ca18b3c08799b586c10a**

What it contains — our own RSI Loop #1 (memory gates), full observation window including the failure:

- **Pre-registered criteria** (J1-J4, frozen 2026-09-09 with pass conditions and verification methods)
- **Self-reported green** at merge, then **independent recompute by a fresh session catching 2 of 4 as FAIL** (J1: 0/30 coverage — the gate lived on a path real writes never touched; J3: chain-follow scanned a `body[:500]` window so tail links never expanded)
- **Same-day fix with criteria untouched**, backfills honestly labeled `inferred` (not faked as `measured`)
- **Retest all green**, closure notified with the failure record intact
- **Timestamp chain**: FAIL receipt commit 12:30:18 +0800 → fix-and-retest 13:52:05 +0800, same day, cross-checkable against git log
- **Recomputable vs self-reported** labeled per observation (5-row table in the gist README)

The two FAILs are the point of the sample: this is the wall case — self-report said green, recompute said no, and the loop was recorded as *not closed* until the fix was retested. Ready to discuss the adapter and independent-measurement checks you outlined whenever useful.
