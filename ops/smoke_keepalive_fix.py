#!/usr/bin/env python3
"""Smoke test · verify --timeout-keep-alive 75 fixed RemoteProtocolError.

Reuses one httpx.AsyncClient (matches V5 production pattern via httpcore
process-level pool) · sleeps 10s between calls (longer than old 5s default
keep-alive, shorter than new 75s) · counts RemoteProtocolError occurrences.

Before fix: low-freq calls hit closed idle conn → RemoteProtocolError
After fix:  server holds conn 75s · idle 10s should pass cleanly.
"""
import asyncio
import sys
import time
import httpx

URL = "http://127.0.0.1:8770/v1/v14/recall"
HEADERS = {"X-Tenant-ID": "smoke-keepalive", "X-User-ID": "smoke-keepalive"}
PARAMS = {"q": "test", "top_k": 3, "scope": "user"}


async def main():
    errs = {"RemoteProtocolError": 0, "ReadError": 0, "other": 0}
    ok = 0
    async with httpx.AsyncClient(timeout=20) as c:
        for i in range(6):
            t0 = time.time()
            try:
                r = await c.get(URL, headers=HEADERS, params=PARAMS)
                if r.status_code == 200:
                    ok += 1
                    dt = (time.time() - t0) * 1000
                    print(f"#{i+1} OK · {dt:.0f}ms · hits={len(r.json().get('hits', []))}")
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
            if i < 5:
                print(f"  ... idle 10s (was old 5s keep-alive · now 75s)")
                await asyncio.sleep(10)
    total_fail = sum(errs.values())
    print(f"\nresult: ok={ok}/6 · fail={total_fail}/6 · {errs}")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
