# 孤儿资产视图 v0 · 2026-09-04(机器检测,治"建完就废"第 9/3 命题的量化延伸)

## ⚠️ 9/4 二次调研翻案(v1 口径,下文 v0 保留原样但口径已过时)

1. **"67% 零写入"实为"近 3 天零写入"**——pg_stat 计数器 8/31 20:00 被 reset,不能推出"从建成起就废"。窗起点此后必带出(table_health 内嵌)。
2. **不是空壳**:精确 count 后 69/94 有历史数据,最大 raid_votes 18123 行(raid 线当年真跑过,属"停摆遗迹"非"没用过")、judge_scores 1607、memory_records 1035。清=真丢数据。
3. **读侧活**:21 张被读 ≥10 次(tasks 3 万次/orders 1.6 万次,调用方=api/tasks.py 等活端点)——零写入≠死表。
4. **代码引用面**:36 张被 api/ops/tools 活引用;11 张仅 models 定义;46 张零引用(含 7 张备份表)。FK 链 13 条(customers/tasks/mcp_servers 等被引用,drop 受阻)。
5. **处置降级**:清理收益=零(千行级表不拖性能)风险=误杀(引用面证明误判率高)。挂账不清理;持续观测已接线 `ops/table_health.py`(架构页每日节 + table_health.jsonl 每日一条,趋势=git 历史)。
6. **v0 三坑(均已修进 table_health.py)**:n_live_tup planner 估计显示 0 差点误判空壳(→ --exact 精确 count);单表 InsufficientPrivilege 把连接打入 failed transaction 致 90+ 张 count 连锁失败(→ 逐表 rollback);采集自身 count 制造 seq_scan 污染"被读"指标(→ 读侧阈值 ≥10)。

---

> 数据源:生产 DB pg_stat_user_tables(9/3 18:31 UTC 实测)+ 本地 grep 引用检测。
> 性质:一次性分析投影(9/3 定谳:投影=按需生成,非待维护资产)。若用户拍分类处置,再考虑生成式化。

## 一、生产表:139 张,94 张零写入(67%)

有写入仅 45 张。活表 top:agent_tool_calls(ins 2.1 万)/helix_blocks(9448)/platform_audit(1891)/platform_conversation_memory(1228)/platform_reflection_log(941)。

**零写入表分四类(零写入 ≠ 可删,先分类再动手)**:

1. **备份/审计归档(留)**:`_backup_metrics_snapshots_phase3_20260506`、`hr_result_thinkstrip_backup_20260427`、`platform_bounties_dedup_audit_74584`、`archived_agents`(240 行)
2. **历史业务遗迹(用户拍后清)**:tenants、rewards、orders、platform_orders、referral_codes、genes、gene_adoptions、bounty_comments/scores、raid_performance_metrics、raid_execution_log、proposal_outcomes、platform_revenue_split、platform_social_security_rules、platform_employees、fde_admission_ledger、fde_produce_versions、partner_tasks、sandbox_experiments、mcp_servers、inbound_mentions 等(多属 3-7 月已停线业务:赏金/RAID/基因/租户/人社/FDE 旧版)
3. **双表并存 split-brain(收口候选)**:
   - `agent_capability_stats`(0 写)vs `platform_agent_capability_stats`(活,首笔 capability 9000014 记在这)——两套 capability 台账并存
   - `orders`(0)vs `platform_orders`(0)vs `org_mailbox`(活)——订单概念三次建表,活的在 mailbox 总线
4. **真孤儿(建了没用过)**:agent_identity_map、platform_shared_rules、platform_judge_scores、agent_tools、platform_v7_schedule、platform_external_events、platform_agent_keys、platform_evolution_log、knowledge_packages、agent_memory_records、agent_actions、agent_intent_history 等——机制建成、生产零流量,与 knowledge_nodes/emergent_patterns(8 张 models 未上生产实锤)同谱系

## 二、ops/tools 脚本引用检测(线索,非结论)

grep 零引用 6 个:`gen_architecture.py`(实为 frame_snapshot 经 ssh 调,活)/`send_snapshot_push.py`(同,活)/`gpu_v4_probe.py`、`g2_b1_historical_bug_runner.py`、`g2b1_fuel_export.py`、`key_manager_cli.py`(孤儿候选)。
**警告**:独立入口脚本靠 ssh/cron/手动跑,grep 不可见;判孤儿须对照 systemd timer 清单+ops 配方引用,单凭 grep 会误杀。

## 三、判读

- "建完就废"不是个案是**常态分布**:67% 零写入率说明历史上每次机制建设的存活率约 1/3——与军令状(9/10 快照消费裁决/9/17 台账正式单裁决)同一教训的数据版。
- 双表并存(capability/orders)再次验证 split-brain 慢性病:同一概念多处置表,活的只有一张。
- **建议不动手**,清单交用户拍:①历史遗迹批量归档 drop ②split-brain 收口(capability 台账以 platform_ 前缀表为准)③真孤儿逐个确认后清。清表=危险操作,走确认制。
