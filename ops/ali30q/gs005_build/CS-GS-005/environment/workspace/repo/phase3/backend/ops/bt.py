#!/usr/bin/env python
"""bt(backend tool)——cwd 坑 L2 物理化(2026-10-04,用户批示范二)。

背景:shell cwd 每次调用后重置,曾 4 次踩".venv 相对路径找不到→pytest 没跑就
继续部署"。记忆/提醒是 L0/L1,这个 wrapper 是 L2:它自己强制 cd 到 backend,
调用它的命令物理上不可能踩 cwd 坑。

用法(绝对路径,勿依赖当前目录):
  python phase3/backend/ops/bt.py pytest tests/xxx.py -q
  python phase3/backend/ops/bt.py scan            # 复发扫描
  python phase3/backend/ops/bt.py clock           # 实测时间(示范一的可信时间源)
  python phase3/backend/ops/bt.py venv            # 打印本机 venv python 路径
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]  # backend/——wrapper 的锚,永不错
VENV_PY = BACKEND / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    cmd = args[0]
    if cmd == "pytest":
        rest = args[1:] or ["tests/", "-q"]
        sys.exit(subprocess.call([str(VENV_PY), "-m", "pytest"] + rest, cwd=str(BACKEND)))
    if cmd == "scan":
        sys.exit(subprocess.call([str(VENV_PY), str(BACKEND / "ops" / "recurrence_scan.py")],
                                  cwd=str(BACKEND)))
    if cmd == "clock":
        # 示范一配套:唯一可信时间源——本地钟+UTC 同打,报告时间从这里抄,禁心算
        from zoneinfo import ZoneInfo
        now = datetime.now()
        print(f"local={now:%Y-%m-%d %H:%M:%S} utc={datetime.now(ZoneInfo('UTC')):%Y-%m-%d %H:%M:%S}Z")
        sys.exit(0)
    if cmd == "venv":
        print(VENV_PY)
        sys.exit(0)
    print(f"未知子命令: {cmd}(pytest/scan/clock/venv)")
    sys.exit(2)


if __name__ == "__main__":
    main()
