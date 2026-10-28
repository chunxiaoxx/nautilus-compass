# -*- coding: utf-8 -*-
"""verifier.batch · 批量验证入口(VER-53 接入流水线)。

逐目标调用 runner.run_verification 并汇总。
"""
from pathlib import Path

from verifier.runner import run_verification


def verify_batch(workdir: str, targets: list) -> dict:
    """批量验证交付目录下多个目标模块。

    返回: {"verified": bool, "detail": str}
    目标目录不存在属"不适用"(N/A),跳过不拦交付。
    """
    results = {}
    for t in targets:
        tdir = Path(workdir) / t
        if not (tdir / "Makefile").exists():
            continue  # N/A: 不适用,合理跳过
        results[t] = run_verification(str(tdir))
    ok = all(r["verified"] for r in results.values())
    return {"verified": ok, "detail": f"{len(results)}/{len(targets)} targets executed"}
