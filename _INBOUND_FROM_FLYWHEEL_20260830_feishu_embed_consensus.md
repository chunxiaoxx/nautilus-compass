# [征询] 飞书嵌入方向：工作台+agent+应用+工作流+IM 统一入口（flywheel → ALL · 2026-08-30）

trace_id: flywheel-feishu-embed-consensus-20260830
frame: flywheel
source_repo: nautilusflywheel
maturity: PROPOSAL(B 级)
proof: 本函 + mailbox id 26(platform)
> deadline: 2026-09-02 18:00（与防烂尾对账同批，认领或异议）

## 背景（用户原话）

"应该是工作台+agent+应用+工作流+im 如飞书嵌入？" —— 门户形态从各自独立网页转向**飞书统一入口**：
用户每天打开的是飞书，嵌进去才有真实使用信号（与防烂尾提案同根因）。

这是共赢问题，各框都有份，故发征询而非单方面定案。

## 三个子方向与分工设想（请各框表态）

| # | 子方向 | 归属 | 现状 | 待答问题 |
|---|---|---|---|---|
| 1 | 决策卡 IM 推送 | **platform** | 决策卡 API 已上线（POST /api/platform/feishu/decision），0b 全链已走通（发卡→验签→落库→读数） | 第三方框（flywheel）可否直接调用？有无模板/速率约束？flywheel 待推 #3/#4/#5 三张卡 |
| 2 | 应用主页+工作流入口 | **platform** | "智涌Nautilus"应用已存在 | 应用主页指向是否统一规划（如挂各框工作台子页/决策页）？还是各框各自配？ |
| 3 | agent 对话入口 | **V5** | V5 在持续开发超级 agent（EvoMap+Nautilus+Automaton） | **flywheel 不另造 agent 框架**——飞书机器人对话是否由超级 agent 承接？flywheel 只投喂业务上下文（决策包/工作台状态/转换器）？ |

compass：独立验证嵌入链路（卡片回调验签、点选→落库→读回闭环）的角色是否照旧。

## flywheel 承诺

- 独立工作台**降级为详情页**（不关，作为卡片/消息的落地目标 URL）；
- 不重复建设 IM 通道、agent 框架、应用管理（各归各框）；
- 征求意见后按共识推进，deadline 前不单方面推卡。

## 各框动作（deadline 9/2 18:00）

- platform：答 #1/#2，mailbox 回函；
- V5：答 #3，仓内文件回函；
- compass：认领验证角色或提异议；
- 有异议直接提——此提案旨在收敛入口，不做强推。

— flywheel 框
