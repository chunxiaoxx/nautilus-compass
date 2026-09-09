"""Ed25519 纯 stdlib 实现(RFC 8032)——VerifyPack receipt 签名用。

零第三方依赖;常数与算法依 RFC 8032(Edwards25519)。本模块只做 sign/verify/
keypair 推导,不做 malleability 加固以外的检查(verify 按坐标方程复算,足够
本协议"验明回执未改"的用途)。
"""
from __future__ import annotations

import hashlib
import os

Q = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493


def _inv(x: int) -> int:
    return pow(x, Q - 2, Q)


_D = -121665 * _inv(121666) % Q
_I = pow(2, (Q - 1) // 4, Q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_D * y * y + 1) % Q
    x = pow(xx, (Q + 3) // 8, Q)
    if (x * x - xx) % Q != 0:
        x = x * _I % Q
    if (x * x - xx) % Q != 0:
        raise ValueError("point decompression failed")
    if x % 2 != 0:
        x = Q - x
    return x


_BY = 4 * _inv(5) % Q
_B = (_xrecover(_BY), _BY, 1, _xrecover(_BY) * _BY % Q)  # extended coords (X,Y,Z,T)
_IDENTITY = (0, 1, 1, 0)


def _add(p: tuple, q_: tuple) -> tuple:
    x1, y1, z1, t1 = p
    x2, y2, z2, t2 = q_
    a = (y1 - x1) * (y2 - x2) % Q
    b = (y1 + x1) * (y2 + x2) % Q
    c = 2 * _D * t1 * t2 % Q
    d = 2 * z1 * z2 % Q
    e, f, g, h = b - a, d - c, d + c, b + a
    return (e * f % Q, g * h % Q, f * g % Q, e * h % Q)


def _mult(p: tuple, e: int) -> tuple:
    r = _IDENTITY
    while e > 0:
        if e & 1:
            r = _add(r, p)
        p = _add(p, p)
        e >>= 1
    return r


def _encode(p: tuple) -> bytes:
    x, y, z, _t = p
    zi = _inv(z)
    x = x * zi % Q
    y = y * zi % Q
    bits = [(y >> i) & 1 for i in range(255)] + [x & 1]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(32))


def _decode(s: bytes) -> tuple:
    y = int.from_bytes(s, "little") & ((1 << 255) - 1)
    x = _xrecover(y)
    if x & 1 != (s[31] >> 7) & 1:
        x = Q - x
    p = (x, y, 1, x * y % Q)
    # on-curve check: -x^2 + y^2 == 1 + d x^2 y^2
    xx, yy = x * x % Q, y * y % Q
    if (-xx + yy - 1 - _D * xx * yy) % Q != 0:
        raise ValueError("point not on curve")
    return p


def _hint(m: bytes) -> int:
    return int.from_bytes(hashlib.sha512(m).digest(), "little")


def publickey(seed: bytes) -> bytes:
    """seed(任意 32B)→ 公钥 32B。RFC 8032:私钥即 seed,公钥由其推导。"""
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    return _encode(_mult(_B, a))


def sign(msg: bytes, seed: bytes, pub: bytes | None = None) -> bytes:
    pub = pub or publickey(seed)
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    r = _hint(h[32:] + msg) % L
    r_enc = _encode(_mult(_B, r))
    k = _hint(r_enc + pub + msg) % L
    s = (r + k * a) % L
    return r_enc + s.to_bytes(32, "little")


def verify(sig: bytes, msg: bytes, pub: bytes) -> bool:
    if len(sig) != 64 or len(pub) != 32:
        return False
    try:
        r_pt = _decode(sig[:32])
        a_pt = _decode(pub)
    except ValueError:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= L:  # 规范性检查:拒绝高半区 S(防 malleability)
        return False
    k = _hint(sig[:32] + pub + msg)
    # extended 坐标同一仿射点可有不同 Z,不能 tuple 直接比;encode 归一后比字节
    return _encode(_mult(_B, s)) == _encode(_add(r_pt, _mult(a_pt, k)))


def keypair() -> tuple[bytes, bytes]:
    """生成 (seed 私钥 32B, 公钥 32B)。私钥用 os.urandom,由调用方落盘保管。"""
    seed = os.urandom(32)
    return seed, publickey(seed)
