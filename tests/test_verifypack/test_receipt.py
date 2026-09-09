"""receipt 签名/验签测试。"""
import json

import pytest

from tools.verifypack import ed25519, receipt, seal


@pytest.fixture()
def pack_dir(tmp_path):
    d = tmp_path / "pack"
    d.mkdir()
    (d / "pack.json").write_text('{"pack": "p1"}', encoding="utf-8")
    seal.write_manifest(d)
    return d


@pytest.fixture()
def keys(tmp_path):
    seed = bytes(range(32))
    pub = ed25519.publickey(seed)
    kp = tmp_path / "v.key"
    kp.write_text(seed.hex(), encoding="utf-8")
    return kp, pub


def _make_receipt(pack_dir, verifier="compass"):
    return receipt.build_receipt(
        "p1", pack_dir, verifier,
        [{"id": "c1", "level": "L1", "verdict": "agree", "recomputed": "1.0", "claimed": "1.0"}],
        "test env")


def test_sign_and_check_ok(pack_dir, keys, tmp_path):
    kp, pub = keys
    rec = _make_receipt(pack_dir)
    rp = tmp_path / "receipt.json"
    rp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    receipt.sign_receipt(rp, kp)
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert diag["ok"], diag
    assert diag["summary"]["agree"] == 1


def test_tampered_receipt_rejected(pack_dir, keys, tmp_path):
    kp, pub = keys
    rec = _make_receipt(pack_dir)
    rp = tmp_path / "receipt.json"
    rp.write_text(json.dumps(rec), encoding="utf-8")
    receipt.sign_receipt(rp, kp)
    rec["summary"]["agree"] = 99  # 篡改结论
    rp.write_text(json.dumps(rec), encoding="utf-8")
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert not diag["ok"] and "INVALID" in diag["reason"]


def test_modified_pack_after_verify_rejected(pack_dir, keys, tmp_path):
    kp, pub = keys
    rec = _make_receipt(pack_dir)
    rp = tmp_path / "receipt.json"
    rp.write_text(json.dumps(rec), encoding="utf-8")
    receipt.sign_receipt(rp, kp)
    (pack_dir / "pack.json").write_text('{"pack": "p1-changed"}', encoding="utf-8")
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert not diag["ok"]
    assert "mismatch" in diag["reason"] or "seal broken" in diag["reason"]


def test_boundary_clause_alteration_rejected(pack_dir, keys, tmp_path):
    kp, pub = keys
    rec = _make_receipt(pack_dir)
    rec["boundary"] = "可以做结算决定"  # 有人想改宪法
    rp = tmp_path / "receipt.json"
    rp.write_text(json.dumps(rec), encoding="utf-8")
    receipt.sign_receipt(rp, kp)
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert not diag["ok"] and "boundary" in diag["reason"]


def test_wrong_pubkey_rejected(pack_dir, keys, tmp_path):
    _kp, pub = keys
    other = ed25519.publickey(bytes(range(64, 96)))
    rec = _make_receipt(pack_dir)
    rp = tmp_path / "receipt.json"
    rp.write_text(json.dumps(rec), encoding="utf-8")
    receipt.sign_receipt(rp, tmp_path / "v.key")
    diag = receipt.check_receipt(pack_dir, rp, other)
    assert not diag["ok"]


def test_missing_sig_rejected(pack_dir, keys, tmp_path):
    _kp, pub = keys
    rp = tmp_path / "receipt.json"
    rp.write_text(json.dumps(_make_receipt(pack_dir)), encoding="utf-8")
    assert not receipt.check_receipt(pack_dir, rp, pub)["ok"]


def test_summary_counts(pack_dir):
    rec = receipt.build_receipt("p", pack_dir, "compass", [
        {"id": "a", "level": "L1", "verdict": "agree", "recomputed": "", "claimed": ""},
        {"id": "b", "level": "L2", "verdict": "degraded", "recomputed": "", "claimed": ""},
        {"id": "c", "level": "L1", "verdict": "disagree", "recomputed": "", "claimed": ""},
    ], "env")
    assert rec["summary"] == {"agree": 1, "disagree": 1, "degraded": 1, "seal_fail": 0}
    assert rec["boundary"]  # 宪法边界自动写入
