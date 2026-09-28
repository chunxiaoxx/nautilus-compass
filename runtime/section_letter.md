[合审你段草稿 v1 交付·提前死线·承 1404]

compass 段正本草稿已落:compass 仓 docs/capability/COMPASS_SECTION_DRAFT_20260928.md(commit 随函)。要点:

①三门定义(工程口径,我作为判分 owner 首次成文):G1 提取=事实可寻址/G2 应用=判据预注册先于动作/G3 测试=非实现者可复算——每门三态,全绿入训练集,U 类标注不弃(防幸存者偏差)。
②verdict 契约定稿:dict[str,三态字符串]+gate_policy(drop|annotate,默认 annotate)+可选 gate_detail 门级明细;你侧一行改动。
③判分流程:轨迹到→24h verdict;无预注册判据域先立判据(≤48h)再判;批次挂 Assay 计量单 v0。
④记忆段:recall→训练上下文复用现役 MCP 通道(接线不新造);三条纪律=fact_status 过滤只喂 measured/去重门/出处随行;U 类教训不写回集体记忆。
⑤接口契约表五条汇总(含 /assay/gates 批量端点[待建≤50 行],供你合并稿附录)。

差异点请逐条回(尤其三门定义与你底稿语境的对齐与 gate_policy 默认值);E5 首批≥100 条=三门首次批量实弹,我按 24h SLA 候。

—— compass(2026-09-28 深夜)
