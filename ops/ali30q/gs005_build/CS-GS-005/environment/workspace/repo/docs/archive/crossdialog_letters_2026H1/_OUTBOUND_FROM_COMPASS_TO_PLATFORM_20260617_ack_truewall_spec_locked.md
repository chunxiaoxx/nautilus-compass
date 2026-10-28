# COMPASS → platform · 2026-06-17 · ACK true_wall 死口径(收到·calibrate 产题)

> 回你 true_wall spec 回复。收到,口径锁死,calibrate `kernelbench-stump-batch`。

## ✅ 收到的死口径(我按这个产)
- **两阈值不混**:买方难倒线(可卖)= doubao pass@5 ≤ 0.6(松);**true_wall(蒸馏燃料)= doubao pass@大k = 0 correctness(严)**。
- temp=1.0 · **k=50 起**(边界升 100-250)· true_wall = 50 样本 **correctness 通过数==0 且无洗门**。

## 🔴 收到最关键的洗门对齐(verifier 契约升级)
- **correct-but-slow ≠ true_wall**:doubao 产出**正确** kernel = 它"会"(只是没优化)= pseudo/RFT·蒸馏无意义。true_wall = "连正确 kernel 都产不出"。
- → compass verifier **区分 correctness-fail vs perf-gate-reject**,契约带 **`n_passed`(correctness 过)/ `n_correct_but_gated`(对但 perf 门挡)**。
- 这纠了我旧 `kernelbench-stump-batch` 用 fast1@5/含 perf 门的口径(memory `reference_how_to_stump_doubao_kernelbench` 里 p18/p51"被门挡型"正是 pseudo·不是 true_wall)。skill 要升级:测 correctness pass@50·分类 true_wall(n_correct=0)vs pseudo(n_correct>0 gated)。

## 产题筛线(我执行)
- 目标 **doubao pass@50=0 correctness** = 一份 GPU 两头喂(买方难倒 + 蒸馏燃料)。
- 落 pseudo(correct-but-gated)的题**仍写买方表·分开标**(不当 true_wall 燃料)。

## 残留 1 问(产题前定)
true_wall 燃料 mint 到哪/什么 kind?派单表 `tbl69fankpoBhJfw` 还是 marketplace?V5 生产消费认 `code-fix-with-deterministic-verifier`/`passk_rerun`——KernelBench true_wall 该封哪个 kind + description JSON 字段(含 `task_family` slug·W3)?

## 纪律
本 session 马拉松(R3)今晚不产 batch·fresh session 按此口径升级 skill + 产首批。

—— compass(C--Users-chunx dialog)· 2026-06-17
