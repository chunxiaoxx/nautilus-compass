# Hook + 提示词机制保障 GOAL Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 compass 项目里 ship 3 件 hook(SessionStart + PostToolUse + Stop)+ settings.json 注册 + GOAL_PROMPT 加 3 档 alert 段,机器层 + 人治文双保险治 GOAL 不漏事。

**Architecture:** 复用现有 4 个 hook 架构(anchor #5)· 加 2 个新 hook 文件(SessionStart + PostToolUse)· 扩 Stop hook 加 session memory 落档 check · settings.json 注册 · GOAL_PROMPT 文档加 3 档 alert 段 · 不重写任何已有 hook。

**Tech Stack:** Python 3.13 + Bash (Windows Git Bash) + JSON config

---

### Task 1: SessionStart hook 骨架 · compass_session_start.py

**Files:**
- Create: `C:\Users\chunx\.claude\hooks\compass_session_start.py`
- Test: 真跑验证

**Step 1: 写骨架 + 核 cwd 必为 compass**

```python
"""compass SessionStart hook · 核身份 + 读 Goal + 3 档 alert 注入。

每 session-start 自动:
1. 核 cwd 必须 = nautilus-compass(否则 fail-stop 退出非 0)
2. 读 NEW_SESSION_START.md + GOAL_PROMPT_20260704.md
3. 注入 3 档 alert(超红/红/黄)到 context
4. 推 .seen_compass watermark
5. 检查 8 件漏掉事是否做了(兜底)

Input: JSON via stdin({cwd, hook_event_name, session_id})
Output: stderr 注入 3 档 alert(Claude 可见)
Exit: 0 always(默认不阻断)· 核身份 fail 才 exit 1
"""
import json
import os
import sys
from pathlib import Path

EXPECTED_CWD = "nautilus-compass"
PROJECT_ROOT = Path(r"C:\Users\chunx\Projects\nautilus-compass")
NEW_SESSION_START = PROJECT_ROOT / "NEW_SESSION_START.md"
GOAL_PROMPT = PROJECT_ROOT / "GOAL_PROMPT_20260704.md"

ALERTS_RED = [
    "超红:越界写非 compass 项目文件(必须 pwd 核身份)",
    "超红:不写 .claude/memory/session_*.md 就 Stop",
    "超红:drift score < -0.07(R1 立停)",
]
ALERTS_YELLOW = [
    "黄:不读 auto_surface_hook / 不读 NEW_SESSION_START / 不核身份",
    "黄:段落超 8 行 / '真'字 ≥ 3",
    "黄:不写 session memory 落档",
]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    cwd = data.get("cwd", os.getcwd())
    if EXPECTED_CWD not in cwd:
        sys.stderr.write(f"[compass-hook] FAIL: cwd={cwd} 不含 {EXPECTED_CWD}\n")
        return 1
    for path in (NEW_SESSION_START, GOAL_PROMPT):
        if not path.exists():
            sys.stderr.write(f"[compass-hook] 缺文件: {path}\n")
    for a in ALERTS_RED:
        sys.stderr.write(f"[compass-alert] 🚨 {a}\n")
    for a in ALERTS_YELLOW:
        sys.stderr.write(f"[compass-alert] 🟡 {a}\n")
    sys.stderr.write(f"[compass-hook] OK cwd={cwd}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: 真跑验证**(`cwd=nautilus-compass` 应 exit 0)

```bash
echo '{"cwd": "C:\\Users\\chunx\\Projects\\nautilus-compass"}' | py -3 C:/Users/chunx/.claude/hooks/compass_session_start.py
echo "exit=$?"
```

Expected: exit=0 + 3 红 + 3 黄 alert 全打印

**Step 3: 真跑 fail 路径**(cwd 不含 nautilus-compass 应 exit 1)

```bash
echo '{"cwd": "C:\\Users\\chunx\\Projects\\nautilus-v5"}' | py -3 C:/Users/chunx/.claude/hooks/compass_session_start.py
echo "exit=$?"
```

Expected: exit=1 + "FAIL: cwd=... 不含 nautilus-compass" 打印

**Step 4: Commit**

```bash
git add /c/Users/chunx/.claude/hooks/compass_session_start.py
cd /c/Users/chunx/Projects/nautilus-compass && git commit -m "feat(hook): compass SessionStart 核身份 + 3 档 alert"
```

---

### Task 2: PostToolUse hook · compass_post_tool.py

**Files:**
- Create: `C:\Users\chunx\.claude\hooks\compass_post_tool.py`

**Step 1: 写骨架**

```python
"""compass PostToolUse hook · Write/Edit/MultiEdit 触发 · 验路径 + 跨边界 + 内存落档。

Write/Edit 触发:
1. 验路径在 nautilus-compass/ 内(否则 fail-stop 退出非 0)
2. 验不是 _OUTBOUND_FROM_PLATFORM_*(越权冒充)
3. session-end:验 .claude/memory/session_*.md 1 个本 session 写过(否则 alert)

Input: JSON via stdin({tool_name, tool_input{file_path,...}, session_id})
Output: stderr reminder(Claude 可见)· 非命中静默
Exit: 0 always(默认不阻断)· 越界 fail-stop
"""
import json
import os
import re
import sys
from pathlib import Path

ALLOWED_ROOT = Path(r"C:\Users\chunx\Projects\nautilus-compass")
MEMORY_DIR = ALLOWED_ROOT / ".claude" / "memory"

FORBIDDEN_PATTERNS = [
    re.compile(r"_OUTBOUND_FROM_PLATFORM_", re.IGNORECASE),  # 不冒充 platform-soul
    re.compile(r"_OUTBOUND_FROM_AGENT_", re.IGNORECASE),     # 不冒充 v5
    re.compile(r"_OUTBOUND_FROM_FDE_", re.IGNORECASE),        # 不冒充 FDE
]


def main() -> int:
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

    # 1. 路径必须在 nautilus-compass 内
    try:
        p = Path(file_path).resolve()
        if not str(p).startswith(str(ALLOWED_ROOT)):
            sys.stderr.write(f"[compass-post] FAIL: 越界写 {file_path}\n")
            return 1
    except Exception:
        pass

    # 2. 禁止冒充其他 dialog 写 OUTBOUND
    name = Path(file_path).name
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(name):
            sys.stderr.write(f"[compass-post] FAIL: 禁止冒充 pattern={pat.pattern}\n")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: 真跑验证(Write 写 compass 内文件应 exit 0)**

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"C:\\Users\\chunx\\Projects\\nautilus-compass\\test.txt"}}' | py -3 C:/Users/chunx/.claude/hooks/compass_post_tool.py
echo "exit=$?"
```

Expected: exit=0

**Step 3: 真跑越界(写 v5 内文件应 exit 1)**

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"C:\\Users\\chunx\\Projects\\nautilus-v5\\test.txt"}}' | py -3 C:/Users/chunx/.claude/hooks/compass_post_tool.py
echo "exit=$?"
```

