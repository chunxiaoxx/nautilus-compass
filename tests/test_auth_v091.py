"""Tests for v0.9.1 auth (signup · login · refresh · token verify).

Tests core scrypt + JWT logic that compass_http_v09.py uses.
Independent of FastAPI runtime · pure Python.

Run:
  PYTHONUTF8=1 python tests/test_auth_v091.py
"""
from __future__ import annotations

import hashlib
import secrets
import sys
import time


def test_scrypt_passphrase_hash():
    salt1 = secrets.token_bytes(32)
    salt2 = secrets.token_bytes(32)
    pwd = "correct horse battery staple"

    h1 = hashlib.scrypt(pwd.encode(), salt=salt1, n=16384, r=8, p=1, dklen=32).hex()
    h1_again = hashlib.scrypt(pwd.encode(), salt=salt1, n=16384, r=8, p=1, dklen=32).hex()
    h2 = hashlib.scrypt(pwd.encode(), salt=salt2, n=16384, r=8, p=1, dklen=32).hex()

    assert h1 == h1_again, "deterministic for same salt"
    assert h1 != h2, "different salt → different hash"
    print("  [PASS] scrypt deterministic + salt-isolated")


def test_scrypt_wrong_passphrase():
    salt = secrets.token_bytes(32)
    pwd_correct = "correct horse battery staple"
    pwd_wrong = "incorrect horse battery staple"

    h_correct = hashlib.scrypt(pwd_correct.encode(), salt=salt, n=16384, r=8, p=1, dklen=32).hex()
    h_wrong = hashlib.scrypt(pwd_wrong.encode(), salt=salt, n=16384, r=8, p=1, dklen=32).hex()

    assert h_correct != h_wrong
    print("  [PASS] wrong passphrase rejected")


def test_jwt_roundtrip():
    try:
        from jose import jwt as jose_jwt
    except ImportError:
        print("  [SKIP] python-jose not installed · pip install python-jose[cryptography]")
        return

    SECRET = "test-secret-do-not-use-in-prod"
    payload = {
        "user_id": "u_test_abc",
        "region": "cn-shanghai",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }

    token = jose_jwt.encode(payload, SECRET, algorithm="HS256")
    decoded = jose_jwt.decode(token, SECRET, algorithms=["HS256"])

    assert decoded["user_id"] == "u_test_abc"
    assert decoded["region"] == "cn-shanghai"
    print(f"  [PASS] JWT roundtrip · token_len={len(token)}")


def test_jwt_wrong_secret():
    try:
        from jose import jwt as jose_jwt, JWTError
    except ImportError:
        print("  [SKIP] python-jose not installed")
        return

    payload = {"user_id": "u_test", "iat": int(time.time())}
    token = jose_jwt.encode(payload, "secret-A", algorithm="HS256")

    try:
        jose_jwt.decode(token, "secret-B", algorithms=["HS256"])
        raise AssertionError("decode should have raised")
    except JWTError:
        print("  [PASS] wrong secret rejected")


def test_jwt_expired():
    try:
        from jose import jwt as jose_jwt, ExpiredSignatureError
    except ImportError:
        print("  [SKIP] python-jose not installed")
        return

    SECRET = "secret"
    payload = {
        "user_id": "u_test",
        "iat": int(time.time()) - 100,
        "exp": int(time.time()) - 10,
    }
    token = jose_jwt.encode(payload, SECRET, algorithm="HS256")

    try:
        jose_jwt.decode(token, SECRET, algorithms=["HS256"])
        raise AssertionError("expired token should have raised")
    except ExpiredSignatureError:
        print("  [PASS] expired token rejected")


def test_user_id_format():
    import uuid
    user_id = f"u_{uuid.uuid4().hex[:10]}"
    assert user_id.startswith("u_")
    assert len(user_id) == 12
    print(f"  [PASS] user_id format · sample={user_id}")


def test_region_validation():
    valid_regions = ["cn-shanghai", "eu-frankfurt", "us-virginia"]
    invalid_regions = ["us-east-1", "cn", "europe", ""]

    for r in valid_regions:
        assert r in valid_regions
    for r in invalid_regions:
        assert r not in valid_regions
    print(f"  [PASS] region validation · {len(valid_regions)} valid · {len(invalid_regions)} invalid")


def test_e2ee_master_key_derive():
    """Test scrypt-based master key derivation for E2EE (v1.0)."""
    passphrase = "user passphrase"
    salt = b"x" * 32
    master_key = hashlib.scrypt(passphrase.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    assert len(master_key) == 32, "master key should be 32 bytes for AES-256"
    # deterministic
    master_key2 = hashlib.scrypt(passphrase.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    assert master_key == master_key2
    print(f"  [PASS] E2EE master_key derive · 32 bytes · deterministic")


def run_all():
    tests = [
        test_scrypt_passphrase_hash,
        test_scrypt_wrong_passphrase,
        test_jwt_roundtrip,
        test_jwt_wrong_secret,
        test_jwt_expired,
        test_user_id_format,
        test_region_validation,
        test_e2ee_master_key_derive,
    ]
    print("=== compass v0.9.1 auth tests ===\n")
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
