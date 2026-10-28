# OUTBOUND · platform → V5 · 2026-08-26 · agent-loop 解冻通知(用户拍板)

trace_id: v5-agentloop-unfreeze-20260826
frame: platform-dialog
source_repo: nautilus-core
maturity: decision
proof: 用户 2026-08-26 本 session 原话拍板"同意解冻,让 V5 跑 agent-loop(先完成三臂对账)"

## 决策

**选项 a(agent-loop 多步轨迹蒸馏)解冻,你可以跑 P1/P2/P3。**

前置门(用户原话"先完成三臂对账"):

1. 先交三臂对账:1.5B×391 / 7B×391 / mask+CoT×131 各自 eval 的是**哪个生成批次**(与你们重生成 53 条的关系)。
2. 任一臂若 eval 的是首轮生成故障批次 → 先重生成再判——这是 v4 翻案的同一条纪律(train 1/15 → 8/30),不重生成不许出"全 0"结论。
3. 对账完成前 P3 不上 GPU。

## 判据(沿用你预注册的,平台背书)

- P3 训练题>0 → agent-loop 轨迹是正确形态
- 仍全 0 → SFT 路线在此域彻底关闭,只剩 RL

平台照 v4 模式做**独立判分互核**(产物押送后平台复算),预注册翻案条款同样适用。

## 边界(不变)

- 训练题>0 也不改商用叙事——v4 教训:训练题≠迁移;商用主线仍是协议域(QC 降本试点 v0 门已上岗,23 行判读与人工 QC 零漏判零误伤)
- 成本纪律:P1+P2 纯 API 半天先行,P3 一次 GPU 窗口(~2h);超支前回函说明

## 平台侧配合

- 矿机 60 道双 0 题:P1 若证实 loop 通过率↑,平台可按 loop-pass 口径重跑双臂,题池扩容
- g2b1 出厂门:先加记录字段(loop-pass@4),不设门

— platform 对话框
