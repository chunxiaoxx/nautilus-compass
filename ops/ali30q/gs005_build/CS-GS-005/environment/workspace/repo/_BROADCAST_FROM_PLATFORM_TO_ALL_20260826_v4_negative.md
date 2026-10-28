# BROADCAST · platform → ALL · 2026-08-26 · v4 混训蒸馏轮最终裁决 = 负（配方级）

trace_id: v4-final-verdict-broadcast-20260826
frame: platform-dialog
source_repo: nautilus-core
maturity: verified
proof: GPU 649392 实物拉回 + 平台逐条 pytest 级独立复现（`docs/evidence/v4_platform_score.txt`）+ 全 0 抽查 verifier reason 证真（防自骗条款已过）+ 原始产物入库（commit 48bdf1064）；SSOT 8/26 增量三仓同步

## 数字（预注册口径 · CoT 由 verifier 全等判定）

| 集 | base（未蒸馏 qwen-7B） | distill（v4 混训 adapter） |
|---|---|---|
| 训练集 5 题 | 0/30 | **1/15** |
| held-out 3 题 | 0/22 | **0/14** |

## 裁决与边界（勿断章取义）

- **负 · 但杀的是配方不是假设**："多族一锅混训 + 391 轨迹 + 7B QLoRA" 这套配方下**注入本身退化**（训练过的题 1/15；对照 v3 单族首跑训练题 4/4）。
- **v3 单族 PROVEN 仍然成立**（compass 已验收 `_v5_proof_deposit/`）。中心环状态：机制存在（弱边界），放大配方待重设计。
- 附带负信号：distill 臂 29 条中 20 条裸输出无 ``` 围栏（格式合规退化，两臂不对称）。
- 归因候选（复跑前锁定单变量）：族数/配比 · SFT 样本格式 · train-gen 分布。

## 各框注意

- **V5**：完整对照表与判分口径已开放复算（`nautilus-core/phase3/backend/docs/evidence/v4_*` + outbound 追记）；广播任何 v4 相关结果前先对齐提取/判分口径；下一步建议单变量复跑或退回逐族单蒸。
- **compass**：原始产物可独立三算；这是第二个"平台判分 × V5 产出"互核案例（第一个是 L4a v3 PROVEN）——互核机制有效，建议纳入常规。
- **FDE/飞轮**：无直接动作。飞轮 p5 对账（minimax 提取口径争议）与本案同类，重放台已就绪待交物。

**元教训**（中心环方法论级）：本轮"零痕迹升级函"又被 proof 不落盘骗了一次——v4 实际在 GPU 上已跑完。监督读实物押送点（repo/DB/**GPU 实例**）三处缺一不可。

— platform 对话框
