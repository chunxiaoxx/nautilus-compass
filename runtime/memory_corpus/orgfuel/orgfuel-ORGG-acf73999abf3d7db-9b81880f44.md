---
name: orgfuel-ORGG-acf73999abf3d7db-9b81880f44
description: "判读档判例 NACRE_WHITEPAPER_V1 · 第一章 模型是什么(一句话) ## 第一章 模型是什么(一句话)"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-acf73999abf3d7db
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 NACRE_WHITEPAPER_V1 · 第一章 模型是什么(一句话)
## 第一章 模型是什么(一句话)

**NACRE 是 judgment-native 的判分模型**:输入任意 agent/系统的产出工件,输出**三态判定(PASS / FAIL / UNVERIFIABLE)+证据分层标注**;以增量 LoRA delta 的形式吸收组织判例与勘误,经零翻转门验证后写入版本化 registry,旧案判定永不回退。

如 Metis 之于 memory(记忆原生基模),NACRE 之于 judgment(判分原生判分模型)。

**为什么是三态**:判分场景的常态不是"对错分明",而是"证据不足"。强制二选一的判分器会生产幻觉判定;NACRE 的第三态 UNVERIFIABLE 是产品的一部分——"判不动就明说"本身是交付物(判例集 16 案中 U 态与证据三层标注全程在线 [实测])。
