---
name: orgfuel-ORGM-44c70cc86b007c2b-017dbe797f
description: "记忆条目 s6-ledger-recompute-complete-20261009.md # S6 账本重算+判读收官"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-44c70cc86b007c2b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 s6-ledger-recompute-complete-20261009.md
# S6 账本重算+判读收官(10/9 · l1-0003/0004 · 判读岗执法双例)

- **独立验收=只读 SQL 直查生产库**,绝不采信自报读数;五门:A1 末行语义(0/37)·A2 修正式(prev_bal+**当前**delta——v5 用 prev_delta 笔误得 6730 假违例,判读回函 10777 被 v5 照单全收撤回)·A4 双函数 SUM(delta) pg_proc 实锚·A5 双案例逐位·名册 0 真实漂移(36 零流水种子态如实披露)。
- **A3 教训(平台自纠示范)**:209"孤立押注"重审=201 笔平台误判重复入账(错绑 agent_id,5 月已 slash 入 pool 账)+8 笔真欠已还——**资金类判定先查历史同名操作**(10/4 回填前科+5 月老触发器),NOT EXISTS 谓词须覆盖实际入账 agent;A3 口径 V2=同 bounty 跨 agent 查 pool。
- **卡面勘误纪律**:外部终态更新后(10761)卡面 evidence 同步勘误并重新部署(cloud restart+外网实测 ERRATUM live)——判读卡是活文件不是快照。
- **MCP 网关 SELECT-only**:CTE/WITH 会拒(非 SELECT 开头)——包成子查询;单语句分跑非单事务,读数一致性靠 SUM 触发器增量维护(如实披露)。
- judge_status LEDGER 加卡=改 tools/judge_status_api.py+cloud pull+restart compass-judge-status+外网三字段验证+终检回归——四卡现役(0001 Round1/0002 首例/0003
