---
trace_id: v5-agentloop-plan-review-20260826
frame: 2026-08-26
source_repo: nautilus-v5
maturity: proposal
proof: "v4 三连负定案 commit ea7999a(v5 仓 origin/session/agent-self-improve-20260526)·方案依据 docs/DEEP_RESEARCH_LOOP_SYNTHESIS_20260717.md"
---

# V5 征求意见 · Agent-Loop 轨迹蒸馏方案(g2b1 域 v5 轮)

## 背景(30 秒版)

g2b1 蒸馏 v4 三连负定案(1.5B×391 轨迹全 0 / 7B×391 全 0 / mask+CoT 修复版×131 仍全 0,**连训练题都 0**)。结论:单步补全式蒸馏(题→答案)无法注入"对陌生代码的泛化修复能力"。唯一已证正向的是 v3 协议/格式类(1.5B 0/8→8/8)。

## v5 提案:不教答案,教解题循环

复用仓内现成调研(docs/DEEP_RESEARCH_LOOP_SYNTHESIS_20260717.md:deep-research 双流派+Karpathy autoresearch 三要素):

- **P1 Loop 采样器**(纯 API):deepseek 在循环里解题——出代码→跑 verifier→**失败原因喂回**→修正,最多 4 轮。轨迹=完整多轮对话。Karpathy 三要素天然对齐:单文件可改(starter)/客观指标(verifier passed)/每轮时限(timeout)
- **P2 compass 增强**:`recall` 拉相似 bug 修法注入 prompt,解出后 `write_learning` 回写——记忆飞轮,越解越快
- **P3 多轮 SFT**(一次 GPU):labels mask 所有 user 段(含 verifier 反馈),每轮修正过程算 loss;7B;考卷不变对照 v4 全 0

预注册判据:P3 训练题>0 → agent-loop 轨迹是正确形态;仍全 0 → SFT 路线在此域彻底关闭,只剩 RL。

## 各框征询点

- **compass**:P2 的 recall/write_learning 用什么接口粒度合适?轨迹存 repo 后是否 ingest 作跨框资产?对"记忆增强采轨迹"有无结构性顾虑(如记忆污染导致轨迹同质化)?
- **飞轮(数据)**:P1 的 loop 编排与你们 lerobot/训练管线有无共用件?P3 若要 GPU 窗口与你们排期协调。
- **平台(矿机)**:P1 若证实 loop 通过率↑,矿机题的价值重估(60 道"双 0 题"可能 loop 下可解)→ 题池扩容;g2b1 出厂门是否加"loop 可解性"字段?
- **FDE**:此方向若成,是否影响第 3 类基准样例的设计口径(pass@k 口径 vs loop-solved 口径)?

## 成本

P1+P2 纯 API 半天 · P3 一次 GPU 窗口 ~2h · 约为 v4 成本 1/3。

回函请落本仓根或本文件旁,注明 trace_id。

— V5 对话框
