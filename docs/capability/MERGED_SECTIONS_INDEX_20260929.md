# 能力架构合并段 · 合审完成索引(2026-09-29)

> 合审两轮闭环(#1404→1431→1436):v5 全盘采纳 compass 三门定稿(三态+
> gate_policy 默认 annotate 当日落地 TDD 9 绿);compass 采纳 v5 差异回复。
> **差异清零,两段齐,可入融合正本。**

## 段坐标(可寻址,不重抄)

- **compass 段**(清洗判分+记忆中枢):compass 仓 docs/capability/COMPASS_SECTION_DRAFT_20260928.md(83444f01)
- **v5 段**(采集+训练+回流):v5 仓 docs/capability/V5_SECTION_DRAFT_20260929.md

## 合并契约表(十口,合并稿附录正本)

| # | 契约 | 方向 | 状态 |
|---|---|---|---|
| 1 | three_gate_verdicts{sid:三态} | compass→v5 | ✅已接(v5 当日 commit) |
| 2 | gate_policy drop\|annotate(默认 annotate) | 契约字段 | ✅已落地 |
| 3 | 判分 SLA 24h/立判据≤48h | compass 承诺 | ✅ |
| 4 | /assay/gates 批量端点 | compass 建 | [待建]≤50 行 |
| 5 | 轨迹批(≥100 带标) | v5→compass | E5 后 |
| 6 | 计量单 v0 挂账 | compass→platform | 通道在产 |
| 7 | recall 注入三纪律 | compass→v5 学生 | 现役 |
| 8 | 教训写回走写入门 | v5→compass | 现役 |
| 9 | flywheel 管线尾挂 postprocessor | v5↔flywheel | 约定函在途 |
| 10 | 学生模型批 3 报名 | v5→platform | 待排 |

## 红线(两段共同)

判据预注册先于动作/判分资产禁改/生产者≠判分者/趋势线只计未碰题。
