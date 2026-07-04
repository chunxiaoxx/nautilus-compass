# 5 Dialog 补齐 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 写 1 个 dialog_bootstrap.py 工具,自动给 4 个 dialog(v5/core/buyer/expert)补 .claude/memory/ + 复制 2 个 hook 模板(改 EXPECTED_CWD + ALLOWED_ROOT),20 分钟 ship。

**Architecture:** 模板分发 = compass 已有真资源(memory + hook + GOAL_PROMPT)→ 复制到 4 dialog 各自项目内,改 path 变量,跑 audit 验证。anchor #5 复用不重写。

**Tech Stack:** Python 3.13 + pathlib + shutil + cross_dialog_audit.py 已 ship

---

### Task 1: 写 session memory 模板

**Files:**
- Create: `C:\Users\chunx\Projects\nautilus-compass\ops\templates\session_memory_template.md`

**Step 1: 写模板(其他 dialog 复用)**

```markdown
---
name: session_20260704_<DIALOG_NAME>_bootstrap
description: <DIALOG_NAME> dialog 7/4 bootstrap 第一次真落档 memory(anchor #6 治根)· 真状态 5 dialog 14d 60 commits · compass ABC 三件 + 3 档 alert + auto_surface_hook
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# <DIALOG_NAME> Dialog Bootstrap · 7/4

> 🔴 **本档是 <DIALOG_NAME> 6 周以来第一次真 memory 落档**(compass 7/4 01:30 治根方法复制)

## 5 Dialog 14d 真 sync 结果(60 commits)

| Dialog | commits(14d) | memory | dirty |
|---|---|---|---|
| compass | 20 | ✅ 1 | 5 files |
| v5 | 20 | ❌(本档补) | 3 |
| core | 20 | ❌(本档补) | 5 |
| buyer | 0 (非 git) | ❌ | 1 |
| expert | 0 (非 git) | ❌ | 1 |

## <DIALOG_NAME> 7/4 真状态

(本 dialog 真 commit + 真文件落档状态 · 7/4 后必续)

## 关联

- compass/.claude/memory/session_20260704_compass_genopt_main_loop_handoff_continuation.md
- GOAL_PROMPT_20260704.md · 3 档 alert 契约
- auto_surface_hook.py · 76 条 inbound 真消费
- cross_dialog_audit.py · 5 dialog 14d 60 commits 真扫
```

**Step 2: 真创建**

```bash
mkdir -p /c/Users/chunx/Projects/nautilus-compass/ops/templates
```

**Step 3: 真验证文件存在**

```bash
ls -la /c/Users/chunx/Projects/nautilus-compass/ops/templates/
```

Expected: `session_memory_template.md` 真在

**Step 4: Commit**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
git add ops/templates/session_memory_template.md
git commit -m "feat(compass): session memory 模板(5 dialog 复用)"
```

---

### Task 2: 写 hook 模板生成函数

**Files:**
- Create: `C:\Users\chunx\Projects\nautilus-compass\ops\hook_template.py`

**Step 1: 写骨架**

```python
# -*- coding: utf-8 -*-
"""hook_template.py - 给 4 dialog 各生成定制 hook(改 EXPECTED_CWD + ALLOWED_ROOT)"""
import shutil
from pathlib import Path

def gen_session_start_hook(dialog_name: str, dialog_root: str) -> str:
    """返 dialog 专属 SessionStart hook 内容。"""
    return '''# -*- coding: utf-8 -*-
"""''' + dialog_name + ''' SessionStart hook - 核 cwd + 3 档 alert

从 compass/ops/compass_session_start.py 复制 + 改 EXPECTED_CWD
"""
import json
import os
import sys

EXPECTED_CWD = "''' + dialog_root.split(chr(92))[-1] + '''"
PROJECT_ROOT = Path(r"''' + dialog_root + '''")

ALERTS_RED = [
    "超红: 越界写非 ''' + dialog_name + ''' 项目文件",
    "超红: 不写 .claude/memory/session_*.md 就 Stop",
    "超红: drift score < -0.07(R1 立停)",
]
ALERTS_YELLOW = [
    "黄: 不读 auto_surface_hook / 不读 NEW_SESSION_START / 不核身份",
    "黄: 段落超 8 行 / '真'字 >= 3",
    "黄: 不写 session memory 落档",
]

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    cwd = data.get("cwd", os.getcwd())
    if EXPECTED_CWD not in cwd:
        sys.stderr.write("[" + EXPECTED_CWD + "-hook] FAIL: cwd=" + cwd + " 不含 " + EXPECTED_CWD + "\\n")
        return 1
    for a in ALERTS_RED:
        sys.stderr.write("[" + EXPECTED_CWD + "-alert] [超红] " + a + "\\n")
    for a in ALERTS_YELLOW:
        sys.stderr.write("[" + EXPECTED_CWD + "-alert] [黄] " + a + "\\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


def gen_post_tool_hook(dialog_name: str, dialog_root: str) -> str:
    """返 dialog 专属 PostToolUse hook 内容。"""
    return '''# -*- coding: utf-8 -*-
