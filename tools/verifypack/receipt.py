"""receipt:回执构建与 ed25519 签名/验签(SPEC §7)。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import ed25519
from .seal import canonical_json, sha256_bytes
from .spec import BOUNDARY, RECEIPT_VERSION


def build_receipt(pack_name: str, pack_dir: Path, verifier: str,
                  results: list[dict], environment: str) -> dict:
    """verify 结果 → receipt dict(未签名)。pack_manifest_hash 绑定 seal。"""
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("pack not sealed (manifest.json missing)")
    counts = {"agree": 0, "disagree": 0, "degraded": 0, "seal_fail": 0}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    return {
        "receipt_version": RECEIPT_VERSION,
        "pack": pack_name,
        "pack_manifest_hash": sha256_bytes(manifest_path.read_bytes()),
        "verifier": verifier,
        "verified_at": datetime.now().isoformat(timespec="seconds"),
        "environment": environment,
        "results": results,
        "summary": counts,
        "boundary": BOUNDARY,
    }


def sign_receipt(receipt_path: Path, key_path: Path) -> Path:
    """对 receipt.json 签名,落 receipt.sig(64B hex)。返回 sig 路径。"""
    seed = bytes.fromhex(key_path.read_text(encoding="utf-8").strip())
    if len(seed) != 32:
        raise ValueError(f"key file must contain 32-byte hex seed: {key_path}")
    sig = ed25519.sign(canonical_json(json.loads(receipt_path.read_text(encoding="utf-8"))), seed)
    sig_path = receipt_path.with_suffix(".sig")
    sig_path.write_text(sig.hex(), encoding="utf-8", newline="\n")
    return sig_path


def check_receipt(pack_dir: Path, receipt_path: Path, pubkey_hex: str,
                  sig_path: Path | None = None) -> dict:
    """结算方验签 + manifest 哈希绑定核对(不重算)。返回诊断 dict。"""
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    sig_path = sig_path or receipt_path.with_suffix(".sig")
    if not sig_path.is_file():
        return {"ok": False, "reason": "signature file missing"}
    try:
        sig = bytes.fromhex(sig_path.read_text(encoding="utf-8").strip())
        if isinstance(pubkey_hex, (bytes, bytearray)):
            pubkey_hex = pubkey_hex.hex()
        ok = ed25519.verify(sig, canonical_json(receipt), bytes.fromhex(pubkey_hex))
    except ValueError:
        return {"ok": False, "reason": "malformed signature or pubkey"}
    if not ok:
        return {"ok": False, "reason": "signature INVALID (receipt modified or wrong pubkey)"}
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "reason": "pack manifest missing"}
    mh = sha256_bytes(manifest_path.read_bytes())
    if receipt.get("pack_manifest_hash") != mh:
        return {"ok": False, "reason": "pack manifest hash mismatch (pack changed after verify)"}
    from . import seal as _seal
    seal_ok, violations = _seal.verify_seal(pack_dir)
    if not seal_ok:
        return {"ok": False,
                "reason": f"pack seal broken: {'; '.join(violations[:3])}"}
    if receipt.get("boundary") != BOUNDARY:
        return {"ok": False, "reason": "boundary clause altered"}
    return {"ok": True, "pack": receipt.get("pack"), "summary": receipt.get("summary"),
            "verified_at": receipt.get("verified_at"), "verifier": receipt.get("verifier")}
