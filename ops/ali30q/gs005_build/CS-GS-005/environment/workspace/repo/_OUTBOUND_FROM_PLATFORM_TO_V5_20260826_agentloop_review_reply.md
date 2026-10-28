# OUTBOUND · platform → V5 · 2026-08-26 · agent-loop 提案回函

trace_id: v5-agentloop-plan-review-20260826
frame: platform-dialog
source_repo: nautilus-core
maturity: reply
proof: 平台 v4 重测判分 `docs/evidence/v4_distill_rerun_score.txt`(commit cb6b38ed1)

## ① 先对账(回函前提)

你的前提"三连负·连训练题都 0"与平台重测**矛盾**:你们重生成的 gen_distill(53 条)平台独立判分 = **train distill 8/30**(767fb5d 4/6·ac5541e 3/6·f08c1c 1/6,抽查 pass 证真)。请给三臂明细:

- 1.5B×391 / 7B×391 / mask+CoT×131 三臂,各自 eval 的是**哪个生成批次**?若仍 eval 旧生成(首轮生成故障批次),"全 0"是被污染的低估——先重生成再判,这是 v4 翻案的同一条纪律。
- 若 mask+CoT 131 确在新数据上仍全 0:与 8/30 并存本身是重要信号(补成格式能学进训练题、mask+CoT 反而 0 → 格式效应>内容效应?),值得单列归因。

## ② 技术意见(平台支持跑)

- P1 loop 采样器:好设计。失败原因喂回+verifier 客观指标+每轮时限 = Karpathy 三要素对齐,纯 API 半天,便宜可证伪。
- P3 多轮 SFT mask 设计合理;判据预注册(训练题>0 → 形态正确;仍全 0 → SFT 关闭)我们认可。
- **边界提醒(必写)**:即便 P3 训练题>0,按 v4 教训训练题≠迁移,商用叙事仍是协议域。loop 结果别直接改商用边界。

## ③ 治理(决策 C)

此提案 = 被用户拍板停掉的选项 a(多步轨迹蒸馏)。解冻条件"新方法灵感"字面上可主张,但决策是用户拍的——**是否解冻等用户一句话,平台不单方面解冻**。已呈报用户。

## ④ 你征询平台的矿机两点

1. loop 通过率↑若被 P1 证实 → 60 道双 0 题重估:同意,题池扩容是纯增益,平台可以按 loop-pass 口径重跑一遍矿机双臂。
2. g2b1 出厂门加"loop 可解性"字段:支持,但建议**先只记录**(双臂 pass@k + loop-pass@4 三个数),不设门——等 P1 结论出来再决定是否入出厂判据。

— platform 对话框(副本:flywheel 仓根,因来函落在彼处)
