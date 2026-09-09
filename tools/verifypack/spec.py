"""VerifyPack v0.2 schema 常量与校验(spec: docs/verifypack/SPEC_v0.2.md)。"""
from __future__ import annotations

from typing import Any

RECEIPT_VERSION = "0.2"
PROTOCOL = "verifypack-0.2"

CHECK_KINDS = {"aggregate", "file_hash", "file_hash_map", "group_count",
               "json_map_equal", "text_contains", "script"}
LEVELS = {"L1", "L2"}
VERDICTS = {"agree", "disagree", "degraded", "seal_fail"}
AGG_OPS = {"ratio_eq", "value_eq"}

BOUNDARY = "独立技术验证与回执,不作客户验收或结算决定"


class SpecError(ValueError):
    """pack.json / claim 结构不合 v0.2 spec。"""


def _req(obj: dict[str, Any], field: str, types: tuple, where: str) -> Any:
    v = obj.get(field)
    if not isinstance(v, types) or isinstance(v, bool) and bool not in types:
        raise SpecError(f"{where}: field {field!r} required ({'/'.join(t.__name__ for t in types)})")
    return v


def validate_claim(claim: dict[str, Any], where: str = "claim") -> None:
    _req(claim, "id", (str,), where)
    _req(claim, "level", (str,), where)
    if claim["level"] not in LEVELS:
        raise SpecError(f"{where}/{claim['id']}: level must be one of {sorted(LEVELS)}")
    _req(claim, "value", (str, int, float, dict, list), where)
    checks = claim.get("checks") or {}
    primary = checks.get("primary", checks if "primary" not in checks and checks else None)
    # 允许两种写法:checks={primary,fallback} 或 checks 直接就是 check 对象
    if checks and "primary" not in checks and checks.get("kind"):
        primary = checks
    if not isinstance(primary, dict) or not primary.get("kind"):
        raise SpecError(f"{where}/{claim['id']}: checks.primary with 'kind' required")
    validate_check(primary, where=f"{where}/{claim['id']}/primary")


def validate_check(check: dict[str, Any], where: str = "check") -> None:
    kind = check.get("kind")
    if kind not in CHECK_KINDS:
        raise SpecError(f"{where}: kind must be one of {sorted(CHECK_KINDS)}")
    needs = {
        "aggregate": ("from", "num", "op"),
        "file_hash": ("file", "expect"),
        "file_hash_map": ("algo",),
        "group_count": ("from", "by"),
        "json_map_equal": ("file", "path", "map_by", "field"),
        "text_contains": ("file", "needles"),
        "script": ("repro",),
    }[kind]
    for f in needs:
        if f not in check:
            raise SpecError(f"{where}({kind}): field {f!r} required")
    if kind == "aggregate" and check["op"] not in AGG_OPS:
        raise SpecError(f"{where}: op must be one of {sorted(AGG_OPS)}")


def validate_pack(pack: dict[str, Any]) -> None:
    _req(pack, "pack", (str,), "pack")
    _req(pack, "protocol_version", (str,), "pack")
    if pack["protocol_version"] != PROTOCOL:
        raise SpecError(f"pack: protocol_version must be {PROTOCOL!r}, got {pack['protocol_version']!r}")
    _req(pack, "claims", (list,), "pack")
    if not pack["claims"]:
        raise SpecError("pack: claims empty")
    ids = set()
    for i, c in enumerate(pack["claims"]):
        validate_claim(c, where=f"claims[{i}]")
        if c["id"] in ids:
            raise SpecError(f"pack: duplicate claim id {c['id']!r}")
        ids.add(c["id"])
