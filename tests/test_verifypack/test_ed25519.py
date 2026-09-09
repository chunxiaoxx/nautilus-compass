"""ed25519 纯实现测试:性质断言 + 与 cryptography 库交叉验证(有则测,无则跳)。"""
import pytest

from tools.verifypack import ed25519


def test_sign_verify_roundtrip():
    seed, pub = ed25519.keypair()
    msg = b"receipt canonical bytes"
    sig = ed25519.sign(msg, seed, pub)
    assert len(sig) == 64
    assert ed25519.verify(sig, msg, pub)


def test_deterministic_signature():
    seed = bytes(range(32))
    msg = b"same message"
    assert ed25519.sign(msg, seed) == ed25519.sign(msg, seed)


def test_tampered_message_fails():
    seed, pub = ed25519.keypair()
    sig = ed25519.sign(b"claim A", seed, pub)
    assert not ed25519.verify(sig, b"claim B", pub)


def test_tampered_sig_fails():
    seed, pub = ed25519.keypair()
    sig = bytearray(ed25519.sign(b"m", seed, pub))
    sig[0] ^= 0xFF
    assert not ed25519.verify(bytes(sig), b"m", pub)


def test_wrong_pubkey_fails():
    seed, _pub = ed25519.keypair()
    _s2, pub2 = ed25519.keypair()
    sig = ed25519.sign(b"m", seed)
    assert not ed25519.verify(sig, b"m", pub2)


def test_malformed_lengths_rejected():
    seed, pub = ed25519.keypair()
    assert not ed25519.verify(b"short", b"m", pub)
    assert not ed25519.verify(b"x" * 64, b"m", b"tooshort")


def test_publickey_deterministic():
    seed = b"\x01" * 32
    assert ed25519.publickey(seed) == ed25519.publickey(seed)
    assert len(ed25519.publickey(seed)) == 32


def test_cross_check_with_cryptography_lib():
    """交叉验证自实现的互操作正确性(仅当环境装了 cryptography)。"""
    cryptography = pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    seed, pub = ed25519.keypair()
    msg = b"interop check"

    # 我方 sign → cryptography verify
    priv = Ed25519PrivateKey.from_private_bytes(seed)
    assert priv.public_key().public_bytes_raw() == pub
    priv.public_key().verify(ed25519.sign(msg, seed, pub), msg)

    # cryptography sign → 我方 verify
    their_sig = priv.sign(msg)
    assert ed25519.verify(their_sig, msg, pub)
