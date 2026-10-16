#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""迁移打包器(R544): Windows 主力机 → NAS → Mac mini。

四包结构(见 MACMINI_MIGRATION_PACK_20261016.md):
  01_sessions/  会话历史(每项目一 tar.zst)
  02_memory/    记忆库热层
  03_claude_config/ 配置瘦身影
  manifest.json     逐包 sha256+计数
输出: C:/Users/chunx/nas-outbox/nautilus-migration/(等 NAS 挂载后整体上传)
用法: python tools/migrate_pack_to_nas.py [--upload]
"""
import hashlib
import json
import os
import tarfile
from pathlib import Path

HOME = Path.home()
CLAUDE = HOME / ".claude"
PROJ = CLAUDE / "projects"
OUT = HOME / "nas-outbox" / "nautilus-migration"

SKIP_SESSION_TMP = ("/*.jsonl.tmp",)


def pack_dir(src: Path, arcroot: str, out_path: Path, include=None, exclude=None):
    """tar.zst 打包(zstd 不可用时回退 gzip)。"""
    mode = "w:gz"
    suffix = ".tar.gz"
    out_path = out_path.with_suffix(suffix)
    n = 0
    with tarfile.open(out_path, mode) as tf:
        for root, dirs, files in os.walk(src):
            for f in files:
                full = Path(root) / f
                rel = full.relative_to(src)
                if include and not any(rel.match(pat) for pat in include):
                    continue
                if exclude and any(rel.match(pat) for pat in exclude):
                    continue
                try:
                    tf.add(full, arcname=f"{arcroot}/{rel}")
                    n += 1
                except (PermissionError, OSError):
                    pass
    return out_path, n


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"packages": [], "created": __import__("datetime").datetime.now().isoformat()}

    # 01 会话历史:每个有内容的顶层项目目录一包
    sess_dir = OUT / "01_sessions"
    sess_dir.mkdir(exist_ok=True)
    for d in sorted(PROJ.iterdir()):
        if not d.is_dir():
            continue
        size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
        if size_mb < 1:
            continue
        name = d.name.replace("/", "_")
        out, n = pack_dir(d, name, sess_dir / f"sessions_{name}.tar")
        sz = out.stat().st_size
        manifest["packages"].append({"pkg": out.name, "kind": "sessions", "files": n,
                                     "sha256": sha256(out), "bytes": sz})
        print(f"[01] {out.name}: {n} files {sz/1e6:.1f}MB")

    # 02 记忆库:全部项目的 memory/ 子目录
    mem_out = OUT / "02_memory"
    mem_out.mkdir(parents=True, exist_ok=True)
    out, n = pack_dir(PROJ, "projects", mem_out / "memory_all.tar",
                      include=["*/memory/*"])
    # 重排:上面 include 匹配 rel 即可
    sz = out.stat().st_size
    manifest["packages"].append({"pkg": out.name, "kind": "memory", "files": n,
                                 "sha256": sha256(out), "bytes": sz})
    print(f"[02] memory_all: {n} files {sz/1e6:.1f}MB")

    # 03 配置(瘦身:plugins 只收非缓存;排除 .cache)
    cfg_dir = OUT / "03_claude_config"
    cfg_dir.mkdir(exist_ok=True)
    for name in ("settings.json", ".claude.json"):
        src = HOME / name if not name.startswith(".") else CLAUDE / name
        alt = HOME / ".claude" / name
        src = src if src.exists() else alt
        if src.exists():
            (cfg_dir / name).write_bytes(src.read_bytes())
    for sub in ("hooks", "agents", "skills"):
        if (CLAUDE / sub).exists():
            out, n = pack_dir(CLAUDE / sub, sub, cfg_dir / f"{sub}.tar")
            manifest["packages"].append({"pkg": out.name, "kind": f"config:{sub}",
                                         "files": n, "sha256": sha256(out),
                                         "bytes": out.stat().st_size})
    print("[03] config done(plugins 大缓存剔除,后续按需)")

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    total = sum(p["bytes"] for p in manifest["packages"])
    print(f"== 完成: {len(manifest['packages'])} 包, 总 {total/1e6:.1f}MB -> {OUT}")
    print("待办: NAS 挂载后 --upload(或手动复制 nas-outbox/nautilus-migration/ 整目录)")


if __name__ == "__main__":
    main()
