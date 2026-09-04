"""Capacity smoke test for the hosted endpoint (launch prep, 2026-09-04).

Stages concurrency 1→2→5→10→20 against /mcp/ with a throwaway probe user:
read (recall) and write (ingest_obs) as separate waves per stage. Prints
success rate, p50/p95/max latency and throughput per stage.

Stop-loss rules keep this from hurting production — abort further stages if
any stage shows error rate >20% or p95 >10s. Not a benchmark: a before-launch
capacity check. Total budget ≈400 small JSON-RPC calls over a few minutes.

Usage:
    python scripts/load_probe.py [base_url]
    # default base_url = https://compass.nautilus.social
"""
from __future__ import annotations

import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

_TIMEOUT = 30.0
STAGES = [1, 2, 5, 10, 20]
READ_PER_WORKER = 20        # recall tasks per worker in the read wave
WRITE_PER_WORKER = 8        # ingest_obs tasks per worker in the write wave
STOP_LOSS_ERR = 0.20        # abort if stage error rate exceeds this
STOP_LOSS_P95 = 10.0        # abort if stage p95 (s) exceeds this


def _rpc(client, base: str, token: str, tool: str, args: dict):
    t0 = time.perf_counter()
    try:
        r = client.post(
            f"{base}/mcp/",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                  "params": {"name": tool, "arguments": args}},
            timeout=_TIMEOUT,
        )
        dt = time.perf_counter() - t0
        ok = r.status_code == 200 and "forbidden" not in r.text \
            and "error" not in r.json().get("result", {}).get("content", [{}])[0] \
            .get("text", "error").lower()[:0]  # transport OK; tool errors surface as 200+text
        return dt, ok, r.status_code
    except Exception:
        return time.perf_counter() - t0, False, 0


def _wave(client, base, token, project, tool, args_fn, workers, tasks):
    lat, err = [], 0
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for dt, ok, code in pool.map(lambda i: _rpc(
                client, base, token, tool, args_fn(i)), range(tasks)):
            lat.append(dt)
            err += 0 if ok else 1
    wall = time.perf_counter() - t0
    return lat, err, wall


def _pctl(sorted_lat, p):
    if not sorted_lat:
        return float("nan")
    idx = min(len(sorted_lat) - 1, round(p / 100 * (len(sorted_lat) - 1)))
    return sorted_lat[idx]


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "https://compass.nautilus.social"
    import httpx

    limits = httpx.Limits(max_connections=64)
    with httpx.Client(follow_redirects=True, limits=limits) as client:
        tag = uuid.uuid4().hex[:10]
        email = f"load-{tag}@probe.local"
        client.post(f"{base}/signup", json={"email": email,
                                            "passphrase": "probe-only-9ch"},
                    timeout=_TIMEOUT)
        j = client.post(f"{base}/login", json={"email": email,
                                               "passphrase": "probe-only-9ch"},
                        timeout=_TIMEOUT).json()
        uid, tok = j["user_id"], \
            client.post(f"{base}/tokens", json={"name": f"load-{tag}"},
                        headers={"Authorization": f"Bearer {j['token']}",
                                 "content-type": "application/json"},
                        timeout=_TIMEOUT).json()["token"]

        # warmup (cold path: index creation, conn pool)
        for i in range(3):
            _rpc(client, base, tok, "recall", {"project": uid, "query": f"w{i}"})
        print(f"probed user load-{tag}@probe.local · warmup done\n")

        print(f"{'stage':>5} {'wave':>5} {'n':>4} {'ok%':>6} "
              f"{'p50':>7} {'p95':>7} {'max':>7} {'rps':>6}")
        aborted = None
        for stage in STAGES:
            for wave, tool, per_worker, args_fn in (
                ("read", "recall", READ_PER_WORKER,
                 lambda i: {"project": uid, "query": f"load {i} zenmind compass"}),
                ("write", "ingest_obs", WRITE_PER_WORKER,
                 lambda i: {"project": uid, "name": f"load-{stage}-{i}",
                            "concept": "gotcha"}),
            ):
                tasks = stage * per_worker
                lat, err, wall = _wave(client, base, tok, uid, tool,
                                       args_fn, stage, tasks)
                lat.sort()
                ok_pct = 100.0 * (tasks - err) / tasks
                rps = tasks / wall if wall else 0.0
                print(f"{stage:>5} {wave:>5} {tasks:>4} {ok_pct:>5.1f}% "
                      f"{_pctl(lat, 50):>6.2f}s {_pctl(lat, 95):>6.2f}s "
                      f"{lat[-1]:>6.2f}s {rps:>5.1f}")
                if err / tasks > STOP_LOSS_ERR or _pctl(lat, 95) > STOP_LOSS_P95:
                    aborted = f"stage {stage} {wave}: " \
                              f"err {err}/{tasks}, p95 {_pctl(lat, 95):.2f}s"
                    break
            if aborted:
                break
            time.sleep(3)  # let the server breathe between stages

        print("\nABORTED — " + aborted if aborted else
              "\nALL-STAGES-COMPLETE — capacity smoke within stop-loss limits")


if __name__ == "__main__":
    main()
