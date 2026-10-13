---
name: orgfuel-ORGH-c433579e1d73e2b1-dc78ca85dc
description: "commit ef3fb2972aa2 2026-07-06 feat(compass①): economy liven"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c433579e1d73e2b1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit ef3fb2972aa2 2026-07-06
feat(compass①): economy liveness probe 读生产 DB 真值 · 独立裁判
替换 liveness_audit 纯本地文件的'瞎'探针。走已验证 compass_sub ssh-tunnel
只读连接(复用 cross_agent_outcome_poller · 不另造),直接读生产表验闭环:

- probe_verified_income: fde_verdicts external_verified∧overall_pass 的
  sum(round(score)) 独立复现 income=188(JobShop 98+QAOA 90)· 不信自报
- probe_engine_cycle_liveness: engine_cycle_outcomes last=33.8d/24h=0 独立
  揭穿引擎自循环停摆剧场
- probe_income_ground_truth: agent_survival 无 grant → 诚实报 GAP(不 fake-GREEN)
  · 需 platform GRANT SELECT(合约已发)

TDD 12/12 green + live 实测三读真值通过。SSOT v3 compass ① binding-DONE 判据 2。
