"""密钥管理:keygen/加载。私钥路径一律走参数或 VERIFYPACK_KEY,禁硬编码。"""
from __future__ import annotations

import os
from pathlib import Path

from . import ed25519


def keygen(out_dir: Path, name: str = "compass") -> tuple[Path, Path]:
    """生成 <name>.key(私钥 hex)与 <name>.pub(公钥 hex)。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    seed, pub = ed25519.keypair()
    kp = out_dir / f"{name}.key"
    pp = out_dir / f"{name}.pub"
    kp.write_text(seed.hex() + "\n", encoding="utf-8", newline="\n")
    pp.write_text(pub.hex() + "\n", encoding="utf-8", newline="\n")
    return kp, pp


def load_key(explicit: str | None) -> Path:
    """--key 参数优先,回退环境变量 VERIFYPACK_KEY;两者皆无即报错。"""
    p = explicit or os.environ.get("VERIFYPACK_KEY")
    if not p:
        raise FileNotFoundError("no signing key: pass --key or set VERIFYPACK_KEY")
    kp = Path(p)
    if not kp.is_file():
        raise FileNotFoundError(f"key file not found: {kp}")
    return kp
