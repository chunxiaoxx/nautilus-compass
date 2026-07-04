# -*- coding: utf-8 -*-
"""dialog_bootstrap.py - 5 dialog 补齐(治根 anchor #6)

跑这 1 脚本 = 4 dialog 各补:
1. .claude/memory/ 目录(若不存在)
2. 第 1 个 session memory 落档(从 ops/templates/session_memory_template.md 复制 + 替换 <DIALOG_NAME> placeholder)
3. 不重写已有 memory
4. 不动其他 dialog 的非 .claude/ 文件

复用 anchor #5(不动其他 dialog 的 hook · 只增不替)。
"""
import shutil
from pathlib import Path

DIALOGS = {
    "v5":     r"C:\Users\chunx\Projects\nautilus-v5",
    "core":   r"C:\Users\chunx\Projects\nautilus-core",
    "buyer":  r"C:\Users\chunx\Projects\nautilus-compass-buyer-tasks",
    "expert": r"C:\Users\chunx\Projects\nautilus-compass-expert-settle",
}
TEMPLATE_PATH = Path(r"C:\Users\chunx\Projects\nautilus-compass\ops\templates\session_memory_template.md")


def bootstrap_one(name: str, root: str) -> str:
    """给 1 个 dialog 补 .claude/memory/ + 落档 session memory。

    若已存在 memory 落档则跳过(spec 要求"补齐",不重复造轮)。
    """
    p = Path(root)
    if not p.exists():
        return f"SKIP: {name} 不存在"
    mem_dir = p / ".claude" / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    target = mem_dir / f"session_20260704_{name}_bootstrap.md"
    if target.exists():
        return f"SKIP: {name} memory 已存在 = {target.name}"
    if not TEMPLATE_PATH.exists():
        return f"FAIL: 模板不存在 = {TEMPLATE_PATH}"
    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    # 替换 <DIALOG_NAME> placeholder
    content = content.replace("<DIALOG_NAME>", name)
    target.write_text(content, encoding="utf-8")
    return f"OK: {name} memory 落档 = {target.name}"


def main() -> int:
    for name, root in DIALOGS.items():
        print(bootstrap_one(name, root))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())