from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from platform_protocol.keys import (
    ED25519_V1,
    encode_ed25519_public_key,
    encode_ed25519_signature,
    verify_ed25519_v1,
)


def test_ed25519_v1_uses_canonical_public_key_and_signature_encodings() -> None:
    private_key = Ed25519PrivateKey.generate()
    payload = b"protocol-v2-canonical-payload"

    public_key_material = encode_ed25519_public_key(private_key.public_key())
    signature = encode_ed25519_signature(private_key.sign(payload))

    assert public_key_material.startswith(f"{ED25519_V1}:")
    assert "=" not in public_key_material
    assert signature.startswith("sig_")
    assert "=" not in signature
    assert verify_ed25519_v1(public_key_material, payload, signature) is True


def test_ed25519_v1_fails_closed_for_unknown_encoding_bad_signature_and_tampering() -> (
    None
):
    private_key = Ed25519PrivateKey.generate()
    payload = b"protocol-v2-canonical-payload"
    public_key_material = encode_ed25519_public_key(private_key.public_key())
    signature = encode_ed25519_signature(private_key.sign(payload))

    assert verify_ed25519_v1("rsa-v1:invalid", payload, signature) is False
    assert verify_ed25519_v1(public_key_material, payload, "sig_" + "A" * 85) is False
    assert verify_ed25519_v1(public_key_material, payload, f"{signature}=") is False
    assert (
        verify_ed25519_v1(public_key_material, payload + b"-tampered", signature)
        is False
    )
