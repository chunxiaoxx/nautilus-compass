---
name: orgfuel-ORGQ-R336-1b1c526ce6
description: "### R336 · 2026-10-08 早(主件轮:判读卡状态查询 E2E 上线✅——真源切换完成) - **全链上"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R336
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R336 · 2026-10-08 早(主件轮:判读卡状态查询 E2E 上线✅——真源切换完成)
- **全链上线✅[实测 E2E]**:①judge_status API 上 cloud(systemd compass-judge-status:9890,开机自启)②nginx /api/judge_status 代理(一次转义坑 Host \$host 被吃→nginx -t 抓出→修;sites 16 行损坏复验通过)③status.html 前端切真源(fetch /api/judge_status,DEMO 降级兜底)——**外网端到端**:查 nautilus-l1-0001 返回 done/6 steps/判据 sha ✓,未知 id 404 ✓。**对外服务闭环全链(提交→查询→结果)真数据贯通**。
- 遗留:v0 台账为演示数据,真实受理台账接 DB 后自动切(v0 台账与 status.html 同源结构,切换零改前端)。
