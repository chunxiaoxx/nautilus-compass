# 裁定 C 冲正清单(2026-10-07 深夜 · compass 出 · 应 10417/10432 口径)

> 形态:逐行可执行账务动作+验收 SQL;平台执行前整包呈用户。口径=#10432 用户批(.dedup 负行/保留首条/联合分组键/hr 排除/双写一事务)。
> 证据层:全部 [实测](cloud 生产库只读查询,生成时刻 10/7 23:5x);待裁项标 [待裁]。

## 组件一:重复付款对冲(主体,逐行 CSV 在案)

- **载体**:runtime/audit/correction_c.csv(1019 行对冲动作;云端 /home/ubuntu/correction_c.csv 同源);
- **生成口径[实测]**:分组键(linked_bounty_id, agent_id)· delta>0 · reason 非 stake% · hr-agent-web 排除 · 保留(created_at,id) 首条 · 余条对冲(delta=-原delta,linked=原id+'.dedup',reason='dedup:<源id>');
- **当前读数**:对冲 1019 行 / **-30,413 NAU** / 涉 954 重复单;分布:prime-001 785 行/-24,873;kairos 162/-4,820;9000018 71/-710;caishen 1/-10;
- **与 dry-run(975/-30,653)差异说明**:①行数 +44=止血未部署,重复仍在累积(明早部署窗后至 apply 前增量须重跑本 CSV,以 apply 时刻为准);②金额差 -240=组件归属差异:9000018 的 702(225 单重复释放)在 10417 指定"并入"单独组件,我方 71 行/-710 中含该 225 单的子集重叠——**apply 前须以 apply 时点重跑+组件二合并去重**,避免双重对冲(已在验收 SQL 防线,见下);
- **验收 SQL①(对冲后零重复)**:
```sql
SELECT count(*) FROM (
  SELECT linked_bounty_id, agent_id, count(*) c FROM platform_nau_ledger
  WHERE linked_bounty_id IS NOT NULL AND delta>0 AND reason NOT LIKE 'stake%'
    AND agent_id<>'hr-agent-web' AND linked_bounty_id NOT LIKE '%.dedup'
  GROUP BY 1,2 HAVING count(*)>1) t;  -- 期望 0
```

## 组件二:702 重复释放并入(10417 指定)

A1 审计案 225 单/702 NAU 重复释放——**与组件一重叠部分不重复对冲**(验收 SQL②:corr_reason='dedup:<id>' 的源行集合 ∩ A1 案 225 单集合,若非空则组件二仅对差集执行);差集动作同 .dedup 制式,reason='dedup:a1case'。

## 组件三:三家真缺口注资(正动作)

| 对象 | 金额 | 动作 | 验收 |
|---|---|---|---|
| prime-001 | +20,539 | 注资行( reason='refill:verdict-C') | 余额对账=sum(delta) |
| kairos | +9,997 | 同上 | 同上 |
| platform | +199 | 同上 | 同上 |

## 组件四:prime-001 反向差 10,699 [待裁]

超出对冲解释的余额差——**不建议并入本批**(性质未定:可能是历史口径/双账期),标待裁,用户批后单独批次。

## 组件五:13 种子补注资(6 名册内 gap)

按 #10400 框架名册内 6 个 gap 执行 +7/个(13 总额分解以名册为准);动作 reason='seed:refill'。

## 执行序(与 10432 批次对齐)

止血部署→**apply 时点重跑本 CSV**→组件二差集并入→组件三/五正动作→组件四待裁搁置→唯一索引落地→compass 复读(验收 SQL①零重复+全 agent sum(delta)=balance_after 全表对账)。

—— compass · C-VERDICT-LEDGER(deadline 10/9 12:00 前置交付)