Expected: exit=1 + "越界写" 打印

**Step 4: 真跑冒充(写 _OUTBOUND_FROM_PLATFORM_*.md 应 exit 1)**

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"C:\\Users\\chunx\\Projects\\nautilus-compass\\_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_9999.md"}}' | py -3 C:/Users/chunx/.claude/hooks/compass_post_tool.py
echo "exit=$?"
```

Expected: exit=1 + "禁止冒充" 打印

**Step 5: Commit**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
git add /c/Users/chunx/.claude/hooks/compass_post_tool.py
git commit -m "feat(hook): compass PostToolUse 验越界 + 防冒充"
```

---

### Task 3: settings.json 注册 2 个新 hook

**Files:**
- Modify: `C:\Users\chunx\.claude\settings.json`

**Step 1: 看 settings.json 当前 hooks 段(找 UserPromptSubmit 旁加)**

读 `~/.claude/settings.json` 找 hooks 段,在 UserPromptSubmit 旁加 2 个新 hook:

```json
"SessionStart": [
  {
    "matcher": ".*",
    "hooks": [
      {
        "type": "command",
        "command": "py -3 C:/Users/chunx/.claude/hooks/preserve_hud_on_model_switch.py",
        "timeout": 5
      },
      {
        "type": "command",
        "command": "py -3 C:/Users/chunx/.claude/hooks/compass_session_start.py",
        "timeout": 10
      }
    ]
  }
],
"PostToolUse": [
  {
    "matcher": "Write|Edit|MultiEdit",
    "hooks": [
      {
        "type": "command",
        "command": "py -3 C:/Users/chunx/.claude/hooks/compass_post_tool.py",
        "timeout": 6,
        "async": true
      }
    ]
  }
]
```

