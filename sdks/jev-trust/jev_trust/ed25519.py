# -*- coding: utf-8 -*-
"""ed25519 (RFC 8032) — vendored reference implementation.

Same source as assay-verify (sdks/assay-verify) and nautilus-compass
tools/verifypack; the three implementations are cross-validated (VALID
both ways, 2026-09-19). Pure python, zero dependencies.
"""
from __future__ import annotations

import hashlib
import secrets

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
    x, y, z, _ = P
    zinv = _inv(z)
    x = x * zinv % _p
    y = y * zinv % _p
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


def sign(msg: bytes, seed: bytes) -> bytes:
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


def verify(public: bytes, msg: bytes, signature: bytes) -> bool:
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


def keypair() -> tuple:
    seed = secrets.token_bytes(32)
    h = _sha512(seed)
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    pub = _encode_point(_scalarmult(_B, a))
    return seed, pub
