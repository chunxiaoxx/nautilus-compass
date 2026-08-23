"""N2 燃料周批 QC(GOAL_SSOT 无悔层 · 每周五跑 · 心跳可催)。

对 pending/ 候选执行 Gate B 方法 QC:
1. 过期清理:>14 天未 QC 的候选移入 expired/(记录,不删)。
2. 盘点输出:pending 数 / 本周新增 / 最老候选年龄 → stdout + 写周报 obs。
3. 逐条 QC(需 agent 会话执行,本脚本只做队列卫生与盘点):
   候选 → 提炼自然语言问题 → 裸模型 control 测(control 先失败才可能③类)
   → 失败=有 headroom 候选 → build Gate B suite 验 Gold → 过门转正入池。
判据(GOAL SSOT N2):月增 ≥10 条③类过门燃料。
"""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

POOL = Path(__file__).resolve().parents[1] / "vtf" / "fuel_pool"
PENDING = POOL / "pending"
EXPIRED = POOL / "expired"
MAX_AGE_DAYS = 14


def main() -> int:
    PENDING.mkdir(parents=True, exist_ok=True)
    EXPIRED.mkdir(parents=True, exist_ok=True)
    now = time.time()
    pending, expired_now = [], []
    for f in PENDING.glob("*.md"):
        age_days = (now - f.stat().st_mtime) / 86400
        if age_days > MAX_AGE_DAYS:
            f.rename(EXPIRED / f.name)
            expired_now.append(f.name)
        else:
            pending.append((f.name, age_days))
    pending.sort(key=lambda x: -x[1])
    print(f"pending: {len(pending)} · expired_this_run: {len(expired_now)}")
    for name, age in pending[:10]:
        print(f"  {age:5.1f}d  {name}")
    if pending:
        oldest = pending[0]
        if oldest[1] > 7:
            print(f"🔴 最老候选已 {oldest[1]:.0f} 天未 QC(GOAL SSOT N2 每周五批)——本周该跑 QC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
