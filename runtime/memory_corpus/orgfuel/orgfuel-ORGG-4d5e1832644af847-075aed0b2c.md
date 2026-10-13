---
name: orgfuel-ORGG-4d5e1832644af847-075aed0b2c
description: "判读档判例 2026-07-04-hook-mechanism-guard-goal-design · 🧭 3 个方案对"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-4d5e1832644af847
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-04-hook-mechanism-guard-goal-design · 🧭 3 个方案对比(推荐方案 C = 同推)
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
