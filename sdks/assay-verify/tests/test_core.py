# -*- coding: utf-8 -*-
"""assay-verify SDK 测试:往返 + 跨实现兼容(验 compass 已发真成绩单)+ 三态。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assay_verify import verify, attest, keygen  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def test_roundtrip_and_tamper(tmp_path):
    t = tmp_path / "claims.md"
    t.write_text("# claims\naccuracy 0.91\n", encoding="utf-8")
    kp = keygen(tmp_path / "k")
    pub = (tmp_path / "k.pub").read_text(encoding="utf-8").strip()
    sig = attest(t, kp)
    r = verify(t, sig, pub)
    assert r.ok and r.detail == "VALID"
    t.write_text("# claims tampered\n", encoding="utf-8")
    r2 = verify(t, sig, pub)
    assert not r2.ok and "INVALID" in r2.detail


def test_malformed_missing(tmp_path):
    r = verify(tmp_path / "nope.md", tmp_path / "nope.sig", "00" * 32)
    assert not r.ok and "MALFORMED" in r.detail


def test_custom_payload_roundtrip(tmp_path):
    t = tmp_path / "run.log"
    t.write_text("bench output ...\n", encoding="utf-8")
    kp = keygen(tmp_path / "k2")
    pub = (tmp_path / "k2.pub").read_text(encoding="utf-8").strip()
    pay = {"agent": "demo-bot", "benchmark": "swe-x", "score": 0.83,
           "sha256": "deadbeef"}
    sig = attest(t, kp, payload=pay)
    assert verify(t, sig, pub, payload=pay).ok
    assert not verify(t, sig, pub).ok  # payload 不匹配→INVALID


def test_backward_compat_real_scorecards():
    """跨实现兼容证明:必须能验 compass 主仓已发布的两张真成绩单。"""
    pub = (ROOT / ".verifypack" / "compass.pub").read_text(encoding="utf-8").strip()
    for name in ("EXAM5_SCORECARD.md", "EXAM5_SCORECARD_RETAKE1.md"):
        t = ROOT / "docs" / "wall" / name
        s = ROOT / "docs" / "wall" / (name.replace(".md", ".sig"))
        r = verify(t, s, pub)
        assert r.ok, f"{name}: {r.detail}"
