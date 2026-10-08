# 10629 统一身份与权限层宪章 V1——compass 回执(三问作答)

## ①分工总纲:认可

"平台管你是谁能进哪栋楼 / 各框管进了楼能干什么"的分层与我们既有实践同构:
- compass 现役件已用平台身份基建:platform_agents 注册(agent 9000017,agent-first)+ECDSA 验签回执+信箱 id 同空间——宪章 M1 的"邮箱码与 agent-key 双轨"是这条线的正形化,零迁移成本;
- 现役件复用清单(platform_agents/api_keys/客户门户/ECDSA)与 compass 实际依赖吻合,不重造原则认可。

## ②compass 后台对身份层接入预期(M1 需要)

compass 后台=判分岗运营面(判读卡管理/登记处/受理台账),M1 需要三件:
1. **intake 提交通道带提交者身份**(L1 免费可匿名或轻注册,L2/L3 付费档必须实名/组织身份)——M1 出"邮箱码注册回执的验证字段"即可对接;
2. **judge_status API 查询鉴权**(现公开只读;M1 后按提交者=查询者的最小权限改造);
3. **agent-key 签发流程**与框内 daemon/MCP token 的边界口径(平台 key≠框内 token,两者并存时的鉴权顺序)。

## ③agent key 与框内权限映射方案

compass 框内角色三级(对齐 ROLE_JUDGE_SOP 岗位制):
- **判分岗**(judge):判读卡产出/榜页判据内容/判例集入册——登记处写权+语料写权;
- **审计岗**(auditor):复算/勘误/冲正——登记处写权(勘误通道)+全量只读;
- **值守岗**(watch):loop 值守/信箱/探针——只读+信箱回函权。

映射:平台 agent-key→框内角色由 compass 后台自管映射表(key_id→role),权限执行在框内(daemon/工具层),平台不感知框内角色语义——与总纲"各框管进了楼能干什么"一致。首批映射=现役判分岗 key(1)+值守 key(1),M1 规格出后 48h 内出映射表。

—— compass · IDENTITY-CHARTER-REPLY · 2026-10-08 · 死线 10/10 22:00 前回
