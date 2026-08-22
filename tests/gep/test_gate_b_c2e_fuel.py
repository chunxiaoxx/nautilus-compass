"""Gate B real-fuel spec: compass_exp_c2e (open() default codepage → explicit UTF-8).

Fuel provenance: cloud /home/ubuntu/auto-mint/fuel/c2e_read_encoding_default_codepage/
(task_spec.md + buggy_read.py + deterministic bench_eval.py G1/G2/G3),
first consumed via fde_admission_ledger grant e6fb8a43 (2026-08-22).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gep.live_coding_adapter import (
    LiveCodingError,
    _valid_c2e_source_rule,
    _valid_c2e_transfer_fix,
    load_value_suite,
)

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite_c2e_fuel_v1.json"


class TestC2eSourceRule:
    def test_accepts_explicit_lock_rule(self) -> None:
        assert _valid_c2e_source_rule(
            "Always pass encoding='utf-8' to open(); the platform default "
            "encoding depends on locale and mojibake-corrupts UTF-8 content."
        )

    def test_rejects_vague_answer(self) -> None:
        assert not _valid_c2e_source_rule("just fix the file reading bug")

    def test_rejects_wrong_encoding(self) -> None:
        assert not _valid_c2e_source_rule(
            "use encoding='latin-1' so the default locale never raises"
        )

    def test_rejects_non_string(self) -> None:
        assert not _valid_c2e_source_rule(None)


class TestC2eTransferFix:
    def test_accepts_open_with_utf8(self) -> None:
        assert _valid_c2e_transfer_fix("open(path, encoding='utf-8').read()")

    def test_accepts_bytes_decode(self) -> None:
        assert _valid_c2e_transfer_fix("open(path, 'rb').read().decode('utf-8')")

    def test_accepts_read_text(self) -> None:
        assert _valid_c2e_transfer_fix("Path(path).read_text(encoding='utf-8')")

    def test_rejects_bare_open(self) -> None:
        assert not _valid_c2e_transfer_fix("open(path).read()")

    def test_rejects_wrong_encoding_kw(self) -> None:
        assert not _valid_c2e_transfer_fix("open(path, encoding='gbk').read()")

    def test_rejects_non_expression(self) -> None:
        assert not _valid_c2e_transfer_fix("def read(p): return open(p).read()")

    def test_rejects_non_string(self) -> None:
        assert not _valid_c2e_transfer_fix(123)


class TestC2eSuiteLoads:
    def test_suite_parses_and_binds_registered_oracle(self) -> None:
        suite = load_value_suite(SUITE)
        assert suite.suite_id == "compass-exp-c2e-encoding-v1"
        cases = suite.loop_plan["task"]["cases"]
        assert cases["source"]["prompt"].strip()
        assert cases["transfer"]["prompt"].strip()

    def test_unregistered_oracle_variant_is_rejected(self, tmp_path: Path) -> None:
        raw = json.loads(SUITE.read_text(encoding="utf-8"))
        raw["loop_plan"]["oracle"]["cases"]["source"]["expected"] = "tampered"
        body = {k: v for k, v in raw.items() if k != "suite_hash"}
        import hashlib

        raw["suite_hash"] = "sha256:" + hashlib.sha256(
            json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()
        tampered = tmp_path / "tampered.json"
        tampered.write_text(json.dumps(raw), encoding="utf-8")
        suite = load_value_suite(tampered)  # hash-consistent load still succeeds
        from gep.live_coding_adapter import GateBSoftwareVerifier

        with pytest.raises(LiveCodingError):
            GateBSoftwareVerifier(suite)  # oracle no longer matches the registered spec
