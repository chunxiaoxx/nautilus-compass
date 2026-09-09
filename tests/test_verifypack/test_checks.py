"""check 引擎七种 kind 测试(各含过/败例)。"""
import json

import pytest

from tools.verifypack import checks

ROWS = [
    {"name": "v1", "frames_written": 100, "frames_decoded": 100, "rc": 0,
     "ratio": 0.99, "video_sha16": "aa11", "video": "payload/v1.mp4"},
    {"name": "v2", "frames_written": 90, "frames_decoded": 100, "rc": 0,
     "ratio": 0.98, "video_sha16": "aa11", "video": "payload/v2.mp4"},
]


@pytest.fixture()
def pack_dir(tmp_path):
    d = tmp_path / "pack"
    (d / "payload").mkdir(parents=True)
    (d / "payload" / "payload.json").write_text(json.dumps({"episodes": ROWS}), encoding="utf-8")
    (d / "payload" / "v1.mp4").write_bytes(b"video-bytes-1")
    (d / "payload" / "v2.mp4").write_bytes(b"video-bytes-2")
    (d / "report.md").write_text("# report\n帧完整率 0.95\n轨迹 2/2\n", encoding="utf-8")
    return d


def test_aggregate_ratio(pack_dir):
    claim = {"id": "d2", "value": 0.95}
    check = {"kind": "aggregate", "from": "payload/payload.json#episodes",
             "num": "sum(frames_written)", "den": "sum(frames_decoded)",
             "op": "ratio_eq", "ndigits": 2}
    assert checks.run_check({}, claim, check, pack_dir)["ok"]
    claim_bad = {"id": "d2", "value": 0.11}
    assert not checks.run_check({}, claim_bad, check, pack_dir)["ok"]


def test_aggregate_with_filter(pack_dir):
    """D3 形态:rc==0 且 ratio>=0.98 的行占比。"""
    claim = {"id": "d3", "value": 1.0}
    check = {"kind": "aggregate", "from": "payload/payload.json#episodes",
             "filter": [{"field": "rc", "op": "==", "value": 0},
                        {"field": "ratio", "op": ">=", "value": 0.98}],
             "num": "count()", "den": "count()", "op": "ratio_eq"}
    assert checks.run_check({}, claim, check, pack_dir)["ok"]
    claim["value"] = 0.5
    assert not checks.run_check({}, claim, check, pack_dir)["ok"]
    check["filter"] = [{"field": "rc", "op": "!", "value": 0}]  # 非法 op
    with pytest.raises(Exception):
        checks.run_check({}, {"id": "x", "value": 1}, check, pack_dir)


def test_file_hash_map_from_rows(pack_dir):
    """行映射模式:名字字段→路径字段(视频哈希形态)。"""
    import hashlib
    m = {"v1": hashlib.sha256(b"video-bytes-1").hexdigest()[:16],
         "v2": hashlib.sha256(b"video-bytes-2").hexdigest()[:16]}
    claim = {"id": "vh", "value": m}
    check = {"kind": "file_hash_map", "algo": "sha256_16",
             "from": "payload/payload.json#episodes", "key": "name", "path": "video"}
    assert checks.run_check({}, claim, check, pack_dir)["ok"]
    claim["value"]["v1"] = "0" * 16
    assert not checks.run_check({}, claim, check, pack_dir)["ok"]


def test_file_hash(pack_dir):
    import hashlib
    expect = hashlib.sha256(b"video-bytes-1").hexdigest()[:16]
    claim = {"id": "fh", "value": expect}
    check = {"kind": "file_hash", "file": "payload/v1.mp4", "algo": "sha256_16",
             "expect": expect}
    assert checks.run_check({}, claim, check, pack_dir)["ok"]
    check["expect"] = "0" * 16
    assert not checks.run_check({}, claim, check, pack_dir)["ok"]


def test_file_hash_map(pack_dir):
    import hashlib
    m = {f"v{i}.mp4": hashlib.sha256(b).hexdigest()[:16]
         for i, b in ((1, b"video-bytes-1"), (2, b"video-bytes-2"))}
    claim = {"id": "vh", "value": m}
    check = {"kind": "file_hash_map", "algo": "sha256_16", "names_from": "claim",
             "dir": "payload"}
    r = checks.run_check({}, claim, check, pack_dir)
    assert r["ok"] and r["recomputed"] == m
    claim["value"]["v1.mp4"] = "0" * 16
    assert not checks.run_check({}, claim, check, pack_dir)["ok"]


def test_group_count(pack_dir):
    claim = {"id": "dup", "value": {"aa11": 2}}
    check = {"kind": "group_count", "from": "payload/payload.json#episodes",
             "by": "video_sha16", "min_group": 2, "expect_groups": 1}
    r = checks.run_check({}, claim, check, pack_dir)
    assert r["ok"] and r["recomputed"] == {"aa11": 2}
    check["expect_groups"] = 4
    assert not checks.run_check({}, claim, check, pack_dir)["ok"]


def test_json_map_equal(pack_dir):
    claim = {"id": "face", "value": {"v1": 0.99, "v2": 0.98}}
    check = {"kind": "json_map_equal", "file": "payload/payload.json",
             "path": "episodes", "map_by": "name", "field": "ratio"}
    assert checks.run_check({}, claim, check, pack_dir)["ok"]
    claim["value"]["v1"] = 0.5
    assert not checks.run_check({}, claim, check, pack_dir)["ok"]


def test_text_contains(pack_dir):
    claim = {"id": "c7", "value": "report.md"}
    check = {"kind": "text_contains", "file": "report.md",
             "needles": [{"value": "0.95"}, {"value": "2/2"}]}
    assert checks.run_check({}, claim, check, pack_dir)["ok"]
    check["needles"].append({"value": "not-in-report"})
    r = checks.run_check({}, claim, check, pack_dir)
    assert not r["ok"] and "not-in-report" in r["recomputed"]


def test_text_contains_claim_ref_needs_computed(pack_dir):
    check = {"kind": "text_contains", "file": "report.md",
             "needles": [{"claim": "d2"}]}
    with pytest.raises(checks.CheckError):
        checks.run_check({}, {"id": "c7", "value": "x"}, check, pack_dir, computed={})


def test_script_kind(tmp_path, pack_dir):
    (pack_dir / "repro").mkdir()
    (pack_dir / "repro" / "calc.py").write_text(
        'import json;print(json.dumps({"value": 42}))', encoding="utf-8")
    claim = {"id": "s", "value": 42}
    check = {"kind": "script", "repro": "repro/calc.py"}
    assert checks.run_check({}, claim, check, pack_dir)["ok"]
    claim["value"] = 43
    assert not checks.run_check({}, claim, check, pack_dir)["ok"]


def test_undeclared_input_dir_rejected(pack_dir):
    check = {"kind": "file_hash_map", "algo": "sha256_16", "names_from": "claim",
             "dir_decl": "logs"}
    claim = {"id": "x", "value": {"a.log": "0" * 16}}
    with pytest.raises(checks.CheckError):
        checks.run_check({}, claim, check, pack_dir)
