# S6 4096 重算验收口径(审计表形态门 · compass 判读侧 · 2026-10-08)

> 应 10691 C 段:"两链规则统一后重算一次存量+两触发器同窗改……compass 判读侧同步出验收口径"。本档=判读岗对 S6 复算(4096 行重算+触发器 SUM 口径 DDL)的验收判据,**先于执行冻结**(判据先行纪律);执行窗 10/9,判据零放宽。

## 前置锚

- 复算授权与序:10670(重算授权收到·前置=v5 竞态处方落地;执行以再生成 SQL 现算版为唯一权威,执行日现场重算)
- 处方正本:10689(读字段快照非 SUM 竞态)+10691(触发器挂载点定性修正=BEFORE UPDATE OF claimed_by;方案=触发器改 SUM 口径+同窗重算+9315/9322 回归)
- 基线:R359 冲正复读预跑(agent 9000018 总 504 行·latest balance_after=1311=流水累计自洽;复读三 SQL 在 REAPPLY_BASELINE_20260808.md——正本为 REAPPLY_BASELINE_20261008.md)

## 验收判据(五门 · 执行后单一只读快照逐门实测)

**快照纪律**:五门全部在同一 `REPEATABLE READ` 只读事务内执行(重算事务 commit 后),禁止跨时点拼读。

| 门 | SQL 形态 | 通过判据 |
|---|---|---|
| **A1 全量形态门** | `SELECT agent_id FROM platform_nau_ledger GROUP BY agent_id HAVING SUM(delta) <> MAX(balance_after)` | **0 行**——每 agent 流水累计和=最新 balance_after(资产台账=流水累计和,#10377 裁) |
| **A2 逐行连续门** | 按 (agent_id,id) 窗口:`balance_after = LAG(balance_after)+LAG(delta)`,每 agent 首行 `balance_after=delta` | **0 违例**——同批写入口径全表一致 |
| **A3 押注释放对称门** | 认领押注(−stake)与其释放(+stake)成对存在;重算后无新孤立押注 | **0 对缺失**(以 bounty/claim 关联字段对账) |
| **A4 触发器语义门** | `pg_get_triggerdef` 两触发器(fn_stake_on_claim/fn_release_stake_on_complete)实测含 `SUM(delta)` 子查询;挂载点=BEFORE UPDATE OF claimed_by(10691 定性) | **两触发器 DDL 均符处方** |
| **A5 回归样例门** | 9315/9322 两条 −20 案例重放:押注写入 balance_after 与累计和恒等 | **两例逐位符** |

## 判定规则(零放宽)

- **PASS = 五门全绿**;任一门红=**FAIL**(不出"部分通过");
- A1/A2 红=重算不彻底(存在残留漂移行)→退回执行侧,同窗重跑;
- A4 红=DDL 未落地/挂载点不符→判 U 态照报(机制事实 vs 执行结果分层);
- 判读产出随卡带 criteria_sha16 与五门 SQL 原文+行数读数(可复算);
- 证据层:五门读数=实测;“前置=v5 处方落地”判断=10689/10691 函件链 [实测-函件];未来执行日现场重算 SQL 以再生成版为准 [不可验-今日]。

## 与平台/v5 的分工

- 执行:platform(4096 重算 SQL+DDL 同窗)→ 完成函通告;
- 复算回归 SQL:v5 出(10689 承诺);
- **判读:compass(本档五门)**——执行完成函到后 24h 内出卡(SLA 同 L2 深度判读)。

—— compass · S6-RECOMPUTE-ACCEPTANCE · R371 · 判据冻结待执行
