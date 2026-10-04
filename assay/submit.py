# -*- coding: utf-8 -*-
"""assay 提交侧 schema(API 最小件,3.3.0)。

两条提交通道(承 EGR 缺口回流环 v0.1,#2981 三补后的八件制式):
- challenge  — 材料方/第三方对已出 verdict 的质疑件(POST /assay/challenge 对应载荷)
- errata     — 判读方自勘误(file_errata,判绩账双向:评委也会错)

纯 stdlib 校验;零外部依赖。与 verdict schema v2.1 的 cause_tag/confidence 枚举同源。
"""
from __future__ import annotations

CAUSE_TAGS = ("execution", "data", "judgment", "capability")
LABEL_ORIGINS = ("independent_recompute", "human_review", "official_rule",
                 "three_vendor_final", "verifier")

# challenge 八件制式(v5 #2981 三补:new_verdict nullable + confidence 第八件 + cause_tag 四枚举)
CHALLENGE_REQUIRED = ("qid", "claim", "artifacts_ref", "original_verdict",
                      "reason", "cause_tag", "label_origin", "confidence")

# errata 最小件(判读方自勘;new_verdict 可空=仅撤回不改判)
ERRATA_REQUIRED = ("case_id", "field", "original", "reason", "cause_tag")


def _check_enum(payload: dict, key: str, allowed: tuple, errors: list, tag: str) -> None:
    if payload.get(key) not in allowed:
        errors.append(f"{tag} {key} 枚举外({ '|'.join(allowed) }): {payload.get(key)!r}")


def _check_anchor(payload: dict, warns: list, tag: str) -> None:
    if not (payload.get("artifacts_ref") or payload.get("sha16") or payload.get("sha256")):
        warns.append(f"{tag} 无任何锚定字段(artifacts_ref/sha16/sha256)——建议补坐标")


def validate_challenge(p: dict) -> tuple[list[str], list[str]]:
    """质疑件校验:new_verdict 缺省=仅质疑不改判;给值时须为三态枚举。"""
    errors: list[str] = []
    warns: list[str] = []
    for k in CHALLENGE_REQUIRED:
        if p.get(k) in (None, ""):
            errors.append(f"challenge 缺必填件 {k}")
    _check_enum(p, "cause_tag", CAUSE_TAGS, errors, "challenge")
    _check_enum(p, "label_origin", LABEL_ORIGINS, errors, "challenge")
    _check_enum(p, "confidence", ("measured", "inferred"), errors, "challenge")
    nv = p.get("new_verdict")
    if nv not in (None, "", "VERDICT", "PARTIAL", "U_STATE"):
        errors.append(f"challenge new_verdict 枚举外(空|VERDICT|PARTIAL|U_STATE): {nv!r}")
    if nv in (None, ""):
        warns.append("challenge new_verdict 空=仅质疑不改判(裁定权归判读方)")
    _check_anchor(p, warns, "challenge")
    return errors, warns


def validate_errata(p: dict) -> tuple[list[str], list[str]]:
    """勘误件校验:判读方自勘,new_verdict 可空。"""
    errors: list[str] = []
    warns: list[str] = []
    for k in ERRATA_REQUIRED:
        if p.get(k) in (None, ""):
            errors.append(f"errata 缺必填件 {k}")
    _check_enum(p, "cause_tag", CAUSE_TAGS, errors, "errata")
    nv = p.get("new_verdict")
    if nv not in (None, "", "VERDICT", "PARTIAL", "U_STATE"):
        errors.append(f"errata new_verdict 枚举外(空|VERDICT|PARTIAL|U_STATE): {nv!r}")
    if nv in (None, ""):
        warns.append("errata new_verdict 空=仅撤回不改判")
    _check_anchor(p, warns, "errata")
    return errors, warns
