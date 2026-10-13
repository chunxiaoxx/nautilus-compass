---
name: orgfuel-ORGD-8a1abf9fb1707fb5-2b31c2650f
description: "[## ① 4-tier 生命周期 · 真实缺口 = tier 驱动从没调度过] - 已闭合:生产 recall 路径 "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-8a1abf9fb1707fb5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## ① 4-tier 生命周期 · 真实缺口 = tier 驱动从没调度过] - 已闭合:生产 recall 路径 reinforce_count bump + PoI candidate emit + archived-check(daemon)。
- **缺口**:`scripts/tier_promotion_driver.py`(docstring "Cron once daily")cron-ready 但无 `tier_promotion_log.jsonl` = 从没跑过 → 全量每日晋升未发生。
- **🔴 2026-07-08 dry-run 更正(据实)**:对 compass memory 16 文件副本跑 `run_driver` → **0 mutation**。根因:driver 用 `cumulative_impact`(impact 轴)算晋升,而该字段**没被写进 session frontmatter**(recall 只 bump `reinforce_count` = access 轴,driver 不读它)。⇒ **挂调度也 no-op**,① 真前置 = **PoI cumulative_impact → frontmatter 的写流**(比"没调度"深一层)。driver 本身安全(不崩、幂等、0 误伤)。
- **修正后设计**:(a) 先接 impact→frontmatter 写流(PoI emit 时 stamp cumulative_impact),(b) 再挂 driver 调度(否则空转),(c) test 断言有 impact 时 driver 真晋升。
- 风险:driver 改 frontmatter,低;impact 写流涉 PoI 主环,需 careful。
