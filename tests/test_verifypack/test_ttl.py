"""receipt TTL + subject(T8 指纹)+ 续验链(SPEC v0.3 §R)测试。

LE 收敛:90 天续期 ↔ 持续适航订阅是同一结构——valid_until 过 = EXPIRED(UNVERIFIABLE
直至续验);subject 漂移 = 回执不再适用;replaces = 续验链前驱锚。
"""
import json
from datetime import date, timedelta

import pytest

from tools.verifypack import ed25519, receipt, seal

SUBJECT = {"pubkey_fp": "f7554b87", "code_hash": "ab" * 32, "config_hash": "cd" * 32}


@pytest.fixture()
def pack_dir(tmp_path):
    d = tmp_path / "pack"
    d.mkdir()
    (d / "pack.json").write_text(json.dumps({"pack": "p1", "subject": SUBJECT}), encoding="utf-8")
    seal.write_manifest(d)
    return d


@pytest.fixture()
def keys(tmp_path):
    seed = bytes(range(32))
    pub = ed25519.publickey(seed)
    kp = tmp_path / "v.key"
    kp.write_text(seed.hex(), encoding="utf-8")
    return kp, pub


def _results():
    return [{"id": "c1", "level": "L1", "verdict": "agree", "recomputed": "1.0", "claimed": "1.0"}]


def _signed_receipt(pack_dir, keys, tmp_path, **kw):
    kp, pub = keys
    rec = receipt.build_receipt("p1", pack_dir, "compass", _results(), "test env", **kw)
    rp = tmp_path / "receipt.json"
    rp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    receipt.sign_receipt(rp, kp)
    return rp, pub, rec


def test_subject_and_ttl_fields(pack_dir):
    rec = receipt.build_receipt("p1", pack_dir, "compass", _results(), "env",
                                subject=SUBJECT, ttl_days=90)
    assert rec["receipt_version"] == "0.3"
    assert rec["subject"] == SUBJECT
    assert rec["subject_fp"]
    expect = (date.today() + timedelta(days=90)).isoformat()
    assert rec["valid_until"] == expect


def test_legacy_receipt_stays_v02(pack_dir):
    rec = receipt.build_receipt("p1", pack_dir, "compass", _results(), "env")
    assert rec["receipt_version"] == "0.2"
    assert "subject" not in rec and "valid_until" not in rec


def test_check_valid_within_ttl(pack_dir, keys, tmp_path):
    rp, pub, rec = _signed_receipt(pack_dir, keys, tmp_path, subject=SUBJECT, ttl_days=90)
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert diag["ok"], diag
    assert diag.get("status") == "VALID"


def test_check_expired_after_ttl(pack_dir, keys, tmp_path):
    rp, pub, rec = _signed_receipt(pack_dir, keys, tmp_path, subject=SUBJECT, ttl_days=-1)
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert not diag["ok"]
    assert diag.get("status") == "EXPIRED"
    assert "valid_until" in diag["reason"]


def test_subject_mismatch_rejected(pack_dir, keys, tmp_path):
    """回执携带的 subject ≠ 包声明(验证器侧错配):签名有效但元数据不一致。"""
    drifted = dict(SUBJECT, code_hash="ef" * 32)
    rp, pub, rec = _signed_receipt(pack_dir, keys, tmp_path, subject=drifted, ttl_days=90)
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert not diag["ok"]
    assert "subject" in diag["reason"]


def test_legacy_receipt_on_subject_pack_no_drift(pack_dir, keys, tmp_path):
    """v0.2 回执(无 subject)对声明了 subject 的包:签名与 seal 仍有效,不判漂移。"""
    rp, pub, rec = _signed_receipt(pack_dir, keys, tmp_path)
    diag = receipt.check_receipt(pack_dir, rp, pub)
    assert diag["ok"], diag


def test_renewal_chain_field(pack_dir, keys, tmp_path):
    old_rp, pub, _ = _signed_receipt(pack_dir, keys, tmp_path, subject=SUBJECT, ttl_days=-1)
    import hashlib
    replaces = hashlib.sha256(old_rp.read_bytes()).hexdigest()
    rp2 = tmp_path / "receipt2.json"
    rec2 = receipt.build_receipt("p1", pack_dir, "compass", _results(), "env",
                                 subject=SUBJECT, ttl_days=90, replaces=replaces)
    rp2.write_text(json.dumps(rec2, ensure_ascii=False, indent=1), encoding="utf-8")
    receipt.sign_receipt(rp2, keys[0])
    diag = receipt.check_receipt(pack_dir, rp2, pub)
    assert diag["ok"], diag
    assert diag.get("chain_replaces") == replaces


# ── spec:pack.json subject 校验 ──

def test_spec_subject_validation():
    from tools.verifypack import spec
    spec.validate_subject(SUBJECT)
    with pytest.raises(spec.SpecError):
        spec.validate_subject({})  # 三元组至少一员
    with pytest.raises(spec.SpecError):
        spec.validate_subject({"code_hash": 123})  # 非字符串
