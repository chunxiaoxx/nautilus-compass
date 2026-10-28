# -*- coding: utf-8 -*-
"""端点接线对账巡检(U29 20261001 用户批"现在就做")——治"机制静默掉线"。

背景:api/square.py 五路由完整、main.py 连 import 都没有,论坛静默死亡无巡检发现
(2026-10-01 用户质询"论坛还有吗"实锤)。机制不会消失,只会掉线——本脚本每日对账:
  A. main.py 声明的 import(如 api.X)是否有对应 include_router(挂载丢失=红灯)
  B. api/*.py 定义了 router 的文件,哪些从未被 main.py import(孤儿 router=登记)

用法: python ops/endpoint_audit.py        # 打印报告(供 frame_snapshot 调)
       python ops/endpoint_audit.py --json # JSON 行输出
退出码: 0=无红灯; 2=有 import 未挂载(需修复)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
MAIN = BACKEND / "main.py"


def _router_modules() -> set[str]:
    """api/ 下定义了 router 的模块名。"""
    out = set()
    for f in (BACKEND / "api").glob("*.py"):
        if f.name.startswith("_") or f.name.endswith(".disabled"):
            continue
        try:
            if re.search(r"^\s*router\s*=\s*APIRouter", f.read_text(encoding="utf-8", errors="ignore"), re.M):
                out.add(f.stem)
        except OSError:
            continue
    return out


def audit(main_text: str | None = None) -> dict:
    text = main_text if main_text is not None else MAIN.read_text(encoding="utf-8", errors="ignore")
    # import 行(含 try 块缩进形态,session_context 等 5 例实证): from api.X import router as Y_router
    imports = dict(re.findall(r"^\s*from api\.(\w+) import router as (\w+)", text, re.M))
    # include 行(含缩进): include_router(Y_router ...) —— 取调用名首参
    included = set(re.findall(r"include_router\((\w+)", text))
    unmounted = sorted(as_name for mod, as_name in imports.items() if as_name not in included)
    orphans = sorted(_router_modules() - set(imports))
    return {"imported": len(imports), "unmounted": unmounted, "orphan_modules": orphans}


def main() -> int:
    rep = audit()
    if "--json" in sys.argv:
        print(json.dumps(rep, ensure_ascii=False))
    else:
        print(f"endpoint_audit: imported={rep['imported']} "
              f"unmounted={rep['unmounted'] or '无'} orphan_modules={rep['orphan_modules'] or '无'}")
        for m in rep["unmounted"]:
            print(f"  🔴 import 未挂载: api.{m} (接线丢失,红灯)")
        for m in rep["orphan_modules"]:
            print(f"  🟡 孤儿 router 模块: api/{m}.py 从未被 main.py import")
    return 2 if rep["unmounted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
