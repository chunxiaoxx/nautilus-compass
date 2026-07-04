# 机制保障 GOAL 设计文档 · 2026-07-04

> 🎯 **该不该用 hook + compass 机制保障 GOAL 目标实现** = 答案:是 · 必用 · 2 套机制同推

## 🧠 核心判断

按 anchor #6「避免重复错误 · 不靠"我提醒自己"」铁律 · 5 周复发模式证明 = **单靠对话+自律 = 6 周 dog熊掰玉米 = compass .claude/memory/ 全空 6 周**。**外部机制治根 = 必须**。

## 🧭 3 个方案对比(推荐方案 C = 同推)

### 方案 A · 只加 hook(技术治根)

**思路**:SessionStart + PostToolUse + UserPromptSubmit hook 真自动核身份 + 验跨边界 + 推 anchor。
**优点**:机器不可绕开 · 真生效
**缺点**:用户勾简答时不会触发,只覆盖技术动作
**耗时**:1-2h ship

### 方案 B · 只调提示词契约(人治文)

**思路**:在 GOAL_PROMPT / NEW_SESSION_START.md 加 5 件 机制契约(超红/红/黄 3 档 alert + 必检清单)。
**优点**:模型自觉遵循 · 不写代码
**缺点**:依赖模型自律 = 6 周复发证明无效
**耗时**:30 分

### 方案 C · 同推(推荐 ⭐)

**思路**:A 技术 + B 人治文 互补。
- hook 强制核身份 / 验跨边界 / 推 anchor(机器层)
- 提示词契约做 3 档 alert + 必检清单(人层)
**优点**:双保险 · 任何 1 件漏,另 1 件 catch
**缺点**:1.5-3h ship · 多条 hook
**真证据**:本会话已 ship `auto_surface_hook.py` + 修 `hook.sh` + 落 GOAL_PROMPT = 半边在 · 推完 C = 双轮全

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

### GOAL_PROMPT.md 真契约 · 3 档 alert 段

```
🚨 超红(立刻 stop): 越界写非 compass 文件 / 不写 session memory 就 Stop
🔴 红(本次响必检): drift score < -0.07 / 段落超 8 行 / "真"字 ≥3
🟡 黄(本 turn 提醒): 不读 auto_surface_hook / 不读 NEW_SESSION_START / 不核身份
```

## ⏱️ 时间表(方案 C)

- 5 分:写 `compass_session_start.py` 骨架
- 15 分:写 `compass_post_tool.py`
- 30 分:在 settings.json 注册两个 hook + 测试
- 15 分:GOAL_PROMPT.md 加 3 档 alert 段
- 10 分:本设计文档 commit
- 总计:**75 分**

## 🚫 不撞

- 不重写现有 4 hook(SessionStart/PostToolUse/PreToolUse/Stop)· 加不替换
- 不替用户决策(用户没勾前不动手)

## ⏸ 等用户勾

按 brainstorming HARD-GATE · 不 ship 代码 · 等用户回 4 选 1:

- `方案 C 同推`(推荐)· 75 分钟 ship
- `方案 A 只 hook` · 1-2h ship
- `方案 B 只提示词` · 30 分 ship
- `hold` · 你下 session 再说

## 关联

- `compass/NEW_SESSION_START.md` · 启动 prompt
- `compass/GOAL_PROMPT_20260704.md` · Goal 详细版
- `compass/ops/auto_surface_hook.py` · 已 ship 半边
- `~/.claude/plugins/nautilus-compass/hook.sh` · 已修
- `~/.claude/settings.json` · 已加 1 hook
- anchor #6 治根 = 外部机制不靠自律

---
*设计定稿:2026-07-04 01:50 PDT · 走 brainstorming HARD-GATE · 等用户勾后进 writing-plans*