# 孤儿表扫描 · v1 定稿(2026-09-04 · 口径修正后清理建议撤回,降级挂账)

> v0(会话内初判)曾建议清理若干"零读"表;用户要求先调研再议 → 调研推翻 v0 口径,
> 本 v1 为定稿。采集工具:`ops/table_health.py`(pg_stat_user_tables + stats_reset 窗)。

## 结论(撤销清理建议)

**不清理,挂账待复评。** v0 的"零读=孤儿可清"判断在三个口径上全部站不住:

1. **统计窗仅 3 天**:pg_stats 8/31 被 reset 过,9/4 扫描时"读=0"只代表 reset 后三天没人读,
   不能推出"从未被读"。低频表(月度报表/审计回溯)在 3 天窗里读数必然为 0。
2. **非空壳**:被判零读的表多数有历史数据——judge_scores 1607 行、raid_votes 18123 行
   (后者是停摆遗迹而非"没用过":数据是历史业务写入的)。删表=删组织历史资产。
3. **读侧与代码侧都是活的**:tasks 表 3 万行被运维路径高频扫描;约 36 张表被活代码引用;
   13 条 FK 链挂着别的活表。静态代码引用为零 ≠ 运行时零消费(动态 SQL/运维脚本不可见)。

## 复评条件(挂账,非已决)

等 stats_reset 后统计窗 ≥ 30 天(约 **2026-09-30**)重跑:

```
python ops/table_health.py --exact     # 云端跑;输出 markdown + JSON 尾行
```

届时对"窗 ≥30 天且读 < 10 且行数 > 0 且代码引用为零"的表再逐张过堂。
raid_votes 类"停摆遗迹"单独归类:不删,但标注归属业务线与停摆时间。

## 方法论沉淀(采集配方自身的坑,已修进 table_health.py)

- **观测污染**:--exact 逐表 count 自身制造 seq_scan 且计入统计→READ_FLOOR=10 阈值化防误判。
- **psycopg2 连锁失败**:首表 InsufficientPrivilege 会把连接打入 failed transaction,
  后续 90+ 张 count 全部静默失败 fallback 0→except 里必须 s.rollback() 并记 count_failed。
- **n_live_tup 不可信**:planner 长期未 ANALYZE,估计值与真实行数差数量级→精确 count 单独跑。
