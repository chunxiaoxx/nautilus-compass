"""verdict 语料导出器:pack+回执 → JSONL(燃料层第一铲,SPEC §8)。

一行 = 一条 claim-verdict,唯一来源 = pack.json 声明 + receipts/receipt.json。
criteria_ref 从 statement 正文提取(锚引用纪律:声明文本是判据引用唯一来源)。
行内零时间戳(signed_at 取回执,exported_at 只进 sidecar)——同输入同输出。
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from . import receipt as receipt_mod
from . import spec

SCHEMA = "verdict-corpus-v0"
REQUIRED_FIELDS = ("trace", "claim_id", "criteria_ref", "payload_hash",
                   "verdict", "signed_at", "pubkey_fp")

# criteria:<id>@<catalog-vN> 显式形式 + <id>@catalog-vN 裸锚引用形式
_CRIT = re.compile(
    r"criteria:([A-Za-z0-9._-]+@[A-Za-z0-9.-]+)|([A-Za-z0-9-]+@catalog-v\d+)")


def extract_criteria_refs(text: str) -> list[str]:
    """从声明正文提取判据引用(保持出现顺序,去重)。"""
    found: list[str] = []
    for explicit, bare in _CRIT.findall(text or ""):
        if explicit or bare:
            found.append(explicit or bare)
    seen: set[str] = set()
    return [x for x in found if not (x in seen or seen.add(x))]


def pubkey_fp(pub: str) -> str | None:
    """公钥指纹:前 8…后 6(展示用;全量公钥随 sidecar 的 packs[].pubkey)。"""
    return f"{pub[:8]}…{pub[-6:]}" if pub and len(pub) >= 16 else None


def export_pack(pack_dir: Path, trace: str | None,
                pubkey_hex: str | None = None) -> tuple[list[dict], dict]:
    """单个 pack → (rows, meta)。无回执/包坏 → 抛异常,由调用方计失败。"""
    pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    spec.validate_pack(pack)

    rec_path = pack_dir / "receipts" / "receipt.json"
    if not rec_path.is_file():
        raise FileNotFoundError(f"receipt missing (run verify first): {pack_dir}")
    rec = json.loads(rec_path.read_text(encoding="utf-8"))

    sig_ok = False
    if pubkey_hex and rec_path.with_suffix(".sig").is_file():
        diag = receipt_mod.check_receipt(pack_dir, rec_path, pubkey_hex)
        sig_ok = bool(diag.get("ok"))

    results = {r["id"]: r for r in rec.get("results", [])}
    rows: list[dict] = []
    for claim in pack["claims"]:
        r = results.get(claim["id"])
        if r is None:
            continue  # 计入 meta.orphan_claims,不产出行
        rows.append({
            "schema": SCHEMA,
            "trace": trace,
            "pack": pack["pack"],
            "claim_id": claim["id"],
            "level": claim.get("level"),
            "criteria_ref": extract_criteria_refs(claim.get("statement", "")),
            "payload_hash": rec.get("pack_manifest_hash"),
            "verdict": r.get("verdict"),
            "recomputed": r.get("recomputed"),
            "claimed": r.get("claimed"),
            "verifier": rec.get("verifier"),
            "signed_at": rec.get("verified_at"),
            "pubkey_fp": pubkey_fp(pubkey_hex) if sig_ok else None,
        })

    claim_ids = {c["id"] for c in pack["claims"]}
    meta = {
        "pack": pack["pack"],
        "signature_ok": sig_ok,
        "rows": len(rows),
        "orphan_claims": [c["id"] for c in pack["claims"] if c["id"] not in results],
        "orphan_results": [i for i in results if i not in claim_ids],
        "pubkey": pubkey_hex,
    }
    return rows, meta


def write_corpus(rows: list[dict], out_path: Path, trace: str | None,
                 pack_metas: list[dict]) -> dict:
    """rows → <out>.jsonl + sidecar <out>.manifest.json(批次元数据+防篡改哈希)。"""
    payload = "".join(
        json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8", newline="\n")

    manifest = {
        "schema": SCHEMA,
        "trace": trace,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "rows_total": len(rows),
        "sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        "packs": pack_metas,
    }
    sidecar = out_path.with_suffix(".manifest.json")
    sidecar.write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                       encoding="utf-8", newline="\n")
    return manifest
