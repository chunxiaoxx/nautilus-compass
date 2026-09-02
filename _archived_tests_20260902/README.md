# _archived_tests_20260902 · 孤儿测试归档

## test_inbound_select.py(自 tests/hooks/)

- 测试对象:`~/.claude/hooks/inbound_outbound_surface.py`(入站函件选择 hook)
- 归档原因:**被测实现已不存在**——hook 文件在用户目录与 repo ops/ 均已消失(大概率 8/28 遗忘/归档轮清理),全仓 grep 零引用(仅本测试自引用)。留着 = pytest 永久收集错误(FileNotFoundError),污染全量红绿读数。
- 归档日期:2026-09-02(全量测试复活专项)。
- 复活条件:若 inbound_outbound_surface hook 恢复服役(文件回到 ~/.claude/hooks/ 或 ops/),把本测试移回 tests/hooks/ 并将路径常量改为从 repo 读。
