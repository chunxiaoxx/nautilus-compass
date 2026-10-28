#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""端点反哺:main.py 活路由批量导入 capability 账本(能力工程 V1 §七 第2步)。

router 级粒度(79 项):每项=prefix+模块,owner=platform(待各框认领改)。
幂等:按 name 查重。用法(backend/ 下): PYTHONPATH=. python ops/capability_import_endpoints.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.database import SessionLocal  # noqa: E402

MAIN = Path(__file__).resolve().parents[1] / "main.py"
PLATFORM_AID = 999844  # platform_dialog_user 业务 agent_id(FK 指业务列,split-brain 已核)


def main() -> int:
    src = MAIN.read_text(encoding="utf-8", errors="ignore")
    imports = dict(re.findall(r"^\s*from api\.(\w+) import router as (\w+)", src, re.M))
    # include 行:取 prefix 参数或裸 router
    items: list[tuple[str, str]] = []
    for line in src.splitlines():
        m = re.match(r"\s*app\.include_router\((\w+)(?:,\s*prefix=\"([^\"]*)\")?", line)
        if not m:
            continue
        as_name, prefix = m.group(1), m.group(2) or ""
        mod = next((k for k, v in imports.items() if v == m.group(1)), None)
        if mod:
            items.append((f"endpoint:{prefix or '/'}:{mod}", mod))
    s = SessionLocal()
    inserted = 0
    for name, mod in items:
        if s.execute(text("SELECT 1 FROM capability_capsules WHERE name=:n"), {"n": name}).first():
            continue
        s.execute(text(
            "INSERT INTO capability_capsules "
            "(name, description, pattern_type, knowledge_node_ids, epiplexity, "
            " complexity_level, created_by_agent_id, created_at) "
            "VALUES (:n, :d, 'API_ENDPOINT', '[]'::jsonb, 0.0, 'UNKNOWN', :aid, now())"),
            {"n": name, "d": f"端点能力(自动导入,owner待认领): api/{mod}.py", "aid": PLATFORM_AID})
        inserted += 1
    s.commit()
    total = s.execute(text("SELECT count(*) FROM capability_capsules")).scalar()
    s.close()
    print(f"imported +{inserted} | ledger total={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
