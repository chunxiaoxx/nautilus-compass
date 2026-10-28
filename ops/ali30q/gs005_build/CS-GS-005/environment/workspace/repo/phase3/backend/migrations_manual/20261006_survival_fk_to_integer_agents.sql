-- 2026-10-06 双身份表 FK 断裂修复(A 案,HR 发现·平台拍)
-- 事故:agent_first_register(唯一合宪注册通道,宪法 §0-ARCH)100% 失败——
--   agent_survival.agent_id varchar + FK→platform_agents(varchar 生态,违宪侧),
--   而注册写 agents(int 正册);两台账永不相交,agent_survival 总行数=0(从未成功过)。
-- 附 bug:except 吞异常不 rollback,PendingRollback 态炸 lazy refresh=半注册+500(代码侧另修 agent_first_register.py)。
-- 修法:FK 改指 agents(整数生态=合宪侧);表 0 行,无数据迁移。
-- 验证:执行后 HR 框重走全链注册=端到端。

ALTER TABLE agent_survival DROP CONSTRAINT agent_survival_agent_id_fkey;
ALTER TABLE agent_survival ALTER COLUMN agent_id TYPE integer USING agent_id::integer;
ALTER TABLE agent_survival ADD CONSTRAINT agent_survival_agent_id_fkey
  FOREIGN KEY (agent_id) REFERENCES agents(agent_id);

-- 清理:HR 半注册残留(无 key/无 survival/无 platform_agents 行,仅 agents 一行)
DELETE FROM agents WHERE agent_id = 9000024 AND name = 'compass-evidence-auditor';
