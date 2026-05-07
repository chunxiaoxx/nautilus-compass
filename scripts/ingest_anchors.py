#!/usr/bin/env python3
"""Ingest anchor JSON profiles → compass.anchors (BGE-m3 1024-dim).

Usage:
  COMPASS_PG_DSN="postgresql://..." python scripts/ingest_anchors.py

Reads all `anchors_<profile>.json` (positive_anchors/negative_anchors lists)
and `anchors.json` (default · profile=general). Embeds with BGE-m3, upserts
into compass.anchors keyed by (tenant_id, anchor_id).

For Day 3, we ingest as **profile-level templates** (tenant_id = profile name)
so any tenant can switch profile without re-embedding. When external tenants
register with profile=vc, drift_check uses 'vc' anchors.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg

PG_DSN = os.environ.get(
    "COMPASS_PG_DSN",
    "postgresql://v5:v5_local_password_change_me@127.0.0.1:5432/v5",
)
PLUGIN_DIR = Path(__file__).resolve().parent.parent
PROFILES = ["general", "finance", "legal", "medical", "vc", "zenmind", "adapted"]


def load_bge():
    """Lazy load · keep model alive for batch."""
    from sentence_transformers import SentenceTransformer
    home_path = Path.home() / ".cache/modelscope/hub/models/BAAI/bge-m3"
    model_id = str(home_path) if home_path.exists() else "BAAI/bge-m3"
    print(f"[bge] loading {model_id} ...")
    return SentenceTransformer(model_id, device="cpu")


def load_profile(profile: str) -> tuple[list[str], list[str]]:
    """Returns (positive, negative) text lists for a profile."""
    fname = "anchors.json" if profile == "general" else f"anchors_{profile}.json"
    path = PLUGIN_DIR / fname
    if not path.exists():
        return [], []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("positive_anchors", []), data.get("negative_anchors", [])


def ensure_profile_tenant(conn, profile: str):
    """Create system tenant for each profile (if missing)."""
    tid = f"_profile_{profile}"
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO compass.tenants (tenant_id, profile, quota_override) "
            "VALUES (%s, %s, 0) "
            "ON CONFLICT (tenant_id) DO UPDATE SET profile = EXCLUDED.profile",
            (tid, profile),
        )
    return tid


def ingest_one(conn, model, profile: str) -> int:
    pos, neg = load_profile(profile)
    if not pos and not neg:
        print(f"[skip] {profile} · empty")
        return 0
    tid = ensure_profile_tenant(conn, profile)

    rows = []
    if pos:
        embs = model.encode(pos, normalize_embeddings=True, show_progress_bar=False)
        for i, (text, vec) in enumerate(zip(pos, embs)):
            rows.append((tid, f"pos_{i:03d}", vec.tolist(), "positive", text))
    if neg:
        embs = model.encode(neg, normalize_embeddings=True, show_progress_bar=False)
        for i, (text, vec) in enumerate(zip(neg, embs)):
            rows.append((tid, f"neg_{i:03d}", vec.tolist(), "negative", text))

    with conn.cursor() as cur:
        # clear stale anchors for this profile · then bulk insert
        cur.execute("DELETE FROM compass.anchors WHERE tenant_id = %s", (tid,))
        for row in rows:
            cur.execute(
                "INSERT INTO compass.anchors "
                "(tenant_id, anchor_id, vector, type, text) "
                "VALUES (%s, %s, %s::vector, %s, %s)",
                row,
            )
    conn.commit()
    print(f"[ok] {profile} · {len(pos)} pos + {len(neg)} neg = {len(rows)} anchors")
    return len(rows)


def main():
    print(f"[pg] {PG_DSN.split('@')[1] if '@' in PG_DSN else PG_DSN}")
    model = load_bge()
    total = 0
    with psycopg.connect(PG_DSN) as conn:
        for profile in PROFILES:
            try:
                total += ingest_one(conn, model, profile)
            except Exception as e:
                print(f"[fail] {profile}: {type(e).__name__}: {e}")
    print(f"\n[done] total {total} anchors across {len(PROFILES)} profiles")


if __name__ == "__main__":
    main()
