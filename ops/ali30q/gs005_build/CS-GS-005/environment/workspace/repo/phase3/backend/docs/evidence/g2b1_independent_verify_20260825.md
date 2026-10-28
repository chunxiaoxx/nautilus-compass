# g2b1 verdict 独立复现 · 首次抽样(2026-08-25 · platform)

抽样: g2b1-exec-ffbe0dfb38-ark_glm.json(对应云 DB verdict g2b1:e49e8ade7849 一族)
方法: V5 仓临时 worktree @ buggy_commit 2d01cbd2,双门重放:
- 门A(starter必败): buggy 代码 + reference fix 的测试文件 → **FAIL ✅**(测试不存在于 buggy commit,须从 fix commit 带回)
- 门B(fix必过): + reference_fix_commit 修复 fde_consumer.py → **PASS ✅**
结论: 该任务双门成立,executor 自报 test_passed 与独立复现一致(n=1)。

## 顺带发现(结构问题,待处理)
1. **verify-spine 断裂**: g2b1 verdict task_uid=`g2b1:<hash>` 与 fde_dispatch 零关联(无 dispatch 行)→ auto-verify/income 门无法触达这批 verdict,external_verified 全 false 不是"没来得及验",是**链路不通**。
2. **winning_diff 非标格式**: LLM 产 diff hunk 行数不自谐,`git apply --recount` 亦拒——独立复现只能用 reference commit 等价替代;批量验 diff 需先做 diff 规范化(或要求 executor 存全文件)。
3. buggy/fix commit 属 nautilus-v5 仓(自修复题源),平台验证需能读 V5 仓历史——dogfood supervisor 设计的数据源要加这一项。

下一步: 扩 n≥5 抽样 → 修 spine(dispatch 关联或 verify 直读 evidence)→ external_verified 回写。
