---
name: orgfuel-ORGD-3df2ecfa85a12bac-4aea306d14
description: "[### P4-1 · compass 记忆写入热路径(首个装载点,灰度 shadow)] - 形态:**shadow "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-3df2ecfa85a12bac
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### P4-1 · compass 记忆写入热路径(首个装载点,灰度 shadow)] - 形态:**shadow 模式**——judge 对每次记忆写入(fact_status/dedup 判定点)并行出三态,只记录不拦截;**fail-open**:judge 任何异常/超时→自动旁路,写入链路不因装载引入新单点。
- 样本:连续 100 次写入判定或 14 天(先到为准)。
- 判据(预注册):
- J-P4-1a:judge 三态 vs 人审三态**一致率 ≥90%**(人审=装载期每日抽样复核,全量留痕)
- J-P4-1b:**false-fail 率 ≤5%**(合法写入被判 fail 的比例;fail-open 下此率为唯一真实风险)
- J-P4-1c:装载期热路径 P95 时延增量 ≤50ms(承 hotpath_cpu_report_20261002 口径,单机 CPU)
- 过门后才讨论"拦截模式";拦截模式=另案申报,本申报不含。
