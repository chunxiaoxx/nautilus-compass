# -*- coding: utf-8 -*-
"""verifier.runner · 修复版(VER-52)。

§1: 验证不可用→verified=False·detail 写明 unavailable。
§3: 异常分类(FileNotFound/Timeout/CalledProcess)全部 False。
"""
import subprocess


def run_verification(workdir: str) -> dict:
    """运行交付验证: 调用 make test 并返回验证结论。

    返回: {"verified": bool, "detail": str}
    verified=True 表示**实际验证且通过**。
    """
    try:
        r = subprocess.run(
            ["make", "test"],
            cwd=workdir, capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            return {"verified": True, "detail": r.stdout[-500:]}
        return {"verified": False, "detail": r.stderr[-500:]}
    except FileNotFoundError as e:
        return {"verified": False, "detail": f"verification unavailable: {e}"}
    except subprocess.TimeoutExpired:
        return {"verified": False, "detail": "verification timeout"}
