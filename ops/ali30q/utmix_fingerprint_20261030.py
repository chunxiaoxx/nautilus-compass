#!/usr/bin/env python3
"""UTMIX tests 指纹生成器(23984 回函件·compass 侧四题 CS-301/502/511/512)。

口径(显式声明,与 v5 三题口径未校验):
- 范围:items/<题>/tests/ 递归全部 *.py + *.md,外加顶层 conftest.py、pytest.ini(存在才计)
- 排除:__pycache__、.pytest_cache、_s5、_judge、evidence、counterexamples、solution、environment
- 算法:按相对路径排序,拼接 "relpath:md5hex\n",整体 md5 取前 12 位
- 附同口径 CS-001 读数一行供 v5 校验口径同源性(v5 函给值 953fc35366e1 算法未知)

用法: python3 utmix_fingerprint_20261030.py [ITEMS_DIR]
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

DEFAULT_ITEMS = os.path.expanduser(
    "~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items"
)
TARGET_ITEMS = ["CS-301", "CS-502", "CS-511", "CS-512"]
CROSSCHECK = "CS-001"  # v5 给值 953fc35366e1,用于口径校验
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "_s5", "_judge", "evidence",
                "counterexamples", "solution", "environment", ".git"}


def collect(item_dir: str) -> list[tuple[str, str]]:
    """收集 (relpath, abspath),仅 tests/ 递归 py+md + 顶层 conftest.py/pytest.ini。"""
    out: list[tuple[str, str]] = []
    tests = os.path.join(item_dir, "tests")
    if os.path.isdir(tests):
        for root, dirs, files in os.walk(tests):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f.endswith((".py", ".md")):
                    p = os.path.join(root, f)
                    out.append((os.path.relpath(p, item_dir), p))
    for top in ("conftest.py", "pytest.ini"):
        p = os.path.join(item_dir, top)
        if os.path.isfile(p):
            out.append((top, p))
    return sorted(out)


def fingerprint(item_dir: str) -> tuple[str, int]:
    fs = collect(item_dir)
    blob = "".join(
        f"{rel}:{hashlib.md5(open(p, 'rb').read()).hexdigest()}\n" for rel, p in fs
    )
    return hashlib.md5(blob.encode()).hexdigest()[:12], len(fs)


def main() -> int:
    items_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ITEMS
    result = {
        "schema": "utmix-tests-fingerprint-v1",
        "issued_by": "compass R226",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "items_root": items_dir,
        "口径": "tests/递归py+md+conftest.py+pytest.ini·排除产物目录·relpath排序·md5(concat(relpath:md5))前12位",
        "口径校验说明": "v5 函 23984 三题指纹算法未公开,本表四题用本口径,附 CS-001 同口径读数供 v5 复算比对;不一致则以 v5 命令为准重出",
        "fingerprints": {},
    }
    for t in TARGET_ITEMS + [CROSSCHECK]:
        d = os.path.join(items_dir, t)
        if not os.path.isdir(d):
            result["fingerprints"][t] = {"error": "items 目录不存在"}
            continue
        fp, n = fingerprint(d)
        entry = {"md5_12": fp, "files": n}
        if t == CROSSCHECK:
            entry["v5_given"] = "953fc35366e1"
            entry["match"] = fp == "953fc35366e1"
        result["fingerprints"][t] = entry

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "UTMIX_FINGERPRINT_COMPASS_20261030.json")
    with open(out_path, "w") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    for t, e in result["fingerprints"].items():
        print(t, e)
    print("saved:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
