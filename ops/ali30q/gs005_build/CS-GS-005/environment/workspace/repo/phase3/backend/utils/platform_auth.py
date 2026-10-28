"""Minimal platform control-plane auth · gate for WRITE/CONTROL endpoints.

The VIEW endpoints (看板/control-plane reads) stay public. The CONTROL/write
endpoints (dispatch · fde/dispatch 派单) must not be open POSTs on production, so
they depend on `require_platform_key`:

  - If env PLATFORM_DISPATCH_KEY is SET (production) → the request MUST carry a
    matching `X-Platform-Key` header, else 401.
  - If the env var is UNSET (dev / test) → allowed (so local TDD needs no key).

Fail-CLOSED on production (key set) · permissive only when no key is configured.
Deliberately tiny (no JWT/DB) — these are platform-internal control calls; the
downstream blocks (a2a/soul/market) enforce their own auth too.
"""
from __future__ import annotations

import os

from fastapi import Header, HTTPException

_ENV_KEY = "PLATFORM_DISPATCH_KEY"


def require_platform_key(x_platform_key: str | None = Header(default=None)) -> bool:
    """FastAPI dependency · gate a control endpoint behind the platform key."""
    configured = os.environ.get(_ENV_KEY)
    if not configured:
        return True  # no key configured (dev/test) → permissive
    if x_platform_key != configured:
        raise HTTPException(status_code=401, detail="invalid or missing X-Platform-Key")
    return True
