#!/usr/bin/env python3
"""nautilus · 瘦平台 CLI (W-D) · stdlib-only thin client over the platform API.

Same platform API as the web 看板 — `nautilus <view|dispatch|status>` is the
terminal front-end for the control plane. Deliberately NO heavy deps (urllib only)
so it does NOT drag the nautilus-v5 24-dep runtime (anchor #5 · goal W-D).

  nautilus view                          # 一眼看活系统 (GET /api/platform/control-plane)
  nautilus status                        # 脉搏摘要 (GET /api/platform/rsi-fde)
  nautilus dispatch --target agent --action send_msg --payload '{"to":"...","text":"..."}'

Base URL: --base or $NAUTILUS_API (default http://localhost:8000).
"""
from __future__ import annotations

import json
import os
import sys
from urllib import request as _req, error as _err

DEFAULT_BASE = "http://localhost:8000"

_USAGE = (
    "usage: nautilus <view|status|dispatch> [options]\n"
    "  view                          GET /api/platform/control-plane\n"
    "  status                        GET /api/platform/rsi-fde\n"
    "  dispatch --target T --action A [--payload JSON]\n"
    "  (--base URL or $NAUTILUS_API · default %s)" % DEFAULT_BASE
)


def _real_get(url: str) -> dict:
    with _req.urlopen(url, timeout=10) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _real_post(url: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    rq = _req.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with _req.urlopen(rq, timeout=10) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _parse_opts(args: list[str]) -> dict:
    """Minimal --k v option parser (no argparse · keeps it tiny)."""
    opts: dict = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and i + 1 < len(args):
            opts[a[2:]] = args[i + 1]
            i += 2
        else:
            i += 1
    return opts


def _fmt_view(data: dict) -> str:
    v = data.get("verdicts", {}).get("summary", {})
    a = data.get("agents", {})
    e = data.get("events", {}).get("summary", {})
    return (
        f"FDE verdicts: {v.get('passed', '?')}/{v.get('total', '?')} 通过\n"
        f"Agents:       {a.get('active', '?')} 活跃 / {a.get('total', '?')} 总\n"
        f"Events:       {e.get('total', '?')} 事件"
    )


def run(argv: list[str], http_get=_real_get, http_post=_real_post, base: str | None = None) -> str:
    """Execute one CLI invocation · return the output string (HTTP layer injected)."""
    if base is None:
        base = os.environ.get("NAUTILUS_API", DEFAULT_BASE)
    if not argv:
        return _USAGE
    cmd, rest = argv[0], argv[1:]

    if cmd == "view":
        resp = http_get(f"{base}/api/platform/control-plane")
        return _fmt_view(resp.get("data", {})) if resp.get("success") else f"error: {resp.get('error')}"

    if cmd == "status":
        resp = http_get(f"{base}/api/platform/rsi-fde")
        return _fmt_view(resp.get("data", {})) if resp.get("success") else f"error: {resp.get('error')}"

    if cmd == "dispatch":
        opts = _parse_opts(rest)
        target, action = opts.get("target"), opts.get("action")
        if not target or not action:
            return "error: dispatch requires --target and --action"
        payload = {}
        if opts.get("payload"):
            try:
                payload = json.loads(opts["payload"])
            except json.JSONDecodeError:
                return "error: --payload must be valid JSON"
        resp = http_post(f"{base}/api/platform/dispatch",
                         {"target": target, "action": action, "payload": payload})
        d = resp.get("data", {}) if resp.get("success") else {}
        return (f"routed_to: {d.get('routed_to')} · delivered: {d.get('delivered')}"
                if resp.get("success") else f"error: {resp.get('error')}")

    return f"unknown command '{cmd}'\n{_USAGE}"


def main() -> int:
    out = run(sys.argv[1:])
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
