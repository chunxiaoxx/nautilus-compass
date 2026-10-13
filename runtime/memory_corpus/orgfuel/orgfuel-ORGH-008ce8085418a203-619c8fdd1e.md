---
name: orgfuel-ORGH-008ce8085418a203-619c8fdd1e
description: "commit a9558605e2a3 2026-09-30 feat(metering): API网关30天实测计量方"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-008ce8085418a203
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit a9558605e2a3 2026-09-30
feat(metering): API网关30天实测计量方案预注册+probe runner骨架(拿额度即跑)
- 预注册判据档J1-J7冻结(可用性99%/p95对照腿x1.5/身份指纹零矛盾/计费1%/上下文保真/结构化95%/漂移2σ)
- 逐条对准对方宣称验证:100%官方渠道→指纹+对照腿;稳定低延迟→分时段p95;计费明细→usage对账
- J3身份矛盾若FAIL保留公开权(用户安全优先于合作协议);FAIL/U→教程不发(顺序条款落地)
- runner:五类probe/日汇总/指纹题库外置/config模板自动生成/dryrun冒烟过;收工走非实现者复算
- 启动三条件:base_url+key+模型清单齐24h内首轮;首24h出可用性初读对齐口径

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
