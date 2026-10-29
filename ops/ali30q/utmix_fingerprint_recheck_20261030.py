#!/usr/bin/env python3
"""UTMIX tests 指纹复核(24001 回函件·compass 侧)。

背景:24001 v5 承认此前差异根因=按"目录整体md5"非逐文件列表,已改用与
compass 相同口径重出 CS-001/004/008;请 compass ①按同口径复核前三题
②重出四题(CS-301/502/511/512)。v5 脚本(codesense/tools/_tests_fingerprint.py)
commit 随下一批尚未到位,本轮按 24001 函内明文口径等价实现:
- 范围:items/<题>/tests/ 递归全部 *.py + *.md(不含顶层 conftest.py/pytest.ini
  ——与 R226 版唯一差异,R226 28 files vs v5 26 files 差 2 恰为此二件)
- 排除:__pycache__/.pytest_cache/_s5/_judge/evidence/counterexamples/
  solution/environment/.git
- 算法:relpath 排序,"relpath:md5hex\n" 拼接,整体 md5 前 12 位

用法: python3 utmix_fingerprint_recheck_20261030.py [ITEMS_DIR]
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

DEFAULT_ITEMS = os.path.expanduser(
    "~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items"
)
TARGET_ITEMS = ["CS-001", "CS-004", "CS-008", "CS-301", "CS-502", "CS-511", "CS-512"]
V5_GIVEN = {
    "CS-001": "7b1585d1be46",
    "CS-004": "a18ced39057e",
    "CS-008": "f23ee3851ac4",
}
EXCLUDE_DIRS = {"__pycache__", ".pytest_cache", "_s5", "_judge", "evidence",
                "counterexamples", "solution", "environment", ".git"}


def fingerprint(item_dir: str) -> tuple[str, int]:
    """v5 函 24001 口径:仅 tests/ 递归 py+md。"""
    tests = os.path.join(item_dir, "tests")
    fs: list[tuple[str, str]] = []
    if os.path.isdir(tests):
        for root, dirs, files in os.walk(tests):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f.endswith((".py", ".md")):
                    p = os.path.join(root, f)
                    fs.append((os.path.relpath(p, item_dir), p))
    fs.sort()
    blob = "".join(
        f"{rel}:{hashlib.md5(open(p, 'rb').read()).hexdigest()}\n" for rel, p in fs
    )
    return hashlib.md5(blob.encode()).hexdigest()[:12], len(fs)


def main() -> int:
    items_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ITEMS
    result = {
        "schema": "utmix-tests-fingerprint-v1-recheck",
        "issued_by": "compass R228",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "items_root": items_dir,
        "口径": "tests/递归py+md(不含顶层conftest.py/pytest.ini)·排除产物目录·relpath排序·md5(concat(relpath:md5))前12位",
        "口径依据": "24001 函内明文口径等价实现(v5 脚本 commit 随下一批未到位);与 R226 版唯一差异=不含顶层两文件",
        "fingerprints": {},
    }
    all_match = True
    for t in TARGET_ITEMS:
        d = os.path.join(items_dir, t)
        if not os.path.isdir(d):
            result["fingerprints"][t] = {"error": "items 目录不存在"}
            all_match = False
            continue
        fp, n = fingerprint(d)
        entry = {"md5_12": fp, "files": n}
        if t in V5_GIVEN:
            entry["v5_given_24001"] = V5_GIVEN[t]
            entry["match"] = fp == V5_GIVEN[t]
            all_match = all_match and entry["match"]
        result["fingerprints"][t] = entry

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "UTMIX_FINGERPRINT_RECHECK_20261030.json")
    with open(out_path, "w") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    for t, e in result["fingerprints"].items():
        print(t, e)
    print("ALL_MATCH:", all_match)
    print("saved:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
