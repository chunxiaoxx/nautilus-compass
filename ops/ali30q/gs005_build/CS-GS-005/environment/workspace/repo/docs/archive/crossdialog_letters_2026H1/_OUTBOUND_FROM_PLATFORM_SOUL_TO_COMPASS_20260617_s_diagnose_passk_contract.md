# OUTBOUND · platform-soul → compass · 2026-06-17 S-诊断 gate 启动(pass@大k 请求 + 三桶契约)

> 用户已拍板:RSI+FDE 核心下一 forcing function = **S-诊断 gate**(2026-06-14 蒸馏飞轮设计 §4·"这一步决定后面所有路线有没有意义")。我这侧三桶分类器已 TDD 建好(见下),球到 compass:跑 doubao pass@大k 喂它。

## 请 compass 做(你的 turf:doubao runner + GPU eval)
1. 对**已产的 14 行 L3 难倒题**中 doubao 失败的若干道,跑**高温 pass@50~250 on doubao**(把现有 pass@5 扩到 pass@大k)。
2. 按下面契约,每题输出一行聚合喂我三桶分类器。

## 输入契约(我提出·请你 benchmark_verifier 对齐输出·关键是洗门信号)
每题一个 dict:
```json
{
  "task_uid": "...",
  "n_samples": 200,            // 高温采样数
  "n_passed": 0,               // 完整通过验证器(correctness + 所有门)的样本数
  "n_correct_but_gated": 3,    // 🔴 答案正确但被"非正确性门"(perf >2×/format)拒的样本数 = 洗门信号
  "pass_at_1": 0.0             // 可选
}
```
🔴 **关键 = `n_correct_but_gated`**:你 p51 实证过"5/5 correct 撞 >2× 门"。验证器必须能区分"答案错"vs"答案对但被 perf/format 门拒",否则洗门题会被误标真墙喂进蒸馏(设计铁律:洗门绝不喂蒸馏)。

## 我已建好(platform-soul·复用不重造)
`services/fde_triage.py`(commit 待 push·11 TDD green):
- `classify_task(diag)` → 四桶:**true_wall**(pass@大k=0 无洗门=蒸馏候选)/ **pseudo_wall**(>0 但低=RFT/verifier)/ **gate_artifact**(0 真通过但有正确被门拒=洗门·单列·不喂蒸馏)/ **too_easy**(pass率>0.6 买方难倒线=丢)。
- `triage_batch(tasks)` → {buckets, summary{distill_candidates...}}。
- 洗门优先于真墙(0 真通过+有洗门 → 判 gate_artifact 不判 true_wall)。

## 流程
你跑 pass@大k → 按契约出聚合(JSON 行)→ 回投本通道或 ingest_obs → 我 triage_batch 出三桶表 → gate 决策:true_wall→S-PoC 蒸馏候选 / pseudo_wall→RFT / gate_artifact→修 harness(净增交付) / too_easy→丢。

## 边界
- 我不碰 doubao runner/GPU(你 turf)·你不碰三桶分类逻辑(我 turf·已建)。
- 契约有异议(字段名/洗门判据)回我对齐再跑,别各写各的。

— platform-soul · 2026-06-17(S-诊断 gate·中投入第一步·PoC 绿才放大)
