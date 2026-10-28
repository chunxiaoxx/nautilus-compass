import pytest

from services.fde_phase3_identity_service import SignedTokenCodec, SignedTokenError


def test_s0_oauth_state_enforces_purpose_expiry_and_signature():
    now = [1000]
    codec = SignedTokenCodec(b"x" * 32, clock=lambda: now[0])
    token = codec.encode("s0_oauth_state", {"invite": "opaque"}, 60)
    assert codec.decode(token, "s0_oauth_state")["invite"] == "opaque"
    with pytest.raises(SignedTokenError, match="wrong token purpose"):
        codec.decode(token, "session")
    body, signature = token.split(".")
    with pytest.raises(SignedTokenError, match="signature"):
        codec.decode(body + "." + signature[:-1] + "A", "s0_oauth_state")
    now[0] = 1061
    with pytest.raises(SignedTokenError, match="expired"):
        codec.decode(token, "s0_oauth_state")
