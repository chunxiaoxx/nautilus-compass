"""MVP-6: four-probe auth self-check (HANDOFF_20260831 #6 · 无人值守四绿报告).

Runs the four authorization-plane probes against a live 8097 server:
  P1 cross-user read DENY    — token scoped to A cannot read B's space
  P2 cross-user write DENY   — read-only token cannot write anywhere
  P3 same-user own space OK  — A's token reaches A's own space, not denied
  P4 revoke takes effect     — deleted token gets 401 on the next call

Usage:
  python probes.py [base_url]        # default http://127.0.0.1:8097

Exit 0 iff all four green. Creates two throwaway probe users per run
(probe-<tag>@probe.local); safe to rerun; no pre-existing credentials needed.
"""
from __future__ import annotations

import sys
import uuid

_TIMEOUT = 60.0


def _rpc(http, base: str, token: str, tool: str, args: dict):
    # /mcp/ (trailing slash) is the canonical endpoint — bare /mcp 307s.
    return http.post(
        f"{base}/mcp/",
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
              "params": {"name": tool, "arguments": args}},
        timeout=_TIMEOUT,
    )


def run_probes(http, base: str) -> list[tuple[str, bool, str]]:
    """Return [(probe_name, ok, detail)]. `http` is any httpx-compatible client
    (also accepts starlette TestClient, which the pytest suite uses instead)."""
    tag = uuid.uuid4().hex[:10]
    users: dict[str, tuple[str, dict]] = {}
    for k in ("a", "b"):
        email = f"probe-{tag}-{k}@probe.local"
        http.post(f"{base}/signup", json={"email": email,
                                          "passphrase": "probe-only-9ch"},
                  timeout=_TIMEOUT)  # 409 on freak collision; login is the gate
        r = http.post(f"{base}/login", json={"email": email,
                                             "passphrase": "probe-only-9ch"},
                      timeout=_TIMEOUT)
        r.raise_for_status()
        j = r.json()
        users[k] = (j["user_id"], {"Authorization": f"Bearer {j['token']}",
                                   "content-type": "application/json"})
    uid_a, hdr_a = users["a"]
    uid_b, _ = users["b"]
    tok = http.post(f"{base}/tokens", json={"name": f"probe-{tag}"},
                    headers=hdr_a, timeout=_TIMEOUT).json()["token"]

    out: list[tuple[str, bool, str]] = []

    # P1 cross-user read DENY
    r = _rpc(http, base, tok, "recall", {"project": uid_b, "query": "q"})
    out.append(("P1 cross-user read DENY",
                r.status_code == 200 and "forbidden" in r.text,
                f"HTTP {r.status_code}"))

    # P2 cross-user write DENY
    r = _rpc(http, base, tok, "ingest_obs",
             {"project": uid_b, "name": "probe-x", "concept": "gotcha"})
    out.append(("P2 cross-user write DENY",
                r.status_code == 200 and "forbidden" in r.text,
                f"HTTP {r.status_code}"))

    # P3 same-user own space NOT scope-denied (read AND write)
    r1 = _rpc(http, base, tok, "recall", {"project": uid_a, "query": "q"})
    r2 = _rpc(http, base, tok, "ingest_obs",
              {"project": uid_a, "name": "probe-own", "concept": "gotcha"})
    ok = all(r.status_code == 200 and "forbidden" not in r.text
             for r in (r1, r2))
    out.append(("P3 same-user own space OK", ok,
                f"recall {r1.status_code} · write {r2.status_code}"))

    # P4 revoke takes effect immediately
    lst = http.get(f"{base}/tokens", headers=hdr_a, timeout=_TIMEOUT).json()["tokens"]
    tid = next(t["token_id"] for t in lst if t["name"] == f"probe-{tag}")
    rr = http.delete(f"{base}/tokens/{tid}", headers=hdr_a, timeout=_TIMEOUT)
    r = _rpc(http, base, tok, "recall", {"project": uid_a, "query": "q"})
    out.append(("P4 revoke takes effect",
                rr.status_code == 200 and r.status_code == 401,
                f"delete {rr.status_code} · recall-after {r.status_code}"))

    return out


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8097"
    import httpx
    with httpx.Client(follow_redirects=True) as http:
        results = run_probes(http, base)
    all_ok = True
    for name, ok, detail in results:
        print(f"{'GREEN' if ok else 'RED '}  {name}  ({detail})")
        all_ok = all_ok and ok
    print("FOUR-GREEN" if all_ok else "REPORT-RED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
