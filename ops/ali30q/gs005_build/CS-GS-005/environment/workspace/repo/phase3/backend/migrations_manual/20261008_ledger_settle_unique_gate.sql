-- 结算跨运行幂等硬门(止血第二层·DB 约束)
-- 背景:#10400 compass 复算包——重复付款 2179 单/35,523 NAU 且持续产生(fuel_settle.py 去重集合
--   LIKE 'b-turbo-%' 只认 turbo 前缀,代码层已修 2026-10-07 晚:去重放全 linked_bounty_id);
--   bounty_settlement.py(v5 仓)跨运行无门,已函告 v5 补键。
-- 重复实证(2026-10-07 22:0x 平台只读复现):b-82d6fd4704bd 等单号最多 7 次正结算;
--   表上原仅 pkey+agent_idx,linked_bounty_id 无唯一约束。
-- ⚠️ 执行前置:裁定 C 冲正清完存量重复行——否则 CREATE UNIQUE INDEX 直接失败
--   (失败本身=存量重复体检探针,属预期信号非故障)。
-- 部署窗纪律:22:00-07:30 不执行;上窗时与 fuel_settle.py 修复同批部署。
-- v2 修正(承 compass #10411 第五节):同一 bounty 存在合法跨 agent 多行(21 单实证),
--   单列唯一会误挡——改为 (linked_bounty_id, agent_id) 联合唯一:同单同 agent 只许一条正结算,
--   同单跨 agent 各一条合法。linked_bounty_id 填充率 1057/1057 全齐(#10411 实测),索引可建。
-- v3 修正(承 compass #10421 第一节):押金释放(stake_release_on_*=正 delta)与同 bounty 结算正行
--   合法同号——按 v2 谓词实测 1,077 个正当碰撞(1,075 同号+202 单结算+释放)会炸索引且误导"探针"读法
--   去动正当释放行。谓词补 stake 家族排除(=#10402 清单口径,清完 1,057/终版口径存量后可建)。
-- v4 修正(平台预验实测 2026-10-08 01:0x):hr-agent-web 有 62 个联合键违规组(含 hr 全量=1,036,
--   与单键 1,057−20 跨 agent 组=1,037 吻合±漂移),但裁定(#10402)hr 已同步不冲抵——全表索引会因
--   hr 组建不起来。口径一致化:索引排除 hr(其双账治理归 HR 框域),与冲正排 hr 同口径;
--   非 hr 违规组实测 974=将冲正数,apply 后归 0,索引可建。
-- v5.1(承 compass #10507 a+ + #10519 补丁):谓词四排(stake 家族/hr 豁免/.dedup 双腿标记/NULL);
--   被冲正行经 a+ 重命名后不再命中;表实测 1.8MB/8,165 行·锁窗亚毫秒·**未用 CONCURRENTLY**(避事务块+INVALID 吞噬两坑);
--   索引谓词口径残留=71 组(a+ 后归 0,非 153,见 #10514 更正);验收 V3d 改查 indisvalid(#10519 坑二)。
CREATE UNIQUE INDEX IF NOT EXISTS ledger_settle_unique_gate
  ON platform_nau_ledger (linked_bounty_id, agent_id)
  WHERE linked_bounty_id IS NOT NULL AND delta > 0
    AND reason NOT LIKE 'stake%'
    AND linked_bounty_id NOT LIKE '%.dedup'
    AND agent_id <> 'hr-agent-web';
