"""seal 语义测试:不可变快照——篡改/活文件必被抓现行。"""
import pytest

from tools.verifypack import seal

PACK = "testpack"


@pytest.fixture()
def sealed_pack(tmp_path):
    d = tmp_path / PACK
    (d / "payload").mkdir(parents=True)
    (d / "pack.json").write_text('{"pack": "testpack"}', encoding="utf-8")
    (d / "payload" / "data.json").write_text('{"x": 1}', encoding="utf-8")
    seal.write_manifest(d)
    return d


def test_fresh_seal_passes(sealed_pack):
    ok, violations = seal.verify_seal(sealed_pack)
    assert ok, violations


def test_modified_file_caught(sealed_pack):
    (sealed_pack / "payload" / "data.json").write_text('{"x": 2}', encoding="utf-8")
    ok, violations = seal.verify_seal(sealed_pack)
    assert not ok
    assert any("modified: payload/data.json" in v for v in violations)


def test_live_file_appended_after_seal_caught(sealed_pack):
    """batch001 教训:打包后仍被追写的文件必须抓现行。"""
    with open(sealed_pack / "payload" / "data.json", "a", encoding="utf-8") as f:
        f.write('{"late": true}')
    ok, violations = seal.verify_seal(sealed_pack)
    assert not ok
    assert any("payload/data.json" in v for v in violations)


def test_missing_file_caught(sealed_pack):
    (sealed_pack / "payload" / "data.json").unlink()
    ok, violations = seal.verify_seal(sealed_pack)
    assert not ok
    assert any("missing: payload/data.json" in v for v in violations)


def test_extra_unsealed_file_caught(sealed_pack):
    (sealed_pack / "payload" / "sneaky.json").write_text("{}", encoding="utf-8")
    ok, violations = seal.verify_seal(sealed_pack)
    assert not ok
    assert any("unsealed: payload/sneaky.json" in v for v in violations)


def test_declared_input_change_caught(sealed_pack, tmp_path):
    """外部声明路径的文件被改 → input-modified。"""
    ext = tmp_path / "ext"
    ext.mkdir()
    (ext / "resource_log.csv").write_text("row1\n", encoding="utf-8")
    decl = [{"name": "logs", "path": str(ext), "files": ["resource_log.csv"]}]
    seal.write_manifest(sealed_pack, decl)  # input_decls 随 manifest 一起落盘

    ok, _ = seal.verify_seal(sealed_pack)
    assert ok  # 未动时通过

    with open(ext / "resource_log.csv", "a", encoding="utf-8") as f:
        f.write("row2-after-25h\n")
    ok, violations = seal.verify_seal(sealed_pack)
    assert not ok
    assert any("input-modified: logs/resource_log.csv" in v for v in violations)


def test_canonical_json_stable():
    a = seal.canonical_json({"b": 1, "a": [True, "中"]})
    b = seal.canonical_json({"a": [True, "中"], "b": 1})
    assert a == b
