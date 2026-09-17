"""export:回执+pack → verdict 语料 JSONL(燃料层导出器,SPEC §8)。"""
import json

import pytest

from tools.verifypack import cli

REQUIRED = ("trace", "claim_id", "criteria_ref", "payload_hash",
            "verdict", "signed_at", "pubkey_fp")


def _run(*argv):
    return cli.main(list(argv))


@pytest.fixture()
def signed_pack(tmp_path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "payload.json").write_text(json.dumps({
        "episodes": [
            {"name": "e1", "frames_written": 100, "frames_decoded": 100, "rc": 0},
            {"name": "e2", "frames_written": 100, "frames_decoded": 100, "rc": 0},
        ]}), encoding="utf-8")
    spec_doc = {"pack": {
        "pack": "corpus_pack", "protocol_version": "verifypack-0.2", "inputs": [],
        "claims": [
            {"id": "d2", "statement": "帧完整率(锚引用 anchor-pool-selection-bias-v1@catalog-v0)",
             "level": "L1", "value": 1.0,
             "checks": {"primary": {"kind": "aggregate",
                                    "from": "payload/payload.json#episodes",
                                    "num": "sum(frames_written)",
                                    "den": "sum(frames_decoded)",
                                    "op": "ratio_eq"}}},
            {"id": "d3", "statement": "轨迹完整率(无判据引用的普通声明)",
             "level": "L1", "value": 1.0,
             "checks": {"primary": {"kind": "aggregate",
                                    "from": "payload/payload.json#episodes",
                                    "num": "count(rc == 0)", "den": "count()",
                                    "op": "value_eq"}}},
        ]},
        "files": {"payload/payload.json": str(src / "payload.json")}}
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec_doc, ensure_ascii=False), encoding="utf-8")
    pack = tmp_path / "out"
    assert _run("build", "--spec", str(sp), "--out", str(pack)) == 0

    keydir = tmp_path / "keys"
    assert _run("keygen", "--out-dir", str(keydir), "--name", "v") == 0
    monkeypatch.delenv("VERIFYPACK_KEY", raising=False)
    assert _run("verify", str(pack), "--key", str(keydir / "v.key")) == 0
    pub = (keydir / "v.pub").read_text(encoding="utf-8").strip()
    return pack, pub, tmp_path


def test_export_rows_and_manifest(signed_pack):
    pack, pub, tmp = signed_pack
    out = tmp / "corpus.jsonl"
    rc = _run("export", str(pack), "--out", str(out),
              "--trace", "flywheel-c-family-b1-built-20260916", "--pubkey", pub)
    assert rc == 0

    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    rows = [json.loads(x) for x in lines]
    for row in rows:
        for k in REQUIRED:
            assert k in row, f"missing field {k}"
        assert row["payload_hash"] == json.loads(
            (pack / "receipts" / "receipt.json").read_text(encoding="utf-8")
        )["pack_manifest_hash"]
        assert row["verdict"] == "agree"
        assert row["signed_at"]  # receipt.verified_at
        assert row["pubkey_fp"] == f"{pub[:8]}…{pub[-6:]}"

    by_id = {r["claim_id"]: r for r in rows}
    assert by_id["d2"]["criteria_ref"] == ["anchor-pool-selection-bias-v1@catalog-v0"]
    assert by_id["d3"]["criteria_ref"] == []
    assert all(r["trace"] == "flywheel-c-family-b1-built-20260916" for r in rows)

    m = json.loads((tmp / "corpus.manifest.json").read_text(encoding="utf-8"))
    assert m["rows_total"] == 2
    assert m["schema"] == "verdict-corpus-v0"
    assert m["packs"][0]["signature_ok"] is True
    assert m["packs"][0]["pack"] == "corpus_pack"


def test_export_unsigned_receipt(signed_pack):
    pack, _pub, tmp = signed_pack
    (pack / "receipts" / "receipt.sig").unlink()  # 剥签名:语料仍可导,但标未验签
    out = tmp / "corpus2.jsonl"
    assert _run("export", str(pack), "--out", str(out), "--trace", "t") == 0
    rows = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert all(r["pubkey_fp"] is None for r in rows)
    m = json.loads((tmp / "corpus2.manifest.json").read_text(encoding="utf-8"))
    assert m["packs"][0]["signature_ok"] is False


def test_export_missing_receipt_fails(tmp_path, monkeypatch):
    src = tmp_path / "s"
    src.mkdir()
    (src / "payload.json").write_text("{}", encoding="utf-8")
    spec_doc = {"pack": {"pack": "p", "protocol_version": "verifypack-0.2", "inputs": [],
                         "claims": [{"id": "x", "level": "L1", "value": 1,
                                     "checks": {"kind": "aggregate", "from": "a#b",
                                                "num": "count()", "op": "value_eq"}}]},
                "files": {"payload/a.json": str(src / "payload.json")}}
    sp = tmp_path / "spec.json"
    sp.write_text(json.dumps(spec_doc), encoding="utf-8")
    pack = tmp_path / "out"
    assert _run("build", "--spec", str(sp), "--out", str(pack)) == 0
    monkeypatch.delenv("VERIFYPACK_KEY", raising=False)
    assert _run("export", str(pack), "--out", str(tmp_path / "c.jsonl"),
                "--trace", "t") == 1


def test_export_deterministic(signed_pack):
    pack, pub, tmp = signed_pack
    a, b = tmp / "a.jsonl", tmp / "b.jsonl"
    _run("export", str(pack), "--out", str(a), "--trace", "t", "--pubkey", pub)
    _run("export", str(pack), "--out", str(b), "--trace", "t", "--pubkey", pub)
    assert a.read_bytes() == b.read_bytes()  # 行内容零时间戳,可复现