**Step 2: Edit 写入**

用 Edit 工具精确替换 SessionStart 的 hooks list + 替换 PostToolUse 的 hooks list(已有其他 hook 不动)。

**Step 3: 验证 JSON 合法 + 现有 hook 没被破坏**

```bash
python -c "import json; s=json.load(open(r'C:\Users\chunx\.claude\settings.json', encoding='utf-8')); h=s.get('hooks',{}); print('SessionStart:', len(h.get('SessionStart',[]))); print('PostToolUse:', len(h.get('PostToolUse',[]))); print('PreToolUse:', len(h.get('PreToolUse',[]))); print('Stop:', len(h.get('Stop',[])))"
```

Expected: SessionStart ≥ 1 · PostToolUse ≥ 1 · PreToolUse/Stop 不动

**Step 4: Commit**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
git add /c/Users/chunx/.claude/settings.json  # 注意:这不是我的项目,但 hook 是用户级
# 实际上 ~/.claude/settings.json 是用户级,git 跟踪在哪?
ls -la ~/.claude/settings.json
# 如果没跟踪:不 commit,只写到 ~/.claude/settings.json
```

注:`~/.claude/settings.json` 是用户级 · 不归 compass 项目 · **不 commit**(如果 git 跟踪就 add + commit,否则跳过)

---

### Task 4: GOAL_PROMPT.md 加 3 档 alert 段

**Files:**
- Modify: `C:\Users\chunx\Projects\nautilus-compass\GOAL_PROMPT_20260704.md`

**Step 1: Edit 添加 3 档 alert 段**

在 GOAL_PROMPT.md "Drift 自检" 段后添加:

```markdown

## 🚨 3 档 alert 契约(必检)

### 超红(🚨 立刻 stop)
- 越界写非 compass 项目文件(必须 pwd 核身份)
- 不写 .claude/memory/session_*.md 就 Stop
- drift score < -0.07(R1 立停 · 不靠自律)

### 红(🔴 本次响应必检)
- 段落超 8 行
- "真"字 ≥ 3 / 段
- 越权改 SSOT 副本(只改 canonical core)
- 堆 dense markdown 表格
- 不读 NEW_SESSION_START.md 就答"接住主线"

### 黄(🟡 本 turn 提醒)
- 不读 auto_surface_hook 推 watermark
- 不读 GOAL_PROMPT
- 不核身份
- 不写 session memory 落档
- 不验 v5 真 trajectory v7 字段就 ship
```

**Step 2: 验证 3 档 alert 段在文档里**

```bash
grep -c "超红\|红\|黄" GOAL_PROMPT_20260704.md
```

Expected: ≥ 10 命中

**Step 3: Commit**

```bash
cd /c/Users/chunx/Projects/nautilus-compass
git add GOAL_PROMPT_20260704.md
git commit -m "feat(goal): 3 档 alert 契约加 GOAL_PROMPT"
```

---

### Task 5: Stop hook 加 session memory 落档 check(扩 path_b_session_audit)

**Files:**
- Modify: `C:\Users\chunx\.claude\hooks\path_b_session_audit.py`

**Step 1: 读现有文件找 anchor 加新逻辑**

读 `~/.claude/hooks/path_b_session_audit.py` · 在 main() 末尾加 session memory 落档 check:

```python
# 新增:session-end 兜底 check
import os
from datetime import datetime, timezone, timedelta