"""''' + dialog_name + ''' PostToolUse hook - 验越界 + 防冒充"""
import json
import re
import sys
from pathlib import Path

ALLOWED_ROOT = Path(r"''' + dialog_root + '''")

FORBIDDEN_PATTERNS = [
    re.compile(r"_OUTBOUND_FROM_(?!''' + dialog_name.upper() + '''_)", re.IGNORECASE),
]

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool = data.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return 0
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0
    p = Path(file_path).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT)):
        sys.stderr.write("[" + ''' + dialog_name + ''' + "-post] FAIL: 越界写 " + file_path + "\\n")
        return 1
    name = Path(file_path).name
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(name):
            sys.stderr.write("[" + ''' + dialog_name + ''' + "-post] FAIL: 禁止冒充 pattern=" + pat.pattern + "\\n")
            return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


def main():
    dialogs = {
        "v5":     r"C:\Users\chunx\Projects\nautilus-v5",
        "core":   r"C:\Users\chunx\Projects\nautilus-core",
        "buyer":  r"C:\Users\chunx\Projects\nautilus-compass-buyer-tasks",
        "expert": r"C:\Users\chunx\Projects\nautilus-compass-expert-settle",
    }
    for name, root in dialogs.items():
        p = Path(root) / ".claude" / "hooks"
        p.mkdir(parents=True, exist_ok=True)
        for kind, fn in [("session_start", gen_session_start_hook), ("post_tool", gen_post_tool_hook)]:
            (p / f"{name}_{kind}_hook.py").write_text(fn(name, root), encoding="utf-8")
            print(f"OK: {name} {kind} hook")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: 真跑生成 8 个 hook 模板**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
python ops/hook_template.py
```

Expected: 8 行 "OK: <dialog> <kind> hook"

**Step 3: 真验证 4 dialog 都有 hook**

```bash
for d in nautilus-v5 nautilus-core nautilus-compass-buyer-tasks nautilus-compass-expert-settle; do
  echo "===$d==="; ls "$d/.claude/hooks/" 2>&1
done
```

Expected: 每个 dialog 2 个 hook(buyer/expert 非 git repo 但 .claude/hooks/ 仍可创建)

**Step 4: Commit**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
git add ops/hook_template.py
git commit -m "feat(compass): hook 模板生成器(4 dialog × 2 hook)"
```

---

### Task 3: 写 dialog_bootstrap.py 主脚本

**Files:**
- Create: `C:\Users\chunx\Projects\nautilus-compass\ops\dialog_bootstrap.py`

**Step 1: 写骨架**

