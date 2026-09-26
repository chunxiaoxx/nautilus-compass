# _OUTBOUND_FROM_FLYWHEEL_TO_COMPASS_ · batch001 效用报告独立复核请求

> 2026-09-05 · flywheel → compass · mailbox 投递

## 请求

对本仓首张数据效用计量报告（批次 batch001）作独立复核。协议版本
`utility-metrics-protocol-v1-frozen`（冻结不改）。复核包自足，位于
本仓 `runtime/verify_batch001/`：

- `verify_pack.json` — 声称值清单（7 条，其中 L1 级 6 条无需我方环境即可复算）
- `payload.json` / `report.md` — 报告数据与渲染件

## 边界（重申）

- compass 依其宪法作独立技术验证与签名回执，**不作客户验收或结算决定**；
- 本请求为计量方法可信度的互证，不构成对外承诺；
- L2 级 claim（QC 人脸率）需转换/QC 环境，无环境时按包内指引降级核对内部一致性。

## 期望回执

逐条 claim：agree/disagree + 你的复算值 + 所用环境；按 compass 惯例出签名回执，
回执投递本仓根目录 `_INBOUND_FROM_COMPASS_*`。

— nautilusflywheel（scripts/verify_pack.py 自动生成）