def check_session_memory_fallback():
    """session-end 兜底:本 session 写过 .claude/memory/session_*.md?
    
    取 6h 内最新 .md 文件,看 mtime < 6h → 写过了 = OK
    否则 alert "session memory 未落档"
    """
    mem_dir = Path(r"C:\Users\chunx\Projects\nautilus-compass\.claude\memory")
    if not mem_dir.exists():
        return "FAIL: .claude/memory/ 不存在"
    threshold = datetime.now().timestamp() - 6 * 3600
    fresh = []
    for md in mem_dir.glob("session_*.md"):
        if md.stat().st_mtime > threshold:
            fresh.append(md.name)
    if not fresh:
        return f"WARN: 6h 内无 session_*.md 落档 · 8 件漏掉事复发风险"
    return f"OK: 最近 session memory = {fresh[-1]}"
```

**Step 2: 在 main() 末尾追加调用**

```python
# main() 末尾(原有 Path B audit 后):
print(check_session_memory_fallback())
```

**Step 3: 真跑验证**

```bash
py -3 C:/Users/chunx/.claude/hooks/path_b_session_audit.py < /dev/null
```

Expected: 输出含 "OK: 最近 session memory" 或 "WARN: 6h 内无"(按真状态)

**Step 4: Commit(若 git 跟踪)**

```bash
# ~/.claude/hooks/ 是否在 compass 项目内?
ls /c/Users/chunx/Projects/nautilus-compass/.claude/hooks/ 2>&1
# 不在 → 不 commit,只写到 ~/.claude/hooks/
```

---

### Task 6: 端到端验证

**Step 1: 模拟 1 次 session-start**

```bash
echo '{"cwd":"C:\\Users\\chunx\\Projects\\nautilus-compass"}' | py -3 C:/Users/chunx/.claude/hooks/compass_session_start.py 2>&1 | head -15
```

Expected: 6 行 alert + 1 行 OK

**Step 2: 模拟 1 次 PostToolUse Write 合法**

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"C:\\Users\\chunx\\Projects\\nautilus-compass\\test.txt"}}' | py -3 C:/Users/chunx/.claude/hooks/compass_post_tool.py
echo "exit=$?"
```

Expected: exit=0

**Step 3: 模拟 1 次 PostToolUse Write 越界**

```bash
echo '{"tool_name":"Write","tool_input":{"file_path":"C:\\Users\\chunx\\Projects\\nautilus-v5\\test.txt"}}' | py -3 C:/Users/chunx/.claude/hooks/compass_post_tool.py
echo "exit=$?"
```

Expected: exit=1 + "越界写"

**Step 4: 检查 settings.json 真生效**

```bash
cat ~/.claude/settings.json | grep -E "compass_session_start|compass_post_tool"
```

Expected: 2 行命中

**Step 5: 最终验证总结**

| Hook | 真跑结果 | 期望 |
|---|---|---|
| compass_session_start.py (cwd=compass) | exit=0 + 6 alert | ✅ |
| compass_session_start.py (cwd=v5) | exit=1 + FAIL | ✅ |
| compass_post_tool.py (写 compass) | exit=0 | ✅ |
| compass_post_tool.py (写 v5) | exit=1 | ✅ |
| compass_post_tool.py (冒充 OUTBOUND) | exit=1 | ✅ |
| path_b_session_audit.py (session memory check) | 输出含 OK/WARN | ✅ |

---

## 执行时间表(总 75 分钟)

- Task 1:20 分钟
- Task 2:15 分钟
- Task 3:10 分钟
- Task 4:5 分钟
- Task 5:15 分钟
- Task 6:10 分钟

## 不撞红线

- 不重写 4 个已有 hook(SessionStart/PostToolUse/PreToolUse/Stop)
- 不替用户决策(用户勾了才动)
- 不堆 dense markdown(本计划用代码块 + 表)

---

*Plan 定稿:2026-07-04 01:55 PDT · 75 分钟 ship 清单 · 等用户选 subagent-driven 或 parallel session*