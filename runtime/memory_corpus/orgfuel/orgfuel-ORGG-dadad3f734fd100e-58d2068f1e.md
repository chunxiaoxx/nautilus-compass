---
name: orgfuel-ORGG-dadad3f734fd100e-58d2068f1e
description: "判读档判例 J8_HOTPATH_P4_DECLARATION_20261003 · 二 · 装载三步与 P4 判据预注"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-dadad3f734fd100e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 J8_HOTPATH_P4_DECLARATION_20261003 · 二 · 装载三步与 P4 判据预注册
## 二 · 装载三步与 P4 判据预注册

### P4-1 · compass 记忆写入热路径(首个装载点,灰度 shadow)

- 形态:**shadow 模式**——judge 对每次记忆写入(fact_status/dedup 判定点)并行出三态,只记录不拦截;**fail-open**:judge 任何异常/超时→自动旁路,写入链路不因装载引入新单点。
- 样本:连续 100 次写入判定或 14 天(先到为准)。
- 判据(预注册):
  - J-P4-1a:judge 三态 vs 人审三态**一致率 ≥90%**(人审=装载期每日抽样复核,全量留痕)
  - J-P4-1b:**false-fail 率 ≤5%**(合法写入被判 fail 的比例;fail-open 下此率为唯一真实风险)
  - J-P4-1c:装载期热路径 P95 时延增量 ≤50ms(承 hotpath_cpu_report_20261002 口径,单机 CPU)
- 过门后才讨论"拦截模式";拦截模式=另案申报,本申报不含。

### P4-2 · assay G1 自动腿(具身数据验证线)

- 形态:judge 作帧级规则判官(g1_judge_v3/pusht_4win_judge_v1)的**辅助第一腿**,与规则判官平行跑,分歧件人审。
- 判据:与规则判官三态一致率 ≥90%,且分歧件人审后 judge 正确率如实记(判绩账双向:评委也会错)。
- 边界:帧级材料判读主判仍归规则判官+人审;judge 腿输出仅作参考,不进 verdict 本体(反自指护栏 2)。

### P4-3 · F15 meta-judge 第一腿

- 形态:三供应商复判
