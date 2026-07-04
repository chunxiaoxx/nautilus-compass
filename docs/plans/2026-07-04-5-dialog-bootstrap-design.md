# 5 Dialog 补齐设计文档 · 2026-07-04

> 🎯 **用户原话"5 dialog 补齐"= 治根** = 每个 dialog 都有 .claude/memory/ + 注册 hook(治本 + 治未病)
> 设计:compass 已 ship(ABC 三件 + 端到端真验证 5 步全过)· 4 个 dialog(v5/core/soul/FDE)需要补齐

## 🧠 核心判断

按 anchor #6 治根 · 5 dialog 跨 6 周没 .claude/memory/(compass 7/4 第一次真写)= 5 dialog 都没真 memory = **复发根因**。
**治根 = 不靠自律 = hook 自动 + 工具自动 + 模板自动**。

## 🧭 3 方案对比(推荐方案 A · 模板分发)

### 方案 A · 模板分发(推荐 ⭐)

**思路**:写 1 个 `dialog_bootstrap.py` 工具 · 1 脚本自动给 4 个 dialog 补 .claude/memory/ + 推荐 hook + 关联 SSOT + 关联 GOAL_PROMPT。
**优点**:1 个脚本 1 次跑完 4 dialog · 不写 4 套配置
**缺点**:脚本需真测 · 失败回滚复杂
**耗时**:20 分钟 ship

### 方案 B · 4 个 dialog 各跑一遍 cross_dialog_audit + 写 memory

**思路**:每个 dialog 跑 audit 收集真状态 + 各写 1 个 session memory · 不改 hook。
**优点**:治根不强但 4 dialog 各有 memory
**缺点**:不补 hook = 下 session 仍易跑错 · 治标不治本
**耗时**:1 小时

### 方案 C · B + 自动 hook 注册脚本

**思路**:B 基础上 + 写 `install_dialog_hooks.py` 工具 · 给 4 dialog 注入 3 个 hook(SessionStart + PostToolUse + Stop)+ 注册到用户级 settings.json。
**优点**:B + hook 全套 = 真治根
**缺点**:脚本需测 + 风险更高(改其他 dialog 文件)
**耗时**:2 小时

## 🏗️ 设计 · 方案 A 真结构(本会话 ship 范围)

### 1. `compass/ops/dialog_bootstrap.py` · 模板分发工具

```python
"""dialog_bootstrap.py - 给 4 个 dialog(v5/core/soul/FDE)补 .claude/memory/ + 复制 hook。

4 dialog 各跑:
1. mkdir .claude/memory/(如不存在)
2. 复制 compass 真落档的 session memory 模板(参 GOAL_PROMPT_20260704.md)
3. 复制 3 个 hook(本 dialog 已 ship)· 改 cwd 路径 + 改 ALLOWED_ROOT
4. 提示用户到用户级 settings.json 注册(UserPromptSubmit + SessionStart + PostToolUse + Stop)
5. 写第 1 个 session memory(从本 dialog 真有数据填)

不重写已有 hook(只增不替)。
"""
import shutil
from pathlib import Path

DIALOGS = {
    "v5":     r"C:\Users\chunx\Projects\nautilus-v5",
    "core":   r"C:\Users\chunx\Projects\nautilus-core",
    "buyer":  r"C:\Users\chunx\Projects\nautilus-compass-buyer-tasks",
    "expert": r"C:\Users\chunx\Projects\nautilus-compass-expert-settle",
}
TEMPLATES = "compass/ops/templates/"

def bootstrap(name, path):
    p = Path(path)
    mem = p / ".claude" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    # 1. 复制 session memory 模板
    shutil.copy(TEMPLATES + "session_memory_template.md",
                mem / f"session_20260704_dialog_{name}_bootstrap.md")
    # 2. 复制 hook
    for hook in ("compass_session_start.py", "compass_post_tool.py"):
        shutil.copy(f"~/.claude/hooks/{hook}",
                    p / f".claude/hooks/{hook.replace('compass_', name + '_')}")
    return f"OK: {name} 补 .claude/memory/ + 2 hook 模板"

# 每 dialog 跑 + 写第 1 个 session memory
```

### 2. 真补 4 dialog

- v5 + core: 跑脚本 + 改 hook 的 `EXPECTED_CWD` / `ALLOWED_ROOT` 路径
- buyer + expert: 仅 .claude/memory/(非 git repo = 改 hook 没意义)

### 3. 验证

- 4 dialog 全有 .claude/memory/ = `cross_dialog_audit.py 14` 显示"有 memory 的 dialog:['compass','v5','core',...]"
- 4 dialog 各自 hook 真注册到用户级 settings.json

## ⏱️ 时间表(方案 A)

- 5 分:写 `dialog_bootstrap.py` 骨架
- 5 分:写 session memory 模板
- 5 分:真跑 4 dialog(自动化)
- 5 分:验证 audit + 报数
- **总计:20 分钟**

## ⏸ 等用户勾 4 选 1

按 brainstorming HARD-GATE · 不 ship 代码 · 等用户回:

- `方案 A 模板分发` = 20 分 ship · 推荐
- `方案 B 只补 memory` = 1h ship · 治标
- `方案 C B + hook 全套` = 2h ship · 真治根但风险高
- `hold` = 你下 session 再说

## 关联

- `compass/ops/cross_dialog_audit.py` · 已 ship · 5 dialog 14d 60 commits 真扫
- `compass/ops/auto_surface_hook.py` · 已 ship · 76 条 inbound 真消费
- `compass/GOAL_PROMPT_20260704.md` · 已 ship · 3 档 alert 契约
- `compass/NEW_SESSION_START.md` · 已 ship · 启动 prompt
- `compass/HANDOFF_20260704_FINAL.md` · 已 ship
- `~/.claude/hooks/compass_session_start.py` · 已 ship + 真验证
- `~/.claude/hooks/compass_post_tool.py` · 已 ship + 真验证
- `~/.claude/hooks/path_b_session_audit.py` · 已扩 session memory check
- `~/.claude/settings.json` · 已加 2 hook(SessionStart + PostToolUse)

---
*设计定稿:2026-07-04 02:10 PDT · 5 dialog 补齐治根方案 · 等用户勾*