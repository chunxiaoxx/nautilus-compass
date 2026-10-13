---
name: orgfuel-ORGG-d81623e6fdacce2d-15e9ab0646
description: "判读档判例 2026-07-04-5-dialog-bootstrap-design · 🧭 3 方案对比(推荐方案 A"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d81623e6fdacce2d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-04-5-dialog-bootstrap-design · 🧭 3 方案对比(推荐方案 A · 模板分发)
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