```python
# -*- coding: utf-8 -*-
"""dialog_bootstrap.py - 5 dialog 补齐(治根 #6)

跑这 1 脚本 = 4 dialog 各补:
1. .claude/memory/ 目录 + 第 1 个 session memory 落档
2. 2 个 hook(SessionStart + PostToolUse)定制版
3. 不改其他文件

不重写其他 dialog 的 hook(只增不替)。
"""
import shutil
from pathlib import Path

DIALOGS = {
    "v5":     r"C:\Users\chunx\Projects\nautilus-v5",
    "core":   r"C:\Users\chunx\Projects\nautilus-core",
    "buyer":  r"C:\Users\chunx\Projects\nautilus-compass-buyer-tasks",
    "expert": r"C:\Users\chunx\Projects\nautilus-compass-expert-settle",
}
TEMPLATE_DIR = Path(r"C:\Users\chunx\Projects\nautilus-compass\ops\templates")
HOOK_TEMPLATE = Path(r"C:\Users\chunx\Projects\nautilus-compass\ops\hook_template.py")


def main():
    template = (TEMPLATE_DIR / "session_memory_template.md").read_text(encoding="utf-8")
    results = []
    for name, root in DIALOGS.items():
        p = Path(root)
        if not p.exists():
            results.append(f"SKIP: {name} 不存在")
            continue
        # 1. 补 .claude/memory/
        mem = p / ".claude" / "memory"
        mem.mkdir(parents=True, exist_ok=True)
        content = template.replace("<DIALOG_NAME>", name)
        target = mem / f"session_20260704_{name}_bootstrap.md"
        if not target.exists():
            target.write_text(content, encoding="utf-8")
            results.append(f"OK {name}: memory 落档 = {target.name}")
        else:
            results.append(f"SKIP {name}: memory 已存在")
        # 2. 跑 hook_template.py
        # 已在 Task 2 跑过
    return results


if __name__ == "__main__":
    for r in main():
        print(r)
```

**Step 2: 真跑**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
python ops/dialog_bootstrap.py
```

Expected: 4 行 "OK <dialog>: memory 落档" 或 SKIP

**Step 3: 真验证 4 dialog 都有 .claude/memory/session_*.md**

```bash
for d in nautilus-v5 nautilus-core nautilus-compass-buyer-tasks nautilus-compass-expert-settle; do
  echo "===$d==="; ls -la "$d/.claude/memory/" 2>&1
done
```

Expected: 每个 dialog 1 个 session_20260704_*.md

**Step 4: Commit**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
git add ops/dialog_bootstrap.py
git commit -m "feat(compass): dialog_bootstrap.py 模板分发(4 dialog)"
```

---

### Task 4: 端到端验证(audit + 真列表)

**Step 1: 跑 cross_dialog_audit 14d**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
python ops/cross_dialog_audit.py 14 2>&1 | head -80
```

Expected: 4 dialog(v5/core/buyer/expert)memory 段都从"无"变 1 个 session memory

**Step 2: 真列 4 dialog memory 文件**

```bash
for d in nautilus-v5 nautilus-core nautilus-compass-buyer-tasks nautilus-compass-expert-settle; do
  echo "===$d==="; ls -la "/c/Users/chunx/Projects/$d/.claude/memory/" 2>&1
done
```

Expected: 4 个 dialog 各有 1 个 session_20260704_*_bootstrap.md

**Step 3: 真读 1 个 memory 验证内容**

```bash
cat /c/Users/chunx/Projects/nautilus-v5/.claude/memory/session_20260704_v5_bootstrap.md | head -20
```

Expected: 包含 "5 Dialog 14d 真 sync 结果" + "v5 7/4 真状态"

**Step 4: 最终验证表**

| Dialog | 修前 memory | 修后 memory | hook 数 |
|---|---|---|---|
| compass | 1 | 1 | 2 |
| v5 | 0 | 1 | 2 |
| core | 0 | 1 | 2 |
| buyer | 0 | 1 | 2 |
| expert | 0 | 1 | 2 |

总计 = 5/5 dialog 全有 memory + 10 个 hook 模板

---

## 执行时间表(总 20 分钟)

- Task 1:3 分钟
- Task 2:5 分钟
- Task 3:5 分钟
- Task 4:5 分钟
- commit + verify:2 分钟

## 不撞红线

- 不重写其他 dialog 的 hook(只增不替)
- 不改用户级 settings.json(用户自己决定是否注册)
- 不越界写其他 dialog 的非 .claude/ 文件

## 风险

- 4 dialog 的 .claude/hooks/ 是新目录,用户级 settings.json 需手动注册才能生效
- 但 4 dialog 各自 .claude/memory/ 落档是 0 风险(本地新文件)

---

*Plan 定稿:2026-07-04 02:15 PDT · 20 分 ship 清单 · 等用户选 subagent-driven 或 parallel session*