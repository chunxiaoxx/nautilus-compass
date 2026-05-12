#!/usr/bin/env python3
"""Long-idle smoke · simulates V5 production gap.

Production V5 calls recall every 10-15 min · prior smoke used 10s · false-positive.
This smoke uses 90s idle (> uvicorn --timeout-keep-alive 75s) so that WITHOUT
Connection: close · pool entry stale · client next call must fail.

Expected after Connection: close patch:
- /v1/v14/recall · 0 RemoteProtocolError even with 90s idle (server told client to close)
- pool stays clean across calls

Without patch (old behavior):
- /v1/v14/recall · idle 90s · server-side close · client pool stale · fail
"""
import asyncio
import sys
import time
import httpx

URL = "http://127.0.0.1:8770/v1/v14/recall"
HEADERS = {"X-Tenant-ID": "smoke-long-idle", "X-User-ID": "smoke-long-idle"}
PARAMS = {"q": "test long idle", "top_k": 3, "scope": "user"}
IDLE_S = 90  # > server --timeout-keep-alive 75


async def main():
    errs = {"RemoteProtocolError": 0, "ReadError": 0, "other": 0}
    ok = 0
    # Use a long-lived pooled client (matches V5/V6 httpcore process pool behavior)
    async with httpx.AsyncClient(timeout=20) as c:
        for i in range(3):
            t0 = time.time()
            try:
                r = await c.get(URL, headers=HEADERS, params=PARAMS)
                if r.status_code == 200:
                    ok += 1
                    dt = (time.time() - t0) * 1000
                    conn_hdr = r.headers.get("connection", "(none)")
                    print(f"#{i+1} OK · {dt:.0f}ms · hits={len(r.json().get('hits', []))} · Connection: {conn_hdr}")
                else:
                    print(f"#{i+1} HTTP {r.status_code}")
            except httpx.RemoteProtocolError as e:
                errs["RemoteProtocolError"] += 1
                print(f"#{i+1} FAIL · RemoteProtocolError · {e}")
            except httpx.ReadError as e:
                errs["ReadError"] += 1
                print(f"#{i+1} FAIL · ReadError · {e}")
            except Exception as e:
                errs["other"] += 1
                print(f"#{i+1} FAIL · {type(e).__name__} · {e}")
            if i < 2:
                print(f"  ... idle {IDLE_S}s (> uvicorn keep-alive 75s · would race WITHOUT Connection: close)")
                await asyncio.sleep(IDLE_S)
    total_fail = sum(errs.values())
    print(f"\nresult: ok={ok}/3 · fail={total_fail}/3 · {errs}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
