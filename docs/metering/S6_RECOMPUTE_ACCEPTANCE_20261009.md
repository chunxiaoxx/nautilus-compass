
## V2 勘误+独立验收记录(2026-10-09 · 判读卡 l1-0004)

- **两处门公式勘误采纳**(platform 10751 提议,独立复算验证):A1 改**末行语义**(原 MAX 在余额下行 agent 失真);A2 改 **prev_bal+当前 delta**(原式笔误)。V1 原式作废留档。
- **独立验收[实测,只读 SQL 直查生产库]**:A1=0/37 agents mismatch;A2 连续+首行=0 违例;A4=双函数 SUM(delta) 实锚(pos 610/1131)+挂载点 stake=BEFORE UPDATE OF claimed_by、release=AFTER UPDATE OF status;A5=ledger 9315/9322 行(−20,30236/30452)与 v5 预跑基线逐位一致;名册=0 真实漂移(36 agents=零流水种子额设计态,10712 已知,如实披露)。
- **五门判定:PASS**。A3(209 对历史孤立押注=触发器空窗期产物,非重算回归)——回填与否=资金操作,候用户批,不阻塞本卡。
- 注意:MCP 网关 SELECT-only,单语句分跑(非单事务快照)——读数一致性由 SUM 触发器增量维护保证,如实披露。

## A3 终态勘误(2026-10-09 · 依 10761 平台回填执行报告)

209 孤立押注重审终态:201 笔=平台 A3 门孤立判定错绑 agent_id(5 月已 slash 入 pool 账)误判重复入账,已冲正(app=stake_slash_backfill_20261009_reversal×201,append-only 留痕);8 笔=真欠账已还(+50 NAU release 退 claimer)。**终态:pool=2,434(回 5 月基准),用户呈批项销案**。A3 门口径 V2:孤立判定=同 bounty 无任何 release/slash 行(跨 agent 查 pool);资金判定先查历史同名操作(10/4 回填前科+5 月老触发器)。l1-0004 卡面 A3 段已同步勘误。
