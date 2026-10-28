"""release_pipeline.release — 产物发布流水线(金标修复版)。

修复:pipefail 传导 + PIPESTATUS 回读定位失败步骤——§4 保持单次 shell 调用。
"""
from __future__ import annotations

import subprocess

STEPS = ["export", "validate", "sign"]

# 不用 f-string:命令内 $ 与花括号属 bash 语法,交由 bash 解释
# 注意:PIPESTATUS 必须在管道结束后第一句抓取(任何赋值都会刷新它)
_CMD = (
    "set -o pipefail\n"
    "bash export.sh | bash validate.sh | bash sign.sh\n"
    'ps=("${PIPESTATUS[@]}")\n'
    'rc=0\n'
    'for x in "${ps[@]}"; do [ "$x" -ne 0 ] && rc=$x; done\n'
    'echo "__PS__${ps[0]} ${ps[1]} ${ps[2]}" >&2\n'
    "exit $rc"
)

# 包接口保持与坑版一致(§5.3 不改变对外口径)
PIPELINE_CMD = _CMD


class ReleaseError(Exception):
    """§3:任一步非零即整链失败。"""


def run_release(workdir: str) -> int:
    """执行三步发布管道,返回整链退出码(0=成功出库)。

    修复:任一步非零经 pipefail 传导为整体非零;报错含失败步骤名与退出码。
    """
    proc = subprocess.run(["bash", "-c", _CMD], cwd=workdir,
                          capture_output=True, text=True)
    rc = proc.returncode
    if rc != 0:
        step_codes: dict[str, str] = {}
        for line in (proc.stderr or "").splitlines():
            if line.startswith("__PS__"):
                codes = line[len("__PS__"):].split()
                step_codes = dict(zip(STEPS, codes))
        failed = [f"{k}={v}" for k, v in step_codes.items() if v != "0"] or [f"rc={rc}"]
        raise ReleaseError("release failed: " + " ".join(failed))
    return 0
