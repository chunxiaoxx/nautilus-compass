---
name: orgfuel-ORGM-76fb36364fc7e9eb-8adee36caf
description: "记忆条目 org-frames-probe-runbook.md 2026-09-24 用户灵魂拷问:卖组织记忆的 co"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-76fb36364fc7e9eb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 org-frames-probe-runbook.md
2026-09-24 用户灵魂拷问:卖组织记忆的 compass 却找不到 flywheel 在哪。实测反转:flywheel 当日 7 commit 全速跑(此前我在战略分析里判其"静默/数据线悬置"=完全错误)。

**Why**:compass 记忆按项目分桶(~/.claude/projects/<proj>/),跨框知识只进不进我的召回取决于"compass 会话写过"。凭"我的索引里没有"断言他框状态=自报逻辑复发,违反立身之本。

**How to apply**:任何涉及他框的判断,先做物理探查(≤2 分钟):
- **五框坐标**:compass=`Projects/nautilus-compass`(账本 docs/plans/LOOP_STATE.md);flywheel=`Projects/nautilusflywheel`(北极星 GOALS.md·loop 锚 docs/plans/LOOP_FW_20260921.md·1h cron 自轮值);platform=`Projects/nautilus-platform-sdk`+云端(组织态 GET /api/platform/org/bootstrap?agent=X);v5=Projects/nautilus-v5;日报框=仓未定位(nautilus-core 疑似,待查)
- 探查三件套:①git log --oneline -5 <框仓> ②读其账本/GOALS 头部 ③ls 其 _INBOUND/_OUTBOUND_ 函件尾部日期
- 平台信箱 id 空间全框共享(flywheel SENT 911/914 与 compass 893/896 同空间)——写入端各框都通,9/24 故障面实测收窄为 to=compass 
