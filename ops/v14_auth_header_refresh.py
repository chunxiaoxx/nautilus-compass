#!/usr/bin/env python3
"""Refresh a curl Authorization header from protected v14 service credentials.

The token is cached in a mode-0600 header file and renewed only when it has
less than one hour of life left. No credential or token is printed.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

DEFAULT_CREDENTIALS = Path.home() / ".config" / "compass" / "v14_bridge_credentials.json"
DEFAULT_HEADER = Path.home() / ".config" / "compass" / "v14_bridge_auth_header"
MIN_TTL_S = 3600


def _cached_token_valid(header_path: Path, now: float) -> bool:
    try:
        line = header_path.read_text(encoding="utf-8").strip()
        token = line.removeprefix("Authorization: Bearer ")
        if token == line:
            return False
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        return float(claims["exp"]) - now > MIN_TTL_S
    except (OSError, ValueError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        return False


def _write_header(header_path: Path, token: str) -> None:
    header_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".v14_auth_", dir=header_path.parent)
    try:
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"Authorization: Bearer {token}\n")
        os.replace(temporary, header_path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def refresh_if_expiring(
    credentials_path: Path,
    header_path: Path,
    base_url: str,
    *,
    now: float | None = None,
) -> bool:
    """Return True when a new token was fetched; False for a valid cache."""
    current_time = time.time() if now is None else now
    if _cached_token_valid(header_path, current_time):
        return False
    if os.name == "posix" and credentials_path.stat().st_mode & 0o077:
        raise RuntimeError("v14 service credentials must be mode 0600")
    credentials = json.loads(credentials_path.read_text(encoding="utf-8"))
    if not all(isinstance(credentials.get(key), str) and credentials[key]
               for key in ("email", "passphrase")):
        raise ValueError("v14 credentials require non-empty email and passphrase")
    request = urllib.request.Request(
        base_url.rstrip("/") + "/v1/auth/login",
        data=json.dumps({"email": credentials["email"], "passphrase": credentials["passphrase"]}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    token = result.get("token")
    if not isinstance(token, str) or not token:
        raise RuntimeError("v14 login returned no token")
    _write_header(header_path, token)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials-file", type=Path, default=DEFAULT_CREDENTIALS)
    parser.add_argument("--header-file", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--base-url", default=os.environ.get("COMPASS_BASE_URL", "http://127.0.0.1:8770"))
    args = parser.parse_args()
    try:
        refresh_if_expiring(args.credentials_file, args.header_file, args.base_url)
    except Exception as exc:
        print(f"v14 token refresh failed: {type(exc).__name__}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
