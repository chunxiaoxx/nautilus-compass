"""seal:manifest 构建与校验——不可变快照语义(SPEC §6)。

活文件教训(batch001 resource_log.csv 打包后仍被追写 25h)的产品化:
verify 第一步重算全部哈希,任何不符 = SEAL_FAIL 并指名文件,不继续复算。
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

MANIFEST = "manifest.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_16(p: Path) -> str:
    return sha256_file(p)[:16]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj) -> bytes:
    """签名/哈希用 canonical 序列化(稳定字节)。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _scan_files(pack_dir: Path) -> dict[str, str]:
    """扫 pack 内容:pack.json + payload/ + repro/;排除 receipts/ 与 manifest 自身。"""
    files: dict[str, str] = {}
    for p in sorted(pack_dir.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(pack_dir).as_posix()
        if rel == MANIFEST or rel.split("/", 1)[0] in ("receipts", ".verifypack"):
            continue
        files[rel] = sha256_file(p)
    return files


def build_manifest(pack_dir: Path, inputs: list[dict] | None = None) -> dict:
    """pack 内容 → manifest。覆盖 pack.json + payload/ + repro/;外部 inputs 记声明路径哈希。"""
    files = _scan_files(pack_dir)
    declared: dict[str, str] = {}
    for inp in inputs or []:
        root = Path(inp["path"])
        for name in inp.get("files", []):
            f = root / name
            if not f.is_file():
                raise FileNotFoundError(f"declared input missing: {f}")
            declared[f"{inp['name']}/{name}"] = sha256_file(f)
    return {"manifest_version": "0.2", "files": files, "inputs": declared,
            "input_decls": list(inputs or [])}


def write_manifest(pack_dir: Path, inputs: list[dict] | None = None) -> Path:
    out = pack_dir / MANIFEST
    out.write_text(json.dumps(build_manifest(pack_dir, inputs), ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    return out


def verify_seal(pack_dir: Path) -> tuple[bool, list[str]]:
    """重算 manifest。返回 (ok, 违规列表)——每条形如 'modified: <path>'/'missing: <path>'。"""
    mf_path = pack_dir / MANIFEST
    if not mf_path.is_file():
        return False, ["missing: manifest.json"]
    mf = json.loads(mf_path.read_text(encoding="utf-8"))
    violations: list[str] = []
    current = build_manifest(pack_dir, None)["files"]
    for path, expect in mf["files"].items():
        if path == MANIFEST:
            continue
        if path not in current:
            violations.append(f"missing: {path}")
        elif current[path] != expect:
            violations.append(f"modified: {path}")
    for path in current:
        if path not in mf["files"] and path != MANIFEST:
            violations.append(f"unsealed: {path}")
    declared: dict[str, str] = mf.get("inputs", {})
    for key, expect in declared.items():
        iname, fname = key.split("/", 1)
        decl = next((d for d in mf.get("input_decls", []) if d["name"] == iname), None)
        f = (Path(decl["path"]) / fname) if decl else None
        if f is None or not f.is_file():
            violations.append(f"input-missing: {key}")
        elif sha256_file(f) != expect:
            violations.append(f"input-modified: {key}")
    return (not violations), violations
