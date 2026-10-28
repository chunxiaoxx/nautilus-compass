"""R5 constitution lock smoke test · 验证 hash + verify_locks 流程"""
from __future__ import annotations
import pytest
from pathlib import Path
from nautilus_core import constitution as cst


def test_compute_locks_returns_sha256():
    locks = cst.compute_locks()
    assert isinstance(locks, dict)
    for fname, digest in locks.items():
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)


def test_verify_locks_strict_false_no_raise(tmp_path, monkeypatch):
    """没有 lock 文件时 strict=False 只返报告 不 raise"""
    monkeypatch.setattr(cst, "LOCKS_DIR", tmp_path / "empty")
    report = cst.verify_locks(strict=False)
    assert isinstance(report, dict)
    for fname in cst.LOCKED_FILES:
        if (cst.CORE_DIR / fname).exists():
            assert fname in report


def test_verify_locks_strict_true_raises_on_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(cst, "LOCKS_DIR", tmp_path / "empty")
    with pytest.raises(cst.ConstitutionViolation):
        cst.verify_locks(strict=True)


def test_round_trip_write_then_verify(tmp_path, monkeypatch):
    """写 lock → verify_locks 应全 OK"""
    monkeypatch.setattr(cst, "LOCKS_DIR", tmp_path)
    locks = cst.compute_locks()
    cst.write_locks(locks, target=tmp_path)
    report = cst.verify_locks(strict=True)
    for fname, (exp, act, match) in report.items():
        if (cst.CORE_DIR / fname).exists():
            assert match, f"{fname} mismatch after round trip"


def test_mismatch_raises(tmp_path, monkeypatch):
    """写假 lock → verify_locks strict=True 应 raise"""
    monkeypatch.setattr(cst, "LOCKS_DIR", tmp_path)
    fake_locks = {f: "0" * 64 for f in cst.LOCKED_FILES if (cst.CORE_DIR / f).exists()}
    cst.write_locks(fake_locks, target=tmp_path)
    with pytest.raises(cst.ConstitutionViolation):
        cst.verify_locks(strict=True)
