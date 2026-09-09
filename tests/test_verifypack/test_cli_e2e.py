"""CLI 端到端:build → verify → receipt(签名) → check 四连 + 篡改场景。"""
import json

import pytest

from tools.verifypack import cli


def _run(*argv):
    rc = cli.main(list(argv))
    return rc


@pytest.fixture()
def spec_and_out(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "payload.json").write_text(json.dumps({
        "episodes": [
            {"name": "e1", "frames_written": 100, "frames_decoded": 100, "rc": 0,
             "ratio": 0.99, "video_sha16": "s1"},
            {"name": "e2", "frames_written": 100, "frames_decoded": 100, "rc": 0,
             "ratio": 0.98, "video_sha16": "s1"},
        ]}), encoding="utf-8")
    (src / "report.md").write_text("# 报告\n帧完整率 1.0\n", encoding="utf-8")

    spec_doc = {
        "pack": {
            "pack": "e2e_pack",
            "protocol_version": "verifypack-0.2",
            "requested_by": "flywheel",
            "inputs": [],
            "claims": [
                {"id": "d2", "statement": "帧完整率", "level": "L1", "value": 1.0,
                 "checks": {"primary": {"kind": "aggregate",
                                        "from": "payload/payload.json#episodes",
                                        "num": "sum(frames_written)",
                                        "den": "sum(frames_decoded)",
                                        "op": "ratio_eq"}}},
                {"id": "d3", "statement": "轨迹完整率", "level": "L1", "value": 1.0,
                 "checks": {"primary": {"kind": "aggregate",
                                        "from": "payload/payload.json#episodes",
                                        "num": "count(rc == 0)", "den": "count()",
                                        "op": "value_eq"}}},
                {"id": "rep", "statement": "报告含数值", "level": "L1", "value": "report.md",
                 "checks": {"primary": {"kind": "text_contains", "file": "report.md",
                                        "needles": [{"claim": "d2"}]}}},
            ],
        },
        "files": {"payload/payload.json": str(src / "payload.json"),
                  "report.md": str(src / "report.md")},
    }
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec_doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return sp, tmp_path / "out", tmp_path


def test_full_pipeline(tmp_path, spec_and_out, monkeypatch):
    sp, out, tmp = spec_and_out
    assert _run("build", "--spec", str(sp), "--out", str(out)) == 0
    assert (out / "manifest.json").is_file()

    # keygen + verify(带签名)
    keydir = tmp / "keys"
    assert _run("keygen", "--out-dir", str(keydir), "--name", "v") == 0
    kp = keydir / "v.key"
    monkeypatch.delenv("VERIFYPACK_KEY", raising=False)
    assert _run("verify", str(out), "--key", str(kp)) == 0

    rec = out / "receipts" / "receipt.json"
    sig = out / "receipts" / "receipt.sig"
    assert rec.is_file() and sig.is_file()

    # check 验签(结算方)
    pub = (keydir / "v.pub").read_text(encoding="utf-8").strip()
    monkeypatch.delenv("VERIFYPACK_KEY", raising=False)
    assert _run("check", str(out), "--receipt", str(rec), "--pubkey", pub) == 0

    summary = json.loads(rec.read_text(encoding="utf-8"))["summary"]
    assert summary["agree"] == 3 and summary["disagree"] == 0


def test_disagree_exit_code(tmp_path, spec_and_out, monkeypatch):
    sp, out, tmp = spec_and_out
    _run("build", "--spec", str(sp), "--out", str(out))
    # 篡改 claim 值(build 前改 spec 才合理——这里直接改 pack.json 后 seal 会抓;
    # 正确场景:spec 里就写了错值 → disagree)
    spec_doc = json.loads(sp.read_text(encoding="utf-8"))
    spec_doc["pack"]["claims"][0]["value"] = 0.5
    sp.write_text(json.dumps(spec_doc), encoding="utf-8")
    out2 = tmp / "out2"
    _run("build", "--spec", str(sp), "--out", str(out2))
    monkeypatch.delenv("VERIFYPACK_KEY", raising=False)
    assert _run("verify", str(out2)) == 1  # disagree → rc 1
    rec = json.loads((out2 / "receipts" / "receipt.json").read_text(encoding="utf-8"))
    assert rec["summary"]["disagree"] == 1


def test_seal_fail_blocks_verify(tmp_path, spec_and_out, monkeypatch):
    sp, out, tmp = spec_and_out
    _run("build", "--spec", str(sp), "--out", str(out))
    # 活文件场景:seal 后 payload 被追写
    with open(out / "payload" / "payload.json", "a", encoding="utf-8") as f:
        f.write(" ")
    monkeypatch.delenv("VERIFYPACK_KEY", raising=False)
    rc = _run("verify", str(out))
    assert rc == 1
    rec = json.loads((out / "receipts" / "receipt.json").read_text(encoding="utf-8"))
    assert all(r["verdict"] == "seal_fail" for r in rec["results"])
    assert rec["summary"]["seal_fail"] == 3


def test_l2_degraded_without_env(tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    (src / "payload.json").write_text(json.dumps(
        {"rows": [{"name": "a", "ratio": 0.9}]}), encoding="utf-8")
    spec_doc = {"pack": {
        "pack": "l2pack", "protocol_version": "verifypack-0.2", "inputs": [],
        "claims": [{"id": "face", "statement": "人脸率", "level": "L2", "value": {"a": 0.9},
                    "checks": {
                        "primary": {"kind": "script", "repro": "repro/none.py",
                                    "requires_env": "qc"},
                        "fallback": {"kind": "json_map_equal", "file": "payload/payload.json",
                                     "path": "rows", "map_by": "name", "field": "ratio"}}}]},
        "files": {"payload/payload.json": str(src / "payload.json")}}
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec_doc, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out"
    assert _run("build", "--spec", str(sp), "--out", str(out)) == 0
    assert _run("verify", str(out)) == 0  # degraded 不算失败
    rec = json.loads((out / "receipts" / "receipt.json").read_text(encoding="utf-8"))
    assert rec["summary"]["degraded"] == 1
    assert rec["results"][0]["verdict"] == "degraded"


def test_build_rejects_missing_source(tmp_path):
    sp = tmp_path / "bad.json"
    sp.write_text(json.dumps({"pack": {"pack": "p", "protocol_version": "verifypack-0.2",
                                       "claims": [{"id": "x", "level": "L1", "value": 1,
                                                   "checks": {"kind": "aggregate",
                                                              "from": "a#b", "num": "count()",
                                                              "op": "value_eq"}}]},
                              "files": {"payload/a.json": str(tmp_path / "nope.json")}}),
                   encoding="utf-8")
    assert _run("build", "--spec", str(sp), "--out", str(tmp_path / "o")) == 1
