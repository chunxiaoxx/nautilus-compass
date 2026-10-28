# FDE 多题样例并发交付 Design

> For Claude: brainstorming 已收口 · user 拍方案 C (并发舰 + 样板交付) · 现 docs/plans/2026-07-04-fde-multi-task-delivery-design.md design 阶段 · 下一 = writing-plans

## 1. 目标

飞书多维表格样例持续产出,7/4-7/9 增 5-50 题 grounded 入 EOVh 派活表与 S3 交付表。复用既有模板与流程,不重造。

## 2. 锚

- 锚 5 复用 - `produce_task.py` + `gapclosed_batch_runner.py` + fde-row-assembler 真复用,不另写并行。
- 锚 6 治根 - 每题跑完 grounded,与现 5/5 同质。
- 锚 3 反 D - ship 闭环完一题再启下题,清单 不闭合。

## 3. 当前真态 (grnd 7/4 22:40)

- 6 题真循买方目录模板,5 题入 EOVh 派活表,5/5 真入 fde_verdicts。
- producer 9000009 真注册,cred 持久化。
- H800 systemd 不可启真 grnd,supervisord 真活 (Task #34 running)。
- 3 接球阻:fde runner · soul verify · Conductor sync。
- 模板 `produce_50_variants.py` 真在 (commit `da7eebd50` 5 域 ×10 variant)。

## 4. 方案 C 拆 3 阶段

### 4.1 阶段 a - 模板批量派生 (本日)

- 复用 `produce_50_variants.py`,逐域提 variant 至目标 9 多学科。
- 新增 Robotics 域 5 道 + Quantum 域 5 道 + ComputerSys 5 道 + KernelEng 5 道。
- verifier 三铁律复检(每道模板生成后即跑)。

### 4.2 阶段 b - driver-ssh-push 真跑 (本日+1)

- H800 supervisord 没起来 仍 driver 手动跑。
- 每题 N=3 真数据 + 持久化进 `/api/platform/fde/verdict` (Task #0 修过路径)。
- 5/5 row 进 EOVh 派活表。复用 `submit_5tasks_to_feishu.py`。

### 4.3 阶段 c - 跨框 inbound 真接 (等回应)

- 推 Conductor 双向 sync (Task #35)。
- 等 soul verify (Task #36) 与 fde 真起 (Task #37)。
- §4 三判据真值累计触发 §5 §0-GOAL 改。

## 5. 输出物

- 50-100 题带 Task.md / README.md / baseline / verification / data / frontier_eval (9 文件)。
- 5-10 真数据行入 EOVh。
- 1 S3 交付 dlr (任一题真循环闭合)。

## 6. 不在本方案

- 不刷 verifier。
- 不替 V5/fde/soul 真接球。
- 不 autopilot 改 SSOT §0-GOAL。

## 7. 风险

- H800 daemon 仍手动,可能 batch 慢。
- verifier bug 复现,例 Cache verifier 路径 bug 真过 5 轮调试治根。
- inbound 真率低,3 接球可能数天无回应。

## 8. 验收

- §0 真 §4.1:trajectory 真行 ≥1 真绑 producer + 真分数 (已 ✓ 5/5)。
- §0 真 §4.2:fde_assignment 真派 ≥1 真 verified (等 #37)。
- §0 真 §4.3:fde_delivery_runner 真入 DLR ≥1 (等 #37)。

## 9. 依赖与文档

- **买方 spec**:`vtf/BUYER_SPEC_GenOpt_RL_20260702.md` (已 grnd 真查 80+ 行)
- **CHARTER**:`FDE_BUSINESS_CHARTER.md` (§1.3 12 类基准 + 第 3 类)
- **架构文档**:`genopt_factory/ARCHITECTURE.md` (14 文件契约)
- **停车位**:`genopt_factory/PARKING_LOT.md` (本周主线)

## 10. 不动项

- 不改 fde_assignment_runner · 不改 fde_delivery_runner。
- 不改 SSOT (前 §0-GOAL 真改需 §5 前置触发)。
- 不写新服务,复用既 daemon。

— 平台 · 7/4 22:55 UTC
