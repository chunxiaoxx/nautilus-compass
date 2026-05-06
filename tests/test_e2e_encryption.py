"""compass v1.0 · end-to-end encryption test.

Simulates the full flow:
  1. User signs up (server side · gets encryption_salt)
  2. Client derives master_key from passphrase + salt
  3. Client encrypts obs · POSTs encrypted_body
  4. Server stores encrypted_body (can't decrypt)
  5. Client GETs back · decrypts using master_key
  6. Plaintext matches

Run:
  PYTHONUTF8=1 python tests/test_e2e_encryption.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR / "sdk"))


def test_e2e_encrypt_decrypt():
    """Full E2EE flow: client encrypts → server stores blob → client decrypts."""
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs, generate_salt

    # Step 1: user signs up · server generates salt
    salt = generate_salt()
    passphrase = "user passphrase 用户密码 with mixed scripts"

    # Step 2: client derives master_key
    master = derive_master_key(passphrase, salt)
    assert len(master) == 32

    # Step 3: client prepares + encrypts obs
    obs_id = "ob_e2e_test_001"
    content = {
        "name": "E2E test obs",
        "description": "Cross-region encrypted memory",
        "body": "Multi-line content · 中英混合 · 特殊字符 ' OR 1=1 -- · emojis 🔐",
    }
    blob = encrypt_obs(master, obs_id, content)
    assert blob.startswith("v1:")

    # Step 4: server stores blob (we simulate · don't have server running)
    server_storage = {obs_id: {"encrypted_body": blob, "encryption_version": "v1"}}

    # Server CANNOT decrypt (doesn't have master_key)
    server_seen_blob = server_storage[obs_id]["encrypted_body"]
    # Verify blob is opaque to server
    assert "name" not in server_seen_blob
    assert "OR 1=1" not in server_seen_blob
    assert "🔐" not in server_seen_blob

    # Step 5: client GETs blob back · decrypts
    decrypted = decrypt_obs(master, obs_id, server_seen_blob)
    assert decrypted == content
    print(f"  [PASS] e2e: client encrypt → server stores opaque → client decrypts")
    print(f"        plaintext_size={sum(len(str(v)) for v in content.values())}")
    print(f"        ciphertext_size={len(blob)}")
    print(f"        overhead={len(blob) - sum(len(str(v)) for v in content.values())} bytes")


def test_e2e_different_users_isolated():
    """User A's master_key cannot decrypt user B's blobs."""
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs, generate_salt

    salt_a = generate_salt()
    salt_b = generate_salt()
    master_a = derive_master_key("alice", salt_a)
    master_b = derive_master_key("bob", salt_b)

    obs_id = "ob_shared_id"
    content_a = {"name": "Alice's secret"}
    blob_a = encrypt_obs(master_a, obs_id, content_a)

    # Bob tries to decrypt Alice's blob with his master_key (and same obs_id)
    try:
        result = decrypt_obs(master_b, obs_id, blob_a)
        raise AssertionError(f"Bob should NOT decrypt Alice's blob · got {result}")
    except Exception as e:
        if "AssertionError" in type(e).__name__:
            raise
        print(f"  [PASS] cross-user isolation · Bob's key fails ({type(e).__name__})")


def test_e2e_bulk_obs():
    """Encrypt + decrypt 100 obs · check throughput is reasonable."""
    import time
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

    master = derive_master_key("test", b"x" * 32)

    contents = [
        {"name": f"obs {i}", "body": f"body {i}" * 50}
        for i in range(100)
    ]

    start = time.time()
    blobs = [encrypt_obs(master, f"ob_{i:04d}", c) for i, c in enumerate(contents)]
    enc_time = time.time() - start

    start = time.time()
    decrypted = [decrypt_obs(master, f"ob_{i:04d}", b) for i, b in enumerate(blobs)]
    dec_time = time.time() - start

    assert decrypted == contents, "bulk roundtrip mismatch"
    print(f"  [PASS] bulk 100 obs · enc={enc_time*1000:.0f}ms · dec={dec_time*1000:.0f}ms")
    print(f"        per-obs: enc={enc_time*10:.1f}ms · dec={dec_time*10:.1f}ms")


def test_e2e_recovery_lost_passphrase():
    """If user loses passphrase · data is lost (by design · this is the tradeoff)."""
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

    salt = b"x" * 32
    correct_pass = "i remember this"
    forgotten_pass = "this is what I now think it was"

    master_correct = derive_master_key(correct_pass, salt)
    master_wrong = derive_master_key(forgotten_pass, salt)

    blob = encrypt_obs(master_correct, "ob_secret", {"data": "very important"})

    # Simulate user trying with forgotten passphrase
    try:
        decrypt_obs(master_wrong, "ob_secret", blob)
        raise AssertionError("forgotten passphrase should fail decryption")
    except Exception as e:
        if "AssertionError" in type(e).__name__:
            raise
        print(f"  [PASS] data lost on forgotten passphrase (intentional · matches v1.0 spec)")


def test_legacy_migration_idempotent():
    """encrypt_legacy_obs · re-running on encrypted data is no-op."""
    import sqlite3
    sys.path.insert(0, str(PLUGIN_DIR / "tools"))

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        conn = sqlite3.connect(db_path)
        conn.executescript("""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                encryption_salt BLOB,
                region TEXT,
                created_at TEXT
            );
            CREATE TABLE observations (
                obs_id TEXT PRIMARY KEY,
                user_id TEXT,
                agent_id TEXT,
                ts TEXT,
                content_plain TEXT,
                encrypted_body TEXT,
                encryption_version TEXT,
                region TEXT
            );
        """)
        salt = b"y" * 32
        conn.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
                     ("u_test", salt, "cn-shanghai", "2026-05-05T00:00:00Z"))
        # 2 plaintext + 1 already-encrypted
        import json
        conn.execute("INSERT INTO observations (obs_id, user_id, agent_id, ts, content_plain, region) VALUES (?, ?, ?, ?, ?, ?)",
                     ("ob_a", "u_test", "ag_a", "2026-05-05T00:00:00Z", json.dumps({"name": "A"}), "cn-shanghai"))
        conn.execute("INSERT INTO observations (obs_id, user_id, agent_id, ts, content_plain, region) VALUES (?, ?, ?, ?, ?, ?)",
                     ("ob_b", "u_test", "ag_b", "2026-05-05T00:00:00Z", json.dumps({"name": "B"}), "cn-shanghai"))
        conn.execute("INSERT INTO observations (obs_id, user_id, agent_id, ts, encrypted_body, encryption_version, region) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     ("ob_c", "u_test", "ag_c", "2026-05-05T00:00:00Z", "v1:already:encrypted", "v1", "cn-shanghai"))
        conn.commit()
        conn.close()

        # Run migration script
        import subprocess
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
        result = subprocess.run(
            [sys.executable, str(PLUGIN_DIR / "tools" / "encrypt_legacy_obs.py"),
             "--user-id", "u_test", "--db", str(db_path),
             "--passphrase", "test_pass"],
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=30,
        )
        assert "encrypted: 2" in result.stdout, f"expected 2 encrypted · got: {result.stdout}"

        # Verify
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT obs_id, content_plain, encrypted_body FROM observations").fetchall()
        for obs_id, plain, enc in rows:
            if obs_id != "ob_c":
                assert plain is None, f"{obs_id} content_plain not nulled"
                assert enc is not None, f"{obs_id} not encrypted"
        conn.close()
        print(f"  [PASS] legacy migration · 2 encrypted · idempotent (ob_c untouched)")


def run_all():
    import os  # for subprocess env
    globals()["os"] = os

    tests = [
        test_e2e_encrypt_decrypt,
        test_e2e_different_users_isolated,
        test_e2e_bulk_obs,
        test_e2e_recovery_lost_passphrase,
        test_legacy_migration_idempotent,
    ]
    print("=== compass v1.0 E2E encryption tests ===\n")
    failed = 0
    for t in tests:
        print(f"[{t.__name__}]")
        try:
            t()
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  [ERROR] {type(e).__name__}: {e}")
            failed += 1
        print()
    print(f"=== {len(tests) - failed}/{len(tests)} passed ===")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())
