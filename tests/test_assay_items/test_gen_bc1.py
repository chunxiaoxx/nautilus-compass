# -*- coding: utf-8 -*-
"""BC1 出题生成器测试:确定性/判据引用/植入违例/切分。"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ALLOWED_CRITERIA = {
    "external-verified-provenance-v1@catalog-v0",
    "evidence-schema-v1@catalog-v0",
    "skip-label-fidelity-v1@catalog-v0",
    "anchor-pool-selection-bias-v1@catalog-v0",
    "judge-systematic-inconsistency-v1@catalog-v0",
    "verdict-recomputability-v1@catalog-v0",
}


def _run(*args):
    r = subprocess.run([sys.executable, "-m", "tools.assay_items.gen_bc1", *args],
                       cwd=ROOT, capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-300:]
    return r.stdout


def _gen(tmp, seed=7):
    out = Path(tmp) / "items.jsonl"
    _run("--all", "--seed", str(seed), "--n", "6", "--out", str(out))
    items = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    return items


def test_deterministic(tmp_path):
    a = _gen(tmp_path, seed=42)
    out2 = tmp_path / "again.jsonl"
    _run("--all", "--seed", "42", "--n", "6", "--out", str(out2))
    b = [json.loads(l) for l in out2.read_text(encoding="utf-8").splitlines()]
    assert a == b


def test_item_shape_and_criteria_refs(tmp_path):
    items = _gen(tmp_path)
    assert len(items) >= 12
    for it in items:
        for k in ("id", "dim", "type", "statement", "criteria_ref", "input", "expected", "check"):
            assert k in it, f"missing {k}"
        assert it["criteria_ref"] in ALLOWED_CRITERIA, it["criteria_ref"]
        assert it["check"] in ("json_map_equal", "script", "aggregate", "expr")
        assert it["id"].startswith("bc1:")


def test_t21_planted_violations_detected(tmp_path):
    items = [i for i in _gen(tmp_path) if i["type"] == "t2.1-gate-rows"]
    assert items
    it = items[0]
    rows = {r["row_id"]: r for r in it["input"]["rows"]}
    for rid, verdict in it["expected"]["gate"].items():
        r = rows[rid]
        if verdict == "reject":
            assert r["external_verified"] and not r.get("verifier"), \
                "被拒行必须是 ev=true 且无 verifier(生产者自置)"


def test_t41_criteria_mapping(tmp_path):
    items = [i for i in _gen(tmp_path) if i["type"] == "t4.1-stage-violation"]
    assert items
    it = items[0]
    rows = {r["row_id"]: r for r in it["input"]["chain"]}
    for rid, crit in it["expected"]["violations"].items():
        r = rows[rid]
        if crit == "evidence-schema-v1@catalog-v0":
            assert r["total_tokens"] == 0 and r["turn_usage_tokens"] > 0
        elif crit == "external-verified-provenance-v1@catalog-v0":
            assert r["external_verified"] and not r["verifier"]
        elif crit == "skip-label-fidelity-v1@catalog-v0":
            assert r["skip_label"] != r["rerun_outcome"]


def test_split_disjoint_and_manifest(tmp_path):
    out = tmp_path / "s.jsonl"
    _run("--all", "--seed", "9", "--n", "5", "--out", str(out),
         "--split", "60/40", "--split-prefix", str(tmp_path / "split"))
    ids = lambda p: [json.loads(l)["id"] for l in Path(p).read_text(encoding="utf-8").splitlines()]
    pub = ids(tmp_path / "split_public.jsonl")
    hold = ids(tmp_path / "split_holdout.jsonl")
    assert set(pub) & set(hold) == set()
    assert len(pub) + len(hold) == len(pub) + len(hold) > 0
    m = json.loads((tmp_path / "split_manifest.json").read_text(encoding="utf-8"))
    assert m["holdout_sha256"] and abs(m["public_pct"] - 60) < 26
