# -*- coding: utf-8 -*-
"""Signed receipts over decision logs — make your evidence independently
verifiable (Assay-compatible: canonical JSON + ed25519 detached signature).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .ed25519 import keypair, pub_from_seed, sign, verify


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def log_payload(log_path) -> dict:
    """Receipt payload for a decision log: {log, sha256, n_records}."""
    p = Path(log_path)
    raw = p.read_bytes()
    n = raw.count(b"\n") if raw else 0
    return {"log": p.name, "sha256": hashlib.sha256(raw).hexdigest(),
            "n_records": n}


@dataclass
class ReceiptResult:
    ok: bool
    log: str
    sha256: str
    detail: str = ""

    def __bool__(self):
        return self.ok


class KeyPair:
    """An ed25519 key pair for signing decision logs. Generate once, keep the
    seed private, publish the pubkey hex next to any log you share."""

    def __init__(self, seed: bytes = None, pub: bytes = None):
        if seed is None and pub is None:
            seed, pub = keypair()
        if pub is None and seed is not None:
            pub = pub_from_seed(seed)
        self.seed = seed
        self.pub = pub

    @classmethod
    def from_hex(cls, seed_hex: str) -> "KeyPair":
        seed = bytes.fromhex(seed_hex.strip())
        if len(seed) != 32:
            raise ValueError("seed must be 32-byte hex")
        return cls(seed=seed)

    @property
    def pub_hex(self) -> str:
        return self.pub.hex()

    def sign_log(self, log_path) -> Path:
        """Write <log>.sig next to the log. Returns the signature path."""
        payload = log_payload(log_path)
        sig = sign(canonical_json(payload).encode("utf-8"), self.seed)
        sig_path = Path(str(log_path) + ".sig")
        sig_path.write_text(sig.hex(), encoding="utf-8", newline="\n")
        return sig_path

    def verify_log(self, log_path, sig_path) -> ReceiptResult:
        p, s = Path(log_path), Path(sig_path)
        if not p.is_file():
            return ReceiptResult(False, str(p), "", "log missing")
        if not s.is_file():
            return ReceiptResult(False, str(p), "", "signature file missing")
        try:
            sig = bytes.fromhex(s.read_text(encoding="utf-8").strip())
        except ValueError as e:
            return ReceiptResult(False, str(p), "", f"bad hex: {e}")
        payload = log_payload(p)
        ok = verify(self.pub, canonical_json(payload).encode("utf-8"), sig)
        return ReceiptResult(ok, str(p), payload["sha256"],
                             "VALID" if ok else "INVALID (signature mismatch)")


def verify_log(log_path, sig_path, pub_hex: str) -> ReceiptResult:
    """Anyone can verify a shared log+sig against a published pubkey."""
    return _verify_with_hex(log_path, sig_path, pub_hex)


def _verify_with_hex(log_path, sig_path, pub_hex: str) -> ReceiptResult:
    p, s = Path(log_path), Path(sig_path)
    try:
        pub = bytes.fromhex(str(pub_hex).strip())
    except ValueError as e:
        return ReceiptResult(False, str(p), "", f"bad pubkey hex: {e}")
    if len(pub) != 32:
        return ReceiptResult(False, str(p), "", "pubkey must be 32-byte hex")
    if not p.is_file():
        return ReceiptResult(False, str(p), "", "log missing")
    if not s.is_file():
        return ReceiptResult(False, str(p), "", "signature file missing")
    try:
        sig = bytes.fromhex(s.read_text(encoding="utf-8").strip())
    except ValueError as e:
        return ReceiptResult(False, str(p), "", f"bad sig hex: {e}")
    payload = log_payload(p)
    ok = verify(pub, canonical_json(payload).encode("utf-8"), sig)
    return ReceiptResult(ok, str(p), payload["sha256"],
                         "VALID" if ok else "INVALID (signature mismatch)")
