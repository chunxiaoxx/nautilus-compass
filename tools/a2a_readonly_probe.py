#!/usr/bin/env python3
"""Read-only A2A settlement probe.

Only calls settlement.account(mode=balance) and settlement.ledger. It refuses
all other tool names and writes a redacted evidence bundle with SHA-256 hashes.
Run from an environment that is explicitly allowed to reach the partner gateway.
"""
from __future__ import annotations
import argparse, hashlib, json, time
from pathlib import Path
from urllib.request import Request, urlopen

ALLOWED = {"settlement.account", "settlement.ledger"}

def call(url: str, name: str, arguments: dict, timeout: int) -> dict:
    if name not in ALLOWED:
        raise ValueError(f"refusing non-read-only tool: {name}")
    body = {"jsonrpc": "2.0", "id": name, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    req = Request(url, data=raw, method="POST", headers={
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    started = time.time()
    with urlopen(req, timeout=timeout) as resp:
        payload = resp.read()
        return {
            "tool": name, "status": resp.status,
            "elapsed_ms": round((time.time() - started) * 1000, 2),
            "request_sha256": hashlib.sha256(raw).hexdigest(),
            "response_sha256": hashlib.sha256(payload).hexdigest(),
            "response": payload.decode("utf-8", "replace"),
        }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="https://mcp.xn--5kvtwv52d.com/mcp/gateway")
    ap.add_argument("--account", default="agent-demo-verify")
    ap.add_argument("--out", default="a2a_readonly_trace.json")
    ap.add_argument("--timeout", type=int, default=15)
    args = ap.parse_args()
    results = []
    errors = []
    for name, arguments in [
        ("settlement.account", {"account_id": args.account, "mode": "balance"}),
        ("settlement.ledger", {"account_id": args.account}),
    ]:
        try:
            results.append(call(args.url, name, arguments, args.timeout))
        except Exception as exc:
            errors.append({"tool": name, "error_type": type(exc).__name__, "error": str(exc)})
    bundle = {"url": args.url, "account": args.account, "read_only": True,
              "writes_attempted": False, "results": results, "errors": errors}
    Path(args.out).write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"out": args.out, "results": len(results), "errors": len(errors)}, ensure_ascii=False))
    return 0 if not errors else 2

if __name__ == "__main__":
    raise SystemExit(main())
