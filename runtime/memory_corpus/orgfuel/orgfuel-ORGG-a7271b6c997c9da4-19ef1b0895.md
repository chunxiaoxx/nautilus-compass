---
name: orgfuel-ORGG-a7271b6c997c9da4-19ef1b0895
description: "判读档判例 BC1_LAUNCH_RUNBOOK_0927 · 一 · 前置依赖(T-1 日 9/26 前必须全绿) #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a7271b6c997c9da4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 BC1_LAUNCH_RUNBOOK_0927 · 一 · 前置依赖(T-1 日 9/26 前必须全绿)
## 一 · 前置依赖(T-1 日 9/26 前必须全绿)

| # | 项 | 判据 | 状态 | 风险预案 |
|---|---|---|---|---|
| P1 | 日报框接单回函 | 9/26 12:00 前回函确认渠道+稿时 | ⏳函 862 已发 | 未回→我方备稿直发(渠道降级:知乎/公众号由用户定)。**9/24 注**:信箱读路径故障(函 893 通报 platform)——届时日报回函若读不到,按「未回」处理直接走备稿,不以信箱故障延期 |
| P2 | 中文稿事实核对 | 9/26 我方过稿:全部数字与 SELFTEST_SCORECARD_V2/BC1_LAUNCH 逐项一致,零自夸外推 | 🔄 备稿完成 a055156(BC1_LAUNCH_CN_DRAFT,9/24 逐项自查过);9/26 终核 | 核对不字→打回改,再核 |
| P3 | Discord 登录态 | 9/26 开 CDP 窗口验一次(9224,profile cookie) | ✅ 9/23 验过(logged_in=true);9/26 复验 | 失效→请用户扫码(用户面板提前 24h 挂) |
| P4 | 发布物链接全检 | BC1_LAUNCH.md/README/wall/报名模板 GitHub 页全部 curl 200 | ✅ 9/23 六链接检过(报名 302=登录跳转正常) | 死链即修即重验 |
| P5 | Discord 稿链接填实 | DISCORD_LAUNCH_DRAFT 三处占位符(<exam-signup link>等)替换为实际 URL | ✅ 9/23 填实 | — |
| P6 | 当期考卷就位 | selftest_ex
