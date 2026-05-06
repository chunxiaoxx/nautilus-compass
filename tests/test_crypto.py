"""Tests for compass v1.0 E2EE crypto module.

Run:
  PYTHONUTF8=1 python tests/test_crypto.py
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR / "sdk"))


def _has_aes():
    try:
        from compass_crypto import _has_aes_lib
        return _has_aes_lib()
    except Exception:
        return False


def test_hkdf_rfc5869_test_vector():
    """RFC 5869 Test Case 1 vector."""
    from compass_crypto import hkdf
    ikm = bytes.fromhex("0b" * 22)
    salt = bytes.fromhex("000102030405060708090a0b0c")
    info = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9")
    expected = bytes.fromhex(
        "3cb25f25faacd57a90434f64d0362f2a"
        "2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
        "34007208d5b887185865"
    )
    out = hkdf(ikm, salt, info, length=42)
    assert out == expected, f"HKDF RFC test vector mismatch"
    print("  [PASS] HKDF RFC 5869 test vector 1")


def test_master_key_deterministic():
    from compass_crypto import derive_master_key
    salt = b"x" * 32
    pwd = "passphrase"
    k1 = derive_master_key(pwd, salt)
    k2 = derive_master_key(pwd, salt)
    assert k1 == k2
    assert len(k1) == 32
    print("  [PASS] master_key deterministic · 32 bytes")


def test_master_key_salt_isolation():
    from compass_crypto import derive_master_key
    salt1 = b"a" * 32
    salt2 = b"b" * 32
    k1 = derive_master_key("pw", salt1)
    k2 = derive_master_key("pw", salt2)
    assert k1 != k2
    print("  [PASS] different salt → different master_key")


def test_per_obs_key_isolation():
    from compass_crypto import derive_master_key, derive_per_obs_key
    master = derive_master_key("pw", b"x" * 32)
    k_a = derive_per_obs_key(master, "ob_aaa")
    k_b = derive_per_obs_key(master, "ob_bbb")
    assert k_a != k_b
    assert len(k_a) == 32
    print(f"  [PASS] per-obs-key isolated · 32 bytes")


def test_encrypt_roundtrip():
    if not _has_aes():
        print("  [SKIP] no cryptography/nacl installed")
        return
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

    master = derive_master_key("pw", b"s" * 32)
    obs_id = "ob_test"
    content = {"name": "测试", "body": "encrypted text · 中文 · multi\nline"}
    blob = encrypt_obs(master, obs_id, content)
    decrypted = decrypt_obs(master, obs_id, blob)
    assert decrypted == content
    assert blob.startswith("v1:")
    print(f"  [PASS] encrypt/decrypt roundtrip · blob_len={len(blob)}")


def test_wrong_master_key_fails():
    if not _has_aes():
        print("  [SKIP]")
        return
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

    m1 = derive_master_key("right", b"s" * 32)
    m2 = derive_master_key("wrong", b"s" * 32)
    blob = encrypt_obs(m1, "ob_x", {"k": "v"})
    try:
        decrypt_obs(m2, "ob_x", blob)
        raise AssertionError("should have failed")
    except (ValueError, Exception) as e:
        if "AssertionError" in str(type(e).__name__):
            raise
        print(f"  [PASS] wrong master_key rejected ({type(e).__name__})")


def test_wrong_obs_id_fails():
    if not _has_aes():
        print("  [SKIP]")
        return
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

    m = derive_master_key("pw", b"s" * 32)
    blob = encrypt_obs(m, "ob_x", {"k": "v"})
    try:
        decrypt_obs(m, "ob_DIFFERENT", blob)
        raise AssertionError("should have failed")
    except Exception as e:
        if "AssertionError" in str(type(e).__name__):
            raise
        print(f"  [PASS] wrong obs_id rejected ({type(e).__name__})")


def test_tampered_ciphertext_fails():
    if not _has_aes():
        print("  [SKIP]")
        return
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

    m = derive_master_key("pw", b"s" * 32)
    blob = encrypt_obs(m, "ob_x", {"k": "v"})
    parts = blob.split(":")
    pad = "=" * (-len(parts[2]) % 4)
    ct = bytearray(base64.urlsafe_b64decode(parts[2] + pad))
    ct[0] ^= 0x01
    tampered_ct = base64.urlsafe_b64encode(bytes(ct)).decode("ascii").rstrip("=")
    tampered_blob = f"{parts[0]}:{parts[1]}:{tampered_ct}"
    try:
        decrypt_obs(m, "ob_x", tampered_blob)
        raise AssertionError("should have failed")
    except Exception as e:
        if "AssertionError" in str(type(e).__name__):
            raise
        print(f"  [PASS] tampered ciphertext rejected ({type(e).__name__})")


def test_blob_format():
    if not _has_aes():
        print("  [SKIP]")
        return
    from compass_crypto import derive_master_key, encrypt_obs

    m = derive_master_key("pw", b"s" * 32)
    blob = encrypt_obs(m, "ob_x", {"k": "v"})
    parts = blob.split(":")
    assert len(parts) == 3
    assert parts[0] == "v1"
    # nonce 12 bytes → base64 url-safe ~16 chars (without padding)
    assert 12 <= len(parts[1]) <= 18
    print(f"  [PASS] blob format · v1:nonce:ct · 3 parts")


def test_chinese_content():
    if not _has_aes():
        print("  [SKIP]")
        return
    from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

    m = derive_master_key("用户密码", b"s" * 32)
    content = {
        "name": "中文测试",
        "body": "Mixed 中英 content · with emoji 🎯 (no compass uses emoji though)",
        "description": "包含 SQL 注入字符 ' OR 1=1 --",
    }
    blob = encrypt_obs(m, "ob_中文", content)
    decrypted = decrypt_obs(m, "ob_中文", blob)
    assert decrypted == content, f"got {decrypted}"
    print(f"  [PASS] Chinese content + special chars roundtrip")


def run_all():
    tests = [
        test_hkdf_rfc5869_test_vector,
        test_master_key_deterministic,
        test_master_key_salt_isolation,
        test_per_obs_key_isolation,
        test_encrypt_roundtrip,
        test_wrong_master_key_fails,
        test_wrong_obs_id_fails,
        test_tampered_ciphertext_fails,
        test_blob_format,
        test_chinese_content,
    ]
    print("=== compass v1.0 E2EE crypto tests ===\n")
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
