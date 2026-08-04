"""Canonical JSON and SHA-256 helpers for PoI-Gate-2 artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes or reject non-JSON values."""

    normalized = _normalize_json_value(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def hash_bytes(value: bytes) -> str:
    if not isinstance(value, bytes):
        raise TypeError("value must be bytes")
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def hash_json(value: Any) -> str:
    return hash_bytes(canonical_json_bytes(value))


def _normalize_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite values are not valid canonical JSON")
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("canonical JSON mapping keys must be strings")
        return {key: _normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_normalize_json_value(item) for item in value]
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


__all__ = ["canonical_json_bytes", "hash_bytes", "hash_json"]
