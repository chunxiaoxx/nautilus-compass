# 冲正 apply 复读基线档(2026-10-08 夜预跑 · 10/9 12:00 窗口输入)

> apply 前(本档)与 apply 后(明日复跑)对比即复读。DB=生产只读(mcp nautilus-db)。

## 基线读数(agent 9000018)[实测 2026-10-08 夜]

| 指标 | 值 | 判读 |
|---|---|---|
| 总行数 | 504 | A2 评算时 425,+79 新入 |
| A1 修复(10/7 17:00)后新增行 | 87 | — |
| 修后行 balance_after=流水累计 | **87/87 全对齐** | 写入器修复持续健康(零差异) |
| latest balance_after | 1311 | — |
| 流水累计和 cum_sum | 1311 | 账面自洽(序列一致) |

## 复读三 SQL(apply 后复跑,全部只读)

**S1 修后增量零差异**(续证):
```sql
SELECT count(*) AS rows_total,
       count(*) FILTER (WHERE created_at > '2026-10-07 17:00+08') AS rows_after_fix,
       count(*) FILTER (WHERE created_at > '2026-10-07 17:00+08'
                        AND balance_after = cum) AS after_fix_match,
       max(balance_after) AS latest_balance, max(cum) AS cum_sum
FROM (SELECT id, delta, balance_after, created_at,
             sum(delta) OVER (ORDER BY id) AS cum
      FROM platform_nau_ledger WHERE agent_id='9000018') s
```
判据:after_fix_match=rows_after_fix(零差异持续)。

**S2 冲正行落地核验**(裁定 A3 的 -142 或分期冲):
```sql
SELECT id, delta, reason, balance_after, created_at
FROM platform_nau_ledger
WHERE agent_id='9000018' AND id > (SELECT max(id) FROM platform_nau_ledger
                                   WHERE agent_id='9000018' AND created_at <= '2026-10-08 23:59+08')
ORDER BY id
```
判据:冲正行 reason 含"冲正/A3/correction"语义,delta 合计=-142(或裁定分期首笔),落地后 balance_after=1311+新行 delta。

**S3 冲正后账面自洽**:
同 S1(latest_balance=cum_sum 恒等判据)+ 与 platform 回执读数互证。

## 预期(apply 后)

- 若一次性冲 142:新 balance_after≈1311-142=1169(S2 实测为准);
- 若分期:首笔=裁定值;
- 任一形态:S1 零差异+S3 自洽必须成立,否则复读 RED(先证伪自己 SQL 再报)。

—— compass · REAPPLY-BASELINE · 2026-10-08
