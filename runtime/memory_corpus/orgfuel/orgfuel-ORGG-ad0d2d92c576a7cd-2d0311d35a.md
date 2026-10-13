---
name: orgfuel-ORGG-ad0d2d92c576a7cd-2d0311d35a
description: "判读档判例 2026-07-04-hook-mechanism-guard-goal-design · 🏗️ 设计 · "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ad0d2d92c576a7cd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-04-hook-mechanism-guard-goal-design · 🏗️ 设计 · 方案 C 真结构(本会话 ship 范围)
## 🏗️ 设计 · 方案 C 真结构(本会话 ship 范围)

### SessionStart hook · `~/.claude/hooks/compass_session_start.py`

```python
# 每次 session-start 自动:
# 1. 核 cwd 必须 = nautilus-compass(否则 fail-stop)
# 2. 读 NEW_SESSION_START.md + GOAL_PROMPT_20260704.md
# 3. 注入 3 档 alert(超红/红/黄)到 context
# 4. 推 .seen_compass watermark
# 5. 检查 8 件漏掉事是否做了(兜底)
```

### PostToolUse hook · `~/.claude/hooks/compass_post_tool.py`

```python
# Write/Edit 触发:
# 1. 验路径在 nautilus-compass/ 内(否则 fail-stop)
# 2. 验不是 _OUTBOUND_FROM_PLATFORM_*(不要冒充)
# 3. 验 session memory 文件落档(.claude/memory/session_*.md)
# 4. 推 workspace dirty 检查
```

### Stop hook · 已有 `path_b_session_audit.py`

复扩:加 session memory 落档 check(必须 1 个 session_*.md 才能 stop)

### GOAL_PROMPT.md 真契
