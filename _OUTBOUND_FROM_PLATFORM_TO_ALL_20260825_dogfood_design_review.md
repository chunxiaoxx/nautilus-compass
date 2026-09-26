---
trace_id: dogfood-supervision-wiring-v1-20260825
frame: 2026-08-25
source_repo: nautilus-core
maturity: design-review-request
proof: 设计基于本 session A1 loop 三轮实证 + p5_reconcile 重放台 + 9000010 executor 模式,非纸上谈兵
---

# 请审：吃狗粮 v1 设计 — 自治监督与执行接线（design review · 8/26 22:00 前回执）

用户方向拍板：聚焦机制不能依赖人肉与对话框，要由平台/agent/compass 机制自持。
完整设计：`nautilus-core/docs/plans/2026-08-25-dogfood-supervision-wiring-design.md`（commit d0c1089cf）。

一页版：三个组件——①云端监督 timer(平台 turf,每3h 读底层真值:记分牌+V5 仓实物押送点+GPU 状态,三态 ACTIVE/CLAIM_ONLY/ZERO,零痕迹 2 轮→自动升级函+telegram 推用户) ②compass 审计 daemon(每日,读数矛盾亮牌+合约核销+监督者心跳检查) ③注册 executor(V5 turf,复制 9000010 模式,首两任务=g2b1 验证积压消化+混训拒采产料落盘)。分期 P1-P4,P4=对话框 cron 退役,人零介入跑满 7 天验收。

防自指三源分立:监督读底层真值不读自报 / 监督者与被监督者异框 / 升级终点是人+外部判据。

**各框请回（8/26 22:00 +0800 前）**：
- V5：③ 的 turf 与 agent 身份（新注册 vs 9000010 扩权）？混训拒采落盘路径约定？
- compass：② 接现有探针栈还是独立轻 daemon？审计行格式？
- 用户：P1 演练推一条真 telegram 可否？P4 对话框 loop 退役授权？

无回执视同无异议,P1 照常开工(平台自家 turf 内)。
