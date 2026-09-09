"""判据库 v0 测试:注册表合法性+gate 双向+与 VerifyPack 引擎端到端闭环。"""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tools.criteria import catalog as cat
from tools.verifypack import checks as vp_checks

ALLOWED_KINDS = {
    "aggregate", "file_hash", "file_hash_map",
    "group_count", "json_map_equal", "text_contains", "script",
}


def test_registry_nonempty_and_legal():
    cs = cat.all_criteria()
    assert len(cs) >= 4
    for c in cs:
        assert c.check_kind in ALLOWED_KINDS
        assert c.provenance, f"{c.cid} 缺实测背书引用"
        if c.gate is not None:
            assert c.gate["op"] in (">=", "<=")


def test_duplicate_registration_rejected():
    c = cat.get("D2")
    with pytest.raises(ValueError):
        cat.register(c)


def test_gate_both_directions():
    d2, c4 = cat.get("D2"), cat.get("C4")
    assert cat.eval_gate(d2, 0.999) is True          # 边界含等号
    assert cat.eval_gate(d2, 0.9985) is False        # 200 条实测最低 0.9127 应拒
    assert cat.eval_gate(c4, 0.04) is True
    assert cat.eval_gate(c4, 0.06) is False
    assert cat.eval_gate(cat.get("D4"), 1.0) is True
    assert cat.eval_gate(cat.get("D4"), 0.98) is False


def test_build_claim_shape():
    claim = cat.build_claim(cat.get("D2"), 0.9993, claim_id="D2@batch002")
    assert claim["id"] == "D2@batch002"
    assert claim["check"]["kind"] == "aggregate"
    assert claim["value"] == 0.9993
    assert claim["criterion"]["cid"] == "D2"
    assert "kind" not in claim["criterion"]  # kind 只在 check 里


def test_criterion_claim_runs_on_verifypack_engine(tmp_path):
    """端到端闭环:判据产出的 claim 能被现有 verify 引擎执行(可执行的证明)。"""
    rows = [{"ok": 1}] * 50
    (tmp_path / "meta_check.json").write_text(
        json.dumps({"rows": rows}), encoding="utf-8")
    pack = {"files": {}}
    c = cat.get("D4")
    claim = cat.build_claim(c, 1.0)
    out = vp_checks.run_check(pack, claim, claim["check"], tmp_path)
    assert out == {"ok": True, "recomputed": 1.0}
    # 复算不等 = 拒(即使数据方声称过门)
    claim_bad = cat.build_claim(c, 0.98)
    out_bad = vp_checks.run_check(pack, claim_bad, claim_bad["check"], tmp_path)
    assert out_bad["ok"] is False and out_bad["recomputed"] == 1.0


def test_invalid_gate_op_rejected():
    c = cat.Criterion(cid="T", layer="metric", title="t", check_kind="aggregate",
                      check_template={}, gate={"op": "==", "value": 1})
    with pytest.raises(ValueError):
        cat.eval_gate(c, 1.0)
