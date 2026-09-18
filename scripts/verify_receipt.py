# -*- coding: utf-8 -*-
"""Assay receipt 验签 CLI(外部可复制的单文件 · 零第三方依赖 · "验证的验证免费")。

验证一个 (scorecard/receipt 文件, .sig, 公钥) 三元组——不信任签发方,只信数学。
用法:
  python verify_receipt.py <target.md> <target.sig> <pubkey hex> [payload.json]
payload 缺省 = {"scorecard": <文件名>, "sha256": <target 的 sha256>}(墙面成绩单格式)。
退出码 0=签名有效,1=无效,2=参数/格式错误。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

# ed25519 纯 python 参考实现(与 tools/verifypack/ed25519.py 同源;此处内联拷贝以保
# 单文件可分发 —— 协议要求:验证不依赖签发方的任何代码)。
import base64
import hashlib as _hl


def _sha512(m: bytes) -> bytes:
    return _hl.sha512(m).digest()


try:  # 优先 ctypes 绑定 libsodium(若装了),否则用纯 python 路径
    raise ImportError  # v0:强制走纯 python,保证无第三方依赖
except ImportError:
    pass

# —— 极简 ed25519(RFC 8032,参考实现,签名验证专用)——
p = 2**255 - 19
q = 2**252 + 27742317777372353535851937790883648493


def _inv(x: int) -> int:
    return pow(x, p - 2, p)


_d = -121665 * _inv(121666) % p
_I = pow(2, (p - 1) // 4, p)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_d * y * y + 1)
    x = pow(xx, (p + 3) // 8, p)
    if (x * x - xx) % p != 0:
        x = x * _I % p
    if x % 2 != 0:
        x = p - x
    return x


By = 4 * _inv(5) % p
Bx = _xrecover(By)
B = (Bx % p, By % p, 1, Bx * By % p)  # 扩展坐标


def _edwards_add(P, Q):
    x1, y1, z1, t1 = P
    x2, y2, z2, t2 = Q
    a = (y1 - x1) * (y2 - x2) % p
    b = (y1 + x1) * (y2 + x2) % p
    c = t1 * 2 * _d * t2 % p
    dd = z1 * 2 * z2 % p
    e, f, g, h = b - a, dd - c, dd + c, b + a
    return (e * f % p, g * h % p, f * g % p, e * h % p)


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
        x = p - x
    P = (x, y, 1, x * y % p)
    if not (0 <= x < p and 0 <= y < p):
        raise ValueError("out of range")
    return P


def _sha512_modq(m: bytes) -> int:
    return int.from_bytes(_sha512(m), "little") % q


def verify(public: bytes, msg: bytes, signature: bytes) -> bool:
    if len(public) != 32 or len(signature) != 64:
        return False
    A = _point_decompress(public)
    Rs = signature[:32]
    R = _point_decompress(Rs)
    S = int.from_bytes(signature[32:], "little")
    h = _sha512_modq(Rs + public + msg)
    sB = _scalarmult(B, S)
    hA = _scalarmult(A, h)
    RhA = _edwards_add(R, hA)
    return (sB[1] * RhA[2] - RhA[1] * sB[2]) % p == 0 and (sB[0] * RhA[2] - RhA[0] * sB[2]) % p == 0


def canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main(argv: list[str]) -> int:
    if len(argv) not in (4, 5):
        print(__doc__)
        return 2
    target, sig_path, pub_hex = Path(argv[1]), Path(argv[2]), argv[3].strip()
    if not target.is_file() or not sig_path.is_file():
        print("[err] file missing", file=sys.stderr)
        return 2
    if len(argv) == 5:
        payload = json.loads(Path(argv[4]).read_text(encoding="utf-8"))
    else:
        payload = {"scorecard": target.name,
                   "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    sig = bytes.fromhex(sig_path.read_text(encoding="utf-8").strip())
    pub = bytes.fromhex(pub_hex)
    ok = verify(pub, canonical_json(payload).encode("utf-8"), sig)
    print(f"{'[VALID]' if ok else '[INVALID]'} target={target.name} "
          f"sha256={payload.get('sha256', '?')[:16]}…")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
