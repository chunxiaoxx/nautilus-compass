"""compass v1.0 · client-side E2EE crypto module.

Pure stdlib AES-256-GCM (Python 3.10+ has hashlib.scrypt + cryptography optional).
Falls back to PyNaCl (libsodium) if cryptography not installed.

Schema (per paper/V10_FINAL_SPEC.md §5):
  master_key = scrypt(passphrase, encryption_salt, n=16384, r=8, p=1, dklen=32)
  per_obs_key = HKDF-SHA256(master_key, salt=b"compass.v1", info=obs_id_bytes, length=32)
  ciphertext = AES-256-GCM(per_obs_key, plaintext, nonce=12 bytes random)

Output format (base64-url-safe):
  v1:<nonce_b64>:<ciphertext_b64>

Server stores opaque blob · doesn't decrypt · only indexes meta fields.

Usage:
  from compass_crypto import derive_master_key, encrypt_obs, decrypt_obs

  master_key = derive_master_key(passphrase, encryption_salt)
  blob = encrypt_obs(master_key, obs_id, content_dict)
  content = decrypt_obs(master_key, obs_id, blob)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import sys


# ---- HKDF (RFC 5869 · SHA256) ----

def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    return hmac.new(salt, ikm, hashlib.sha256).digest()


def hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    blocks = b""
    out = b""
    counter = 1
    while len(out) < length:
        blocks = hmac.new(prk, blocks + info + bytes([counter]), hashlib.sha256).digest()
        out += blocks
        counter += 1
    return out[:length]


def hkdf(ikm: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    """RFC 5869 HKDF · SHA256."""
    prk = hkdf_extract(salt, ikm)
    return hkdf_expand(prk, info, length)


# ---- Master key derivation ----

def derive_master_key(passphrase: str, encryption_salt: bytes) -> bytes:
    """scrypt-based master key · 32 bytes for AES-256."""
    if len(encryption_salt) < 16:
        raise ValueError("encryption_salt must be ≥16 bytes")
    return hashlib.scrypt(
        passphrase.encode("utf-8"),
        salt=encryption_salt,
        n=16384, r=8, p=1, dklen=32,
    )


def derive_per_obs_key(master_key: bytes, obs_id: str) -> bytes:
    """HKDF-derive a per-observation key from master."""
    return hkdf(
        ikm=master_key,
        salt=b"compass.v1.obs_key",
        info=obs_id.encode("utf-8"),
        length=32,
    )


# ---- AES-GCM (try cryptography lib · fallback PyNaCl · fallback raise) ----

def _aes_gcm_encrypt(key: bytes, plaintext: bytes, nonce: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).encrypt(nonce, plaintext, None)
    except ImportError:
        pass

    try:
        from nacl.secret import SecretBox
        # nacl uses XChaCha20-Poly1305 not AES-GCM · but it's E2EE-safe
        # Note: this changes the ciphertext format slightly (XChaCha vs AES)
        # We document this · if cryptography is installed it's used preferentially
        return SecretBox(key).encrypt(plaintext, nonce[:24].ljust(24, b"\x00")).ciphertext
    except ImportError:
        pass

    raise ImportError(
        "compass_crypto needs 'cryptography' or 'pynacl' installed.\n"
        "  pip install cryptography  # preferred (AES-256-GCM · standard)\n"
        "  pip install pynacl        # alternative (XChaCha20-Poly1305 · libsodium)"
    )


def _aes_gcm_decrypt(key: bytes, ciphertext: bytes, nonce: bytes) -> bytes:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        return AESGCM(key).decrypt(nonce, ciphertext, None)
    except ImportError:
        pass

    try:
        from nacl.secret import SecretBox
        return SecretBox(key).decrypt(nonce[:24].ljust(24, b"\x00") + ciphertext)
    except ImportError:
        pass

    raise ImportError("compass_crypto needs 'cryptography' or 'pynacl'")


def _has_aes_lib() -> bool:
    try:
        import cryptography  # noqa
        return True
    except ImportError:
        try:
            import nacl  # noqa
            return True
        except ImportError:
            return False


# ---- Public API ----

VERSION = "v1"


def encrypt_obs(master_key: bytes, obs_id: str, content: dict) -> str:
    """Encrypt observation content dict · return opaque base64 blob."""
    plaintext = json.dumps(content, ensure_ascii=False, sort_keys=True).encode("utf-8")
    per_obs_key = derive_per_obs_key(master_key, obs_id)
    nonce = secrets.token_bytes(12)
    ciphertext = _aes_gcm_encrypt(per_obs_key, plaintext, nonce)
    nonce_b64 = base64.urlsafe_b64encode(nonce).decode("ascii").rstrip("=")
    ct_b64 = base64.urlsafe_b64encode(ciphertext).decode("ascii").rstrip("=")
    return f"{VERSION}:{nonce_b64}:{ct_b64}"


def decrypt_obs(master_key: bytes, obs_id: str, blob: str) -> dict:
    """Decrypt blob produced by encrypt_obs · return dict."""
    parts = blob.split(":")
    if len(parts) != 3:
        raise ValueError(f"bad blob format · expected v:nonce:ct · got {len(parts)} parts")
    version, nonce_b64, ct_b64 = parts
    if version != VERSION:
        raise ValueError(f"unsupported encryption version: {version}")
    pad = "=" * (-len(nonce_b64) % 4)
    nonce = base64.urlsafe_b64decode(nonce_b64 + pad)
    pad = "=" * (-len(ct_b64) % 4)
    ciphertext = base64.urlsafe_b64decode(ct_b64 + pad)
    per_obs_key = derive_per_obs_key(master_key, obs_id)
    plaintext = _aes_gcm_decrypt(per_obs_key, ciphertext, nonce)
    return json.loads(plaintext.decode("utf-8"))


def generate_salt() -> bytes:
    """Server-side · 32 bytes random salt for new user."""
    return secrets.token_bytes(32)


# ---- Self-test ----

def selftest():
    print("=== compass v1.0 crypto selftest ===\n")

    if not _has_aes_lib():
        print("[SKIP] no cryptography / nacl installed")
        print("  pip install cryptography")
        return 1

    salt = generate_salt()
    passphrase = "correct horse battery staple"
    print(f"[1] generated salt: {salt.hex()[:32]}... ({len(salt)} bytes)")

    master = derive_master_key(passphrase, salt)
    master2 = derive_master_key(passphrase, salt)
    assert master == master2, "deterministic"
    assert len(master) == 32
    print(f"[2] master_key derived · 32 bytes · deterministic ✓")

    wrong_master = derive_master_key("wrong passphrase", salt)
    assert wrong_master != master
    print(f"[3] wrong passphrase → different key ✓")

    obs_id = "ob_test_abc123"
    content = {
        "name": "测试 obs · 中文",
        "description": "E2EE encryption test",
        "body": "Long body text · 中英混合 · multiple lines\nline 2\nline 3",
    }

    blob = encrypt_obs(master, obs_id, content)
    print(f"[4] encrypted blob: {blob[:60]}... ({len(blob)} chars)")

    decrypted = decrypt_obs(master, obs_id, blob)
    assert decrypted == content, f"roundtrip failed · {decrypted}"
    print(f"[5] roundtrip · plaintext matches ✓")

    # Wrong master key fails
    try:
        decrypt_obs(wrong_master, obs_id, blob)
        print(f"[FAIL] wrong master key should have failed")
        return 1
    except Exception as e:
        print(f"[6] wrong master_key → decryption fails ({type(e).__name__}) ✓")

    # Wrong obs_id fails (different per_obs_key)
    try:
        decrypt_obs(master, "ob_different", blob)
        print(f"[FAIL] wrong obs_id should have failed")
        return 1
    except Exception as e:
        print(f"[7] wrong obs_id → decryption fails ({type(e).__name__}) ✓")

    # Tamper test · flip 1 bit in ciphertext
    parts = blob.split(":")
    pad = "=" * (-len(parts[2]) % 4)
    ct = bytearray(base64.urlsafe_b64decode(parts[2] + pad))
    ct[0] ^= 0x01
    tampered_ct_b64 = base64.urlsafe_b64encode(bytes(ct)).decode("ascii").rstrip("=")
    tampered_blob = f"{parts[0]}:{parts[1]}:{tampered_ct_b64}"
    try:
        decrypt_obs(master, obs_id, tampered_blob)
        print(f"[FAIL] tampered ciphertext should have failed")
        return 1
    except Exception as e:
        print(f"[8] tampered ciphertext → AEAD detects ({type(e).__name__}) ✓")

    print(f"\n=== ALL PASSED · E2EE crypto v1.0 ready ===")
    return 0


if __name__ == "__main__":
    sys.exit(selftest())
