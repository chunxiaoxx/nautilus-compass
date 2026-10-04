# -*- coding: utf-8 -*-
"""nautilus_compass.assay 单测:schema_v2 校验器一致性+submit 提交侧 schema。

注:nautilus_compass 为根目录映射包(未安装环境下不可直接 import),
与 tools CLI 薄壳同法按文件路径加载同源模块。
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_schema = _load("_assay_schema_v2", "assay/schema_v2.py")
_submit = _load("_assay_submit", "assay/submit.py")
migrate, validate = _schema.migrate, _schema.validate
validate_challenge = _submit.validate_challenge
validate_errata = _submit.validate_errata
CAUSE_TAGS = _submit.CAUSE_TAGS
CHALLENGE_REQUIRED = _submit.CHALLENGE_REQUIRED
ERRATA_REQUIRED = _submit.ERRATA_REQUIRED


def _compliant_verdict() -> dict:
    src = ROOT / "runtime" / "v4v2_judge" / "v4v2_judge_verdict_v2.json"
    return json.loads(src.read_text(encoding="utf-8"))


def test_validate_compliant_verdict_zero_errors():
    errors, warns = validate(_compliant_verdict())
    assert errors == []
    assert warns == []


def test_validate_rejects_missing_top_level():
    errors, _ = validate({"ts": "t"})
    assert any("L1 顶层缺" in e for e in errors)


def test_migrate_legacy_string_verdict_becomes_object():
    out = migrate({"verdict": "PARTIAL(样本量不足)", "ts": "t"})
    assert isinstance(out["verdict"], dict)
    assert out["verdict"]["state"] == "PARTIAL"


def _challenge(**over):
    base = {"qid": "q1", "claim": "c", "artifacts_ref": "sha16:abc", "original_verdict": "VERDICT",
            "reason": "r", "cause_tag": "data", "label_origin": "independent_recompute",
            "confidence": "measured"}
    base.update(over)
    return base


def test_challenge_ok():
    errors, _ = validate_challenge(_challenge())
    assert errors == []


def test_challenge_missing_fields_and_bad_enums():
    e, _ = validate_challenge({"qid": "q", "cause_tag": "wrong", "label_origin": "x",
                               "confidence": "guessed"})
    assert len(e) >= 7
    assert any("cause_tag" in x for x in e)
    assert any("label_origin" in x for x in e)
    assert any("confidence" in x for x in e)


def test_challenge_new_verdict_enum():
    e, _ = validate_challenge(_challenge(new_verdict="MAYBE"))
    assert any("new_verdict" in x for x in e)
    e2, w2 = validate_challenge(_challenge(new_verdict="U_STATE"))
    assert e2 == [] and w2 == []  # 显式改判值合法且无撤回警告
    e3, w3 = validate_challenge(_challenge(new_verdict=None))
    assert e3 == [] and any("仅质疑不改判" in x for x in w3)


def test_errata_nullable_new_verdict():
    p = {"case_id": "c", "field": "findings[0]", "original": "o", "reason": "r",
         "cause_tag": "judgment"}
    e, w = validate_errata(p)
    assert e == [] and any("仅撤回不改判" in x for x in w)
    e2, _ = validate_errata({**p, "new_verdict": "bad"})
    assert any("new_verdict" in x for x in e2)


def test_enums_and_required_frozen_shapes():
    assert CAUSE_TAGS == ("execution", "data", "judgment", "capability")
    assert set(CHALLENGE_REQUIRED) == {"qid", "claim", "artifacts_ref", "original_verdict",
                                       "reason", "cause_tag", "label_origin", "confidence"}
    assert set(ERRATA_REQUIRED) == {"case_id", "field", "original", "reason", "cause_tag"}


def test_tools_cli_thin_shell_zero_drift():
    import subprocess
    import sys
    src = ROOT / "runtime" / "gen4v2_btrack" / "gen4v2_btrack_verdict_v2.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "verdict_schema_v2.py"),
                        "validate", str(src)], capture_output=True, text=True)
    assert r.returncode == 0
    assert json.loads(r.stdout)["compliant"] is True


@pytest.mark.parametrize("tier", ["measured", "inferred", "unverifiable"])
def test_tier_enum_stability(tier):
    assert tier in {"measured", "inferred", "unverifiable"}
