# BGE-m3 × nautilus-compass 联动介绍(供与北京智源 BAAI 沟通用 · 2026-09-04)

> 用途:用户与智源团队沟通时发送/展示。数字口径与对外发布物料完全一致(SCOREBOARD 定案)。
> 联系方式/落款由用户补。

---

## 我们是谁

**nautilus-compass**:开源(Modified MIT)的本地优先 agent 记忆层——AI agent 的长期记忆基础设施。设计原则:写入时零 LLM 调用、原文无损存储、全部智能在读取端;支持多 agent 组织记忆(跨 agent 记忆胶囊)与三层多租户隔离。130 天开发,771 commits(603 由我们的 agent 舰队自行提交——我们自己的 AI 原生组织就跑在这套记忆上)。

## BGE-m3 在我们架构中的位置

BGE-m3 是我们**唯一的嵌入模型**,承担两层:

1. **生产层**:所有记忆写入的本地向量化(CPU 推理,零嵌入成本、零数据出域)——这是"个人本地永久免费"商业模式成立的技术前提
2. **评测层**:全部基准评测的检索 embedder(含与 mem0 等厂商的对照实验,BGE-m3 跨系统统一,保证公平)

选型理由:多语(中英混合 agent 语料)、CPU 可跑(本地部署硬约束)、与 BM25 词面检索 RRF 融合后精确标识符与时序查询互补。

## 用 BGE-m3 做出的成绩(全部可复现,复现成本 ≈$3.50 GPU 时)

| 战场 | 结果 |
|---|---|
| LongMemEval-S 检索对打(500 题) | P@1 **0.890** vs mem0 0.774(+11.6pt);P@5 0.978;MRR 0.929 |
| LOCOMO 客场(n=1986) | P@1 **0.644** vs mem0 0.592 |
| LongMemEval-S 端到端(500 题) | **75.4%**(81.6% 剔除判官故障双口径披露) |
| LongMemEval-V2 官方基准(451 题双域) | web **40.0%** / ent **38.4%**(untuned 19.6/12.8) |
| EverMemBench | **44.4-47.3** vs Mem0 37.09 / Zep 39.97 / MemOS 42.55 |
| 检索延迟 | p95 **0.34-0.80s**(对照 LLM controller 26.9s,约 80×) |

方法论侧:我们发布了一套 LLM 判分卫生学协议(抓出并修正自己评测判官的 5 次基础设施故障),论文在投。

## 希望与智源探索的方向

1. **生态收录 / case study**:nautilus-compass 作为 BGE-m3 在 agent 记忆场景的生产案例(全链路可复现证据开源)
2. **联合内容**:面向中文开发者社区的技术内容("BGE-m3 驱动的本地 agent 记忆层"),我们出全部数据与实测
3. **模型迭代协同**:BGE 系后续版本的可提前评估/反馈(我们的基准与对打管线可即插即用)

## 链接

- GitHub:https://github.com/chunxiaoxx/nautilus-compass
- 托管版(open beta):https://compass.nautilus.social
- 成绩册与证据链:仓库 `docs/nautilusmem/`(SCOREBOARD.md / PROTOCOL.md)

*Modified MIT · 本地优先 · 数据不出域*
