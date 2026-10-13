---
name: orgfuel-ORGG-bc4fbf3e41e99fc0-6502ee3df2
description: "判读档判例 SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930 · 二 · 提案:verdi"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-bc4fbf3e41e99fc0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930 · 二 · 提案:verdict-judge(动态权重三态判分器)
## 二 · 提案:verdict-judge(动态权重三态判分器)

**架构**(Laya 式小决策头,<100M 参数):
- 输入:verdict 工件(criteria@catalog 引用+原始读数+被检判分器输出+复算命令)
- 输出:三态 {pass/fail/insufficient_evidence} + 校准置信度(Jev 式:置信度即产品)
- 基线训练:三态 LoRA(Laya 决策头),语料=verdict 库(~50 条)→ 2000 条阈值

**动态权重(SSI 范式移植,核心差异点)**:
- 判分器部署后**持续学习**:每条新人工复核/独立复算结果=真值标签 → 在线小步更新(LoRA 增量)
- **上岗门**:新权重必须过回归门(历史 100 条判例零退化)才切换——动态但有闸
- 这是"验证业务本身长出验证引擎"(总纲原句)的实体化:verdict 越多→判分器越准→热路径判得越快→verdict 更多

**三个装载点**(compass+assay 结合):
1. **compass 记忆写入热路径**:写入前判 fact_status/dedup(七算子审计 9/7 判"写无 gate"的死结,由它解)
2. **assay 三门**:G1 自动腿(证据可解析+MINJA 注入核验)+G3 抽检第一腿(10% 抽样先过它,疑点才人工)
3. **F15 meta-judge**:三供应商复判的廉价第一腿(5% 抽样全量先过它,分歧才上 glm/MiniMax)

**反自指护栏**(RSI 深度启示 9/16 已定):
- 自训只限小判分器,不碰被评测的大模型
- 
