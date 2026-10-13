---
name: orgfuel-ORGM-hud-multiview-crosstalk--d3dd6d0aa5
description: "--- name: hud-multiview-crosstalk-fix-20260901 description: "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-hud-multiview-crosstalk-
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: hud-multiview-crosstalk-fix-20260901
description: "HUD statusline 多窗口串台修复(v3.0.11·commit 2a359aa):claude-hud 段缓存曾全局单份不带 cwd 键,4 窗口互相覆盖=目录/仓库显示混乱+节流窗内空段;修=per-cwd 分桶+独立节流+md5 稳定 hash"
metadata:
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  modified: 2026-09-01T15:51:09.226Z
---

# HUD statusline 多窗口串台修复(2026-09-01 · v3.0.11)

用户报"底部 HUD 显示的工作目录和仓库混乱、信息不齐全"。根因(`compass_hud_wrapper.py` 的 claude-hud 段):

1. **串台**:`hud_out_cache.txt` 全局单份、不带 cwd 键——用户同时开 4 个 Claude Code 窗口(compass/v5/core/flywheel 实测),各窗渲染互相覆盖缓存 → A 窗口显示 B 窗口的 repo/目录/分支 = "混乱"。
2. **缺段**:60s 全局 spawn 节流 + 30s 缓存门槛——缓存过期但节流未到时 hud 段整个消失 = "信息不齐全"。

修复(v3.0.11 · commit 2a359aa):
- 缓存按 cwd **分桶**:`{cwd: {ts, hud}}`,各窗各存各的;旧单份格式自动废弃重建。
- 节流 **per-cwd** 独立(`.last_spawn.<md5
