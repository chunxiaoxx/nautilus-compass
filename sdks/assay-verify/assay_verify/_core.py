# -*- coding: utf-8 -*-
"""assay-verify 核心:纯 python ed25519(RFC 8032)+ 证据签名 + 三态验真。

ed25519 参考实现与 nautilus-compass tools/verifypack、scripts/verify_receipt.py
同源交叉验证(两套实现互验 VALID,2026-09-19)。
"""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from pathlib import Path

# ── ed25519(RFC 8032,签名+验证参考实现)────────────────────────────
_p = 2**255 - 19
_q = 2**252 + 27742317777372353535851937790883648493


def _inv(x: int) -> int:
    return pow(x, _p - 2, _p)


_d = -121665 * _inv(121666) % _p
_I = pow(2, (_p - 1) // 4, _p)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_d * y * y + 1)
    x = pow(xx, (_p + 3) // 8, _p)
    if (x * x - xx) % _p != 0:
        x = x * _I % _p
    if x % 2 != 0:
        x = _p - x
    return x


_By = 4 * _inv(5) % _p
_Bx = _xrecover(_By)
_B = (_Bx % _p, _By % _p, 1, _Bx * _By % _p)


def _edwards_add(P, Q):
    x1, y1, z1, t1 = P
    x2, y2, z2, t2 = Q
    a = (y1 - x1) * (y2 - x2) % _p
    b = (y1 + x1) * (y2 + x2) % _p
    c = t1 * 2 * _d * t2 % _p
    dd = z1 * 2 * z2 % _p
    e, f, g, h = b - a, dd - c, dd + c, b + a
    return (e * f % _p, g * h % _p, f * g % _p, e * h % _p)


def _scalarmult(P, e):
    if e == 0:
        return (0, 1, 1, 0)
    Q = _scalarmult(P, e // 2)
    Q = _edwards_add(Q, Q)
    if e & 1:
        Q = _edwards_add(Q, P)
    return Q


def _point_decompress(s: bytes):
    if len(s) != 32:
        raise ValueError("bad point")
    y = int.from_bytes(s, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    x = _xrecover(y)
    if x & 1 != sign:
        x = _p - x
    P = (x, y, 1, x * y % _p)
    if not (0 <= x < _p and 0 <= y < _p):
        raise ValueError("out of range")
    return P


def _sha512(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def _sha512_modq(m: bytes) -> int:
    return int.from_bytes(_sha512(m), "little") % _q


def _encode_point(P) -> bytes:
    """射影坐标 → 32B 压缩编码(必须先仿射化:x=X/Z,y=Y/Z,Z≠1 时直接取 Y 是错的)。"""
    x, y, z, _ = P
    zinv = _inv(z)
    x = x * zinv % _p
    y = y * zinv % _p
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def _ed25519_verify(public: bytes, msg: bytes, signature: bytes) -> bool:
    if len(public) != 32 or len(signature) != 64:
        return False
    try:
        A = _point_decompress(public)
        R = _point_decompress(signature[:32])
    except ValueError:
        return False
    S = int.from_bytes(signature[32:], "little")
    h = _sha512_modq(signature[:32] + public + msg)
    sB = _scalarmult(_B, S)
    hA = _scalarmult(A, h)
    RhA = _edwards_add(R, hA)
    return (sB[1] * RhA[2] - RhA[1] * sB[2]) % _p == 0 \
        and (sB[0] * RhA[2] - RhA[0] * sB[2]) % _p == 0


def _ed25519_sign(msg: bytes, seed: bytes) -> bytes:
    h = _sha512(seed)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    pub = _encode_point(_scalarmult(_B, a))
    prefix = h[32:]
    r = _sha512_modq(prefix + msg)
    Rs = _encode_point(_scalarmult(_B, r))
    s = (r + _sha512_modq(Rs + pub + msg) * a) % _q
    return Rs + s.to_bytes(32, "little")


def _ed25519_keypair() -> tuple[bytes, bytes]:
    seed = secrets.token_bytes(32)
    return seed, _pub_from_seed(seed)


def _pub_from_seed(seed: bytes) -> bytes:
    h = _sha512(seed)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    return _encode_point(_scalarmult(_B, a))


# ── 协议层(Assay Protocol v0)────────────────────────────────────────
def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def default_payload(target: Path) -> dict:
    """墙面成绩单格式:{"scorecard": 文件名, "sha256": 全文哈希}。"""
    return {"scorecard": target.name,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


@dataclass
class AssayResult:
    ok: bool
    target: str
    sha256: str
    detail: str = ""

    def __bool__(self):
        return self.ok


def verify(target, sig, pubkey, payload=None) -> AssayResult:
    """消费端一行:验 (目标文件, .sig, 公钥hex) 三元组。三态:
    VALID / INVALID(验签失败) / MALFORMED(材料缺失或格式错)。"""
    target, sig = Path(target), Path(sig)
    if not target.is_file():
        return AssayResult(False, str(target), "", "target missing (MALFORMED)")
    if not sig.is_file():
        return AssayResult(False, str(target), "", "signature file missing (MALFORMED)")
    try:
        sig_bytes = bytes.fromhex(sig.read_text(encoding="utf-8").strip())
        pub = bytes.fromhex(str(pubkey).strip())
    except ValueError as e:
        return AssayResult(False, str(target), "", f"bad hex: {e} (MALFORMED)")
    if len(sig_bytes) != 64 or len(pub) != 32:
        return AssayResult(False, str(target), "", "bad length (MALFORMED)")
    try:
        pay = payload if payload is not None else default_payload(target)
        msg = canonical_json(pay).encode("utf-8")
    except (TypeError, ValueError) as e:
        return AssayResult(False, str(target), "", f"payload error: {e} (MALFORMED)")
    ok = _ed25519_verify(pub, msg, sig_bytes)
    digest = pay.get("sha256") if isinstance(pay, dict) else None
    if not digest:
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return AssayResult(ok, str(target), str(digest),
                       "VALID" if ok else "INVALID (signature mismatch)")


def keygen(key_path, name="assay") -> Path:
    """生成密钥对:写 <key_path>(私钥 hex)与同名 .pub。返回私钥路径。"""
    seed, pub = _ed25519_keypair()
    kp = Path(key_path)
    kp.parent.mkdir(parents=True, exist_ok=True)
    kp.write_text(seed.hex() + "\n", encoding="utf-8", newline="\n")
    pp = kp.with_suffix(".pub")
    pp.write_text(pub.hex() + "\n", encoding="utf-8", newline="\n")
    return kp


def attest(target, key_path, payload=None, out=None) -> Path:
    """生产端一行:对目标文件签名,产 <target>.sig(返回 sig 路径)。
    payload 缺省=墙面成绩单格式;自定义声明传 dict。"""
    target = Path(target)
    seed = bytes.fromhex(Path(key_path).read_text(encoding="utf-8").strip())
    if len(seed) != 32:
        raise ValueError("key file must contain 32-byte hex seed")
    pay = payload if payload is not None else default_payload(target)
    sig = _ed25519_sign(canonical_json(pay).encode("utf-8"), seed)
    out = Path(out) if out else target.with_suffix(target.suffix + ".sig")
    out.write_text(sig.hex(), encoding="utf-8", newline="\n")
    return out
