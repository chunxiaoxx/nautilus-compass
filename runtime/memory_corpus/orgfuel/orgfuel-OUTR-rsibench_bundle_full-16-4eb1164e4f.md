---
name: orgfuel-OUTR-rsibench_bundle_full-16-4eb1164e4f
description: "### 9/14 合入执行读数(提前于 9/15 窗口,用户拍板)  - **合入形态**:生产 worktree ch"
metadata:
  type: reference
  source: org_fuel:outreach
  pf_id: OUTR-rsibench_bundle_full-16
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### 9/14 合入执行读数(提前于 9/15 窗口,用户拍板)

- **合入形态**:生产 worktree checkout `feat/memory-gate-trio`(9cb9e7e)。⚠️中途曾试 main 基座 cherry-pick 版(merge-ready-0915),发现 main 缺 3912205 线运行时修复(recall v2.4/HUD wrapper 278 行/daemon_start 改进)→hook 回退 v2.3,当场纠正回 feat 线直切;merge-ready-0915 弃用,main 统一留作后续工作。
- **J1(fact_status 覆盖)**:写入门在线(15 单测覆盖 fact_status 路径);真库覆盖率待合入后新条目产生再统计回填(合入日无新写样本)。
- **J2(查重零误合并)真库抽样**:无关文本→unique(hits 空)✅;同主题不同文→gray 0.840✅(区间 0.75-0.9);真条目原文重判→merge 0.938✅(≥0.9)。三档行为全对,零误合并。
- **J3(沿链一跳)在线验证**:查询命中 aegis-compass-competitor-20260907(含 [[paper-roadmap-history-20260904]]),chain_extra 正确带出被引条目✅;无链查询 chain_extra 恒空✅。延迟:冷路径 389-518ms(与 J4 基线同量级),热缓存 p50=1ms(daemon mtime cache 命中)。
- **J4(全局回归门)**:9876 生产 GREEN(三 fact 全 PASS·命中正确;首查 7.1s=embed 冷缓存,后续 389/400ms);预演日 9878(main 基座版)同样 GREEN——两基座双验
