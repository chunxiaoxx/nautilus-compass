"""release_pipeline.release — 产物发布流水线(坑版:管道退出码被吃待修)。"""
from __future__ import annotations

import subprocess

# 三步管道(§4:保持单次 shell 调用形态,不得拆分)
PIPELINE_CMD = "bash export.sh | bash validate.sh | bash sign.sh"

STEPS = ["export", "validate", "sign"]


class ReleaseError(Exception):
    """§3:任一步非零即整链失败。"""


def run_release(workdir: str) -> int:
    """执行三步发布管道,返回整链退出码(0=成功出库)。

    坑:returncode 只反映管道最后一个命令(sign),上游失败被掩盖。
    """
    proc = subprocess.run(
        PIPELINE_CMD, shell=True, cwd=workdir,
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise ReleaseError(f"release failed rc={proc.returncode}")
    return 0
