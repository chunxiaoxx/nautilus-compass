# -*- coding: utf-8 -*-
"""verifier.batch · 修复版(VER-53)。

§1/§2 原则贯穿到聚合层: 目标未验证(含目录不存在)时,
聚合结论不存在"验证通过"这个状态——N/A 不是跳过,是未验证。
"""
from pathlib import Path

from verifier.runner import run_verification


def verify_batch(workdir: str, targets: list) -> dict:
    """批量验证交付目录下多个目标模块。

    返回: {"verified": bool, "detail": str}
    verified=True 当且仅当**每个**目标都实际验证且通过。
    """
    results = {}
    missing = []
    for t in targets:
        tdir = Path(workdir) / t
        if not (tdir / "Makefile").exists():
            missing.append(t)
            results[t] = {"verified": False,
                          "detail": f"verification unavailable: target missing: {t}"}
            continue
        results[t] = run_verification(str(tdir))
    ok = all(r["verified"] for r in results.values()) if targets else False
    missing_note = f" · missing: {','.join(missing)}" if missing else ""
    return {"verified": ok,
            "detail": f"{len(targets) - len(missing)}/{len(targets)} targets verified{missing_note}"}
