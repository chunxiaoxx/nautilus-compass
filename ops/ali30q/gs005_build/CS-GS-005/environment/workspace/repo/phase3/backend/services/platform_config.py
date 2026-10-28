"""
Platform Config Service — key-value config backed by platform_config table.

Table schema (already exists):
  platform_config(id, config_key, config_value JSONB, source, source_id,
                  previous_value, updated_at, created_at)

Provides get/set with a 60-second in-memory TTL cache.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory cache: {key: (value_dict, expiry_timestamp)}
# ---------------------------------------------------------------------------
_cache: Dict[str, tuple] = {}
_CACHE_TTL = 60  # seconds


def _cache_get(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if entry and entry[1] > time.monotonic():
        return entry[0]
    return None


def _cache_set(key: str, value: dict) -> None:
    _cache[key] = (value, time.monotonic() + _CACHE_TTL)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_config_sync(db: Session, key: str) -> Optional[dict]:
    """Return config_value as dict for *key*, using cache when fresh."""
    cached = _cache_get(key)
    if cached is not None:
        return cached

    try:
        row = db.execute(
            text("SELECT config_value FROM platform_config WHERE config_key = :k ORDER BY updated_at DESC LIMIT 1"),
            {"k": key},
        ).fetchone()
        if row is None:
            return None
        val = row.config_value if isinstance(row.config_value, dict) else {}
        _cache_set(key, val)
        return val
    except Exception as e:
        logger.warning("platform_config.get(%s) failed: %s", key, e)
        return None


def set_config_sync(
    db: Session,
    key: str,
    value: dict,
    source: str = "manual",
    source_id: Optional[str] = None,
) -> bool:
    """Upsert config_value for *key*. Stores previous_value for audit. Returns True on success."""
    import json

    previous = get_config_sync(db, key)
    try:
        db.execute(text(
            """INSERT INTO platform_config (config_key, config_value, source, source_id, previous_value, updated_at)
               VALUES (:k, CAST(:v AS jsonb), :src, :sid, CAST(:pv AS jsonb), NOW())
               ON CONFLICT (config_key) DO UPDATE
               SET config_value  = CAST(:v AS jsonb),
                   previous_value = CAST(:pv AS jsonb),
                   source         = :src,
                   source_id      = :sid,
                   updated_at     = NOW()"""
        ), {
            "k": key,
            "v": json.dumps(value),
            "src": source,
            "sid": source_id,
            "pv": json.dumps(previous) if previous else None,
        })
        db.commit()
        _cache_set(key, value)
        return True
    except Exception as e:
        logger.error("platform_config.set(%s) failed: %s", key, e)
        try:
            db.rollback()
        except Exception:
            pass
        return False
