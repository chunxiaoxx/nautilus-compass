"""compass v0.9.x → v1.0 · encrypt legacy plaintext observations.

For Pro+ users upgrading from v0.9.x: re-encrypt all existing
content_plain rows in observations table using the new master_key.

Run (interactive):
  python tools/encrypt_legacy_obs.py --user-id u_xxx
    → prompts for passphrase + encryption_salt (from signup response)
    → reads all observations WHERE user_id=? AND content_plain IS NOT NULL
    → encrypts each · sets encrypted_body + encryption_version='v1' · NULLs content_plain
    → COMMIT

Idempotent: re-running on already-encrypted obs is a no-op
(skips rows where content_plain IS NULL).

Backup automatic: copies db file to db.pre-v1-encrypt before mutation.
Stop and rollback: copy backup back · restart server.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR / "sdk"))

from compass_crypto import derive_master_key, encrypt_obs


@contextmanager
def db(path: Path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_encryption_salt(conn: sqlite3.Connection, user_id: str) -> bytes:
    row = conn.execute("SELECT encryption_salt FROM users WHERE user_id = ?",
                       (user_id,)).fetchone()
    if not row or not row["encryption_salt"]:
        raise SystemExit(f"no user / encryption_salt for {user_id}")
    return row["encryption_salt"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user-id", required=True, help="u_<id> to encrypt")
    p.add_argument("--db", type=Path, default=Path(os.environ.get("COMPASS_DB_PATH", "/var/lib/compass/compass.db")))
    p.add_argument("--passphrase", default=None, help="(insecure · for testing) · prompts if not set")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not args.db.exists():
        raise SystemExit(f"db not found: {args.db}")

    # Backup
    if not args.dry_run:
        backup = args.db.parent / f"{args.db.name}.pre-v1-encrypt-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(args.db, backup)
        print(f"[backup] {args.db} → {backup}")

    # Get passphrase
    passphrase = args.passphrase or getpass.getpass(f"Passphrase for {args.user_id}: ")

    with db(args.db) as conn:
        salt = get_encryption_salt(conn, args.user_id)
        master = derive_master_key(passphrase, salt)
        print(f"[crypto] master_key derived (32 bytes)")

        # Find legacy plaintext obs
        rows = conn.execute("""
            SELECT obs_id, content_plain
            FROM observations
            WHERE user_id = ? AND content_plain IS NOT NULL AND encrypted_body IS NULL
        """, (args.user_id,)).fetchall()

        print(f"[migrate] found {len(rows)} legacy plaintext obs to encrypt")

        if args.dry_run:
            for r in rows[:5]:
                print(f"  · {r['obs_id']} ({len(r['content_plain'] or '')} chars)")
            if len(rows) > 5:
                print(f"  ... + {len(rows) - 5} more")
            print("[dry-run] no changes made")
            return 0

        encrypted_count = 0
        failed = []
        for r in rows:
            obs_id = r["obs_id"]
            try:
                content = json.loads(r["content_plain"])
                if not isinstance(content, dict):
                    failed.append((obs_id, f"content_plain not a dict: {type(content).__name__}"))
                    continue
                blob = encrypt_obs(master, obs_id, content)
                conn.execute("""
                    UPDATE observations
                    SET encrypted_body = ?, encryption_version = 'v1', content_plain = NULL
                    WHERE obs_id = ?
                """, (blob, obs_id))
                encrypted_count += 1
            except Exception as e:
                failed.append((obs_id, str(e)[:100]))

        conn.commit()

    print(f"\n[migrate] complete:")
    print(f"  encrypted: {encrypted_count}")
    print(f"  failed:    {len(failed)}")
    if failed:
        print(f"\nfailures (first 5):")
        for obs_id, err in failed[:5]:
            print(f"  · {obs_id}: {err}")

    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
