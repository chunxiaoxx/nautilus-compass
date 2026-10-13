---
name: orgfuel-ORGM-71fa0aa37244c5d3-f6bedb1cc9
description: "记忆条目 inbox-agent-round-20260831.md # 收函代理轮(2026-08-31 · 用户授权"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-71fa0aa37244c5d3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 inbox-agent-round-20260831.md
# 收函代理轮(2026-08-31 · 用户授权平台触发,协议 v1 §3 试点)

10 封未 ack 函全部处理:回函 id 41(flywheel GPU)/43(复盘答卷)/44-51(协议认领/配方/审查/SLA/worker/bootstrap/飞书/drift),10/10 ack,bootstrap 复读 unread=0 验证通过。

**已执行**:SSOT 副本自纠(canonical 42ed7a7e 版同步,commit faedfd6,sha=6c4555bb 与 canonical 一致);d13 评测实测(未卡,web 91/240 · ent 117/211,subject=doubao 走 ARK plan 端点,GPU util≈0)。

**Why:** compass 逾期根因=无常驻收函轮(mailbox 自取无到达通知),已向平台承诺协议 §3 daemon 化。

**How to apply(三个到期待办,新 session 优先查)**:
1. **9/2 22:00+0800 前回报 daemon 日轮部署回执**(承诺函 id 44/45)——云机(9876 daemon 同机)cron 起步,配方=nautilus-core/docs/org-inbox-agent-recipe.md,验收三条:无 session 全链/幂等 state.json/连续 3 天零漏函;headless claude 云机可用性未验证,先用降级模式(规则化回执+复杂函升级)。
2. **session-start hook 注入 org/bootstrap 摘要**(随 1 同报)——手动模式已达标,hook 模式待落。
3. **d13 结果拉回**(预计 8/
