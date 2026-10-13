---
name: orgfuel-ORGG-fc7abf8a08950848-d769734ff4
description: "判读档判例 SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930 · 一 · 两个参考源的一手"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fc7abf8a08950848
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930 · 一 · 两个参考源的一手状态
## 一 · 两个参考源的一手状态

**Jev/TypeSafe(一手充足)**:
- 三原语 choice/score/noul(与 T3 口径同名);RLCD=Reinforcement Learning for Calibrated Decisions(proper scoring rule RL,校准即训练目标)
- Laya 开源决策引擎(Apache 2.0):两层 transformer+选项打分+act 头,多语言版 100+(可作私有化底座)
- F15 实测已证:Choice 三态 {pass, fail, insufficient_evidence} 与 compass 三态天然对齐(1a657978)

**SSI(一手=爆料级,论文未发,细节待官方)**:
- 2026-08 首模型曝光方向:**TTT(Test-Time Training 测试时训练)小型推理引擎**——用专门数据学「如何学习」,解决问题过程中**更新部分权重**;规模小但对抗大模型;下一代规模 ×10(源:36氪/头条转 X 爆料 + HappyRock 深读 + Dwarkesh 访谈转述)
- Ilya 范式:部署=学习期,权重持续更新(反"预训练→冻结")
- 8/22 组织记忆锚点(已验):**SSI 持续学习需要 value function 真值供给=验证机构在上游**——带签名 verdict 语料是我们的自有资产
- 风险披露:TTT 细节均为二手转述,架构设计以 Laya/Jev 侧一手为准,SSI 只取"部署后持续更新权重"的范式
