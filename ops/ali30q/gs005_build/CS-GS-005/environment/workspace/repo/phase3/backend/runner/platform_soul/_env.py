"""自包含 env 加载:webhook subprocess 调用时未必透传我方 env,
故 entry 脚本启动时读同目录 `.env`(若存在)补入 os.environ(不覆盖已存在的)。
.env 带外灌(不落仓)· 格式 KEY=VALUE 每行一个 · # 注释 · 忽略空行。
"""
from __future__ import annotations

import os


def load_sibling_env(path: str | None = None) -> None:
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
