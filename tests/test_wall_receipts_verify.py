"""公开墙回执完整性门 · 2026-11-23(审计席)。

背景:docs/wall 下 15 张签名回执,其中 3 张对"入库字节"验签失败而两个多月无人知——
EXAM5_SCORECARD(.RETAKE1) 的签名是对着含 CRLF 的 Windows 工作区字节做的,入库时换行被
规范化成 LF,于是只有原作者那台机器能验过;MEMORY_SYSTEMS_DIRECTORY 是活板,签名后内容
又更新过。README 首页那条"一条命令验证"的示例,在 Linux/Mac 新克隆上照跑是 INVALID。

本测试按**入库字节**(git blob,即任何新克隆者拿到的字节)逐张验签,外加工作区字节口径,
保证"新克隆一命令验证"每次提交都被断言,而不是口号。
"""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WALL = ROOT / "docs" / "wall"
# 公钥正本 = README「Reproducibility Wall」一节的那把(docs/REPRODUCIBILITY_WALL.md 同)
PUBKEY = "f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be"


def _git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


def _tracked_sigs() -> list[str]:
    out = _git("ls-files", "docs/wall").decode("utf-8")
    sigs = [ln.strip() for ln in out.splitlines() if ln.endswith(".sig")]
    assert sigs, "docs/wall 下没有任何已跟踪的 .sig"
    return sigs


def _target_of(sig_rel: str) -> str:
    """去掉 .sig;若该路径不是已跟踪文件,则补 .md(如 EXAM5_SCORECARD.sig → EXAM5_SCORECARD.md)。"""
    base = sig_rel[: -len(".sig")]
    for cand in (base, base + ".md"):
        if subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"HEAD:{cand}"],
                          capture_output=True).returncode == 0:
            return cand
    raise AssertionError(f"{sig_rel} 找不到对应的已跟踪目标文件")


def _load_verifier():
    import importlib.util
    spec = importlib.util.spec_from_file_location("verify_receipt", ROOT / "scripts" / "verify_receipt.py")
    vr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vr)
    return vr


def _verify_scorecard(target_bytes: bytes, target_name: str, sig_bytes: bytes) -> bool:
    """与 scripts/verify_receipt.py 同构(复用其 verify,避免子进程与临时文件)。"""
    import hashlib
    vr = _load_verifier()
    payload = {"scorecard": target_name, "sha256": hashlib.sha256(target_bytes).hexdigest()}
    msg = vr.canonical_json(payload).encode("utf-8")
    try:
        sig = bytes.fromhex(sig_bytes.decode("utf-8").strip())
        pub = bytes.fromhex(PUBKEY)
    except ValueError:
        return False
    return vr.verify(pub, msg, sig)


def _verify_pack(receipt_bytes: bytes, sig_bytes: bytes, manifest_bytes: bytes) -> tuple[bool, bool]:
    """VerifyPack 包回执(tools/verifypack/receipt.check_receipt 同构):
    ① 签名覆盖 receipt.json 解析后的规范化 JSON;② receipt.pack_manifest_hash 须等于 manifest.json 的字节哈希。"""
    import hashlib
    import json
    vr = _load_verifier()
    try:
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        sig = bytes.fromhex(sig_bytes.decode("utf-8").strip())
    except (ValueError, UnicodeDecodeError):
        return False, False
    sig_ok = vr.verify(bytes.fromhex(PUBKEY), vr.canonical_json(receipt).encode("utf-8"), sig)
    manifest_ok = receipt.get("pack_manifest_hash") == hashlib.sha256(manifest_bytes).hexdigest()
    return sig_ok, manifest_ok


def _check(sig_rel: str, *, committed: bool) -> tuple[bool, str]:
    """返回 (是否通过, 说明)。committed=True 读入库字节,否则读工作区字节。"""
    if "/packs/" in sig_rel:
        pack_dir = sig_rel.rsplit("/", 1)[0]
        rp, mp = f"{pack_dir}/receipt.json", f"{pack_dir}/manifest.json"
        if committed:
            r, s, m = (_git("cat-file", "blob", f"HEAD:{p}") for p in (rp, sig_rel, mp))
        else:
            r, s, m = ((ROOT / p).read_bytes() for p in (rp, sig_rel, mp))
        sig_ok, manifest_ok = _verify_pack(r, s, m)
        return sig_ok and manifest_ok, f"pack {Path(pack_dir).name}: sig={'ok' if sig_ok else 'INVALID'} manifest绑定={'ok' if manifest_ok else 'MISMATCH'}"
    tgt_rel = _target_of(sig_rel)
    if committed:
        t, s = _git("cat-file", "blob", f"HEAD:{tgt_rel}"), _git("cat-file", "blob", f"HEAD:{sig_rel}")
    else:
        t, s = (ROOT / tgt_rel).read_bytes(), (ROOT / sig_rel).read_bytes()
    return _verify_scorecard(t, Path(tgt_rel).name, s), Path(tgt_rel).name


@pytest.mark.parametrize("sig_rel", _tracked_sigs(), ids=lambda s: s.replace("docs/wall/", ""))
def test_wall_receipt_verifies_on_committed_bytes(sig_rel: str):
    """入库字节口径:新克隆者在任何平台上照 README 跑,必须 VALID。"""
    ok, what = _check(sig_rel, committed=True)
    assert ok, f"{what}:对入库字节验签失败——新克隆者按 README 验证会得到 INVALID"


@pytest.mark.parametrize("sig_rel", _tracked_sigs(), ids=lambda s: s.replace("docs/wall/", ""))
def test_wall_receipt_verifies_on_working_tree(sig_rel: str):
    """工作区字节口径:防止换行属性被改坏后本机能过、别人不能过。"""
    tgt = sig_rel.rsplit("/", 1)[0] + "/receipt.json" if "/packs/" in sig_rel else _target_of(sig_rel)
    if (ROOT / tgt).read_bytes() != _git("cat-file", "blob", f"HEAD:{tgt}"):
        pytest.skip("工作区检出时做了换行转换,仅入库字节口径有约束力")
    ok, what = _check(sig_rel, committed=False)
    assert ok, f"{what}:工作区口径验签失败"


def test_readme_example_command_succeeds_on_committed_bytes(tmp_path):
    """README 首页示例原样执行(对入库字节),退出码必须为 0。"""
    t = tmp_path / "EXAM5_SCORECARD.md"
    s = tmp_path / "EXAM5_SCORECARD.sig"
    t.write_bytes(_git("cat-file", "blob", "HEAD:docs/wall/EXAM5_SCORECARD.md"))
    s.write_bytes(_git("cat-file", "blob", "HEAD:docs/wall/EXAM5_SCORECARD.sig"))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_receipt.py"), str(t), str(s), PUBKEY],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "[VALID]" in r.stdout


def test_wall_attrs_preserve_bytes():
    """docs/wall 必须声明 -text:签名绑定的是字节,任何换行转换都会让签名失效。"""
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "docs/wall/** -text" in attrs or "docs/wall/* -text" in attrs
