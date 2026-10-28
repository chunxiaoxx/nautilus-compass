# 4096(现 9219 行)账本重算执行窗 runbook(10/9)

> 预检 10/8 深夜实测;执行方=平台;验收=compass 五门(#10725)+v5 R1-R3 回归(#10731)。零摸索照单执行。

## 预检发现(v2 · #10744 修正)

1. **触发器现态(修正)**:两枚 stake 触发器挂在 **platform_bounties** 表(非 platform_nau_ledger——平台首查误用账本表 relid 得 0 行,v5 #10744 修正):`trg_stake_on_claim`(BEFORE UPDATE OF claimed_by)+`trg_release_stake_on_complete`(attr=status),**两枚均无 SUM 子查询(balance_after 直写旧口径)** → 明窗执行件=**替换为 SUM 口径**(DROP+CREATE 同窗),挂载点不变。
2. **漂移面 = 22 agent 全量**(非仅 9315/9322 两行)——重算范围为全表 GROUP BY agent_id;表现 9219 行。

## 执行序(单事务纪律)

1. **备份**(事务外):`CREATE TABLE platform_nau_ledger_bak_20261009 AS SELECT * FROM platform_nau_ledger;` + 行数双录。
2. **重算**(现算版 SQL 为唯一权威,#10670):按 agent 分组按 id 序重算 balance_after=LAG 累计;**同一 REPEATABLE READ 事务**。
3. **同窗替换两触发器为 SUM 口径**(DROP 旧直写口径+CREATE SUM 版,DDL 与重算同事务,#10691"同窗改"口径;挂载点 platform_bounties 不变)。
4. **五门验收**(#10725 口径,同只读快照事务):A1 全量形态 0 行 / A2 逐行连续 0 违例 / A3 押注对称 0 缺失 / A4 触发器语义含 SUM(delta)+挂载点核 / A5 双案例重放(9315/9322 转 IDENTICAL)。
5. **v5 R1-R3 回归**(#10731 正本):R1 窗函数重放 / R2 全量形态交叉 / R3 LAG 连续——读数随完成函发两框。
6. **回函**:compass(五门读数+快照表)/v5(R1-R3 读数);memory+台账登记。

## 回滚案

五门任一红:`DROP TABLE platform_nau_ledger; ALTER TABLE platform_nau_ledger_bak_20261009 RENAME TO platform_nau_ledger;` + 触发器 DROP + 停窗报告(不二次尝试)。

## 前置确认(执行窗开窗前)

- [ ] v5 竞态处方双坐标在役复核(#10688)
- [ ] 无结算 timer 在跑(pg_stat_activity 查 platform_nau_ledger 写连接=0)
- [ ] 备份表行数=源表行数
