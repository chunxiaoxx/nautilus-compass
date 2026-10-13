---
name: orgfuel-ORGG-29ec3617288bd17f-b985c7d2b8
description: "判读档判例 C_VERDICT_LEDGER_20261007 · 组件一:重复付款对冲(主体,逐行 CSV 在案) #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-29ec3617288bd17f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 C_VERDICT_LEDGER_20261007 · 组件一:重复付款对冲(主体,逐行 CSV 在案)
## 组件一:重复付款对冲(主体,逐行 CSV 在案)

- **载体**:runtime/audit/correction_c.csv(1019 行对冲动作;云端 /home/ubuntu/correction_c.csv 同源);
- **生成口径[实测]**:分组键(linked_bounty_id, agent_id)· delta>0 · reason 非 stake% · hr-agent-web 排除 · 保留(created_at,id) 首条 · 余条对冲(delta=-原delta,linked=原id+'.dedup',reason='dedup:<源id>');
- **当前读数**:对冲 1019 行 / **-30,413 NAU** / 涉 954 重复单;分布:prime-001 785 行/-24,873;kairos 162/-4,820;9000018 71/-710;caishen 1/-10;
- **与 dry-run(975/-30,653)差异说明**:①行数 +44=止血未部署,重复仍在累积(明早部署窗后至 apply 前增量须重跑本 CSV,以 apply 时刻为准);②金额差 -240=组件归属差异:9000018 的 702(225 单重复释放)在 10417 指定"并入"单独组件,我方 71 行/-710 中含该 225 单的子集重叠——**apply 前须以 apply 时点重跑+组件二合并去重**,避免双重对冲(已在验收 SQL 防线,见下);
- **验收 SQL①(对冲后零重复)**:
```sql
SELECT count(*) FROM (
  SELECT linked_bounty_i
