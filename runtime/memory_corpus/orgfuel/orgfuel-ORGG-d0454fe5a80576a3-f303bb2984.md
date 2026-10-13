---
name: orgfuel-ORGG-d0454fe5a80576a3-f303bb2984
description: "判读档判例 2026-06-21-memory-capsule-evolution-design · 1b. OKF(G"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d0454fe5a80576a3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-21-memory-capsule-evolution-design · 1b. OKF(Google 开放知识格式)= 我们的「格式层」标准(2026-06-21 补)
## 1b. OKF(Google 开放知识格式)= 我们的「格式层」标准(2026-06-21 补)

**OKF v0.1**(Google Cloud 2026-06-12 发布·`github.com/GoogleCloudPlatform/knowledge-catalog/okf`):知识 = 一目录 `.md` + YAML frontmatter;唯一必需字段 `type`(可选 title/description/resource/tags/timestamp);markdown 链接 `[..](/path.md)` 构成有向知识图谱 + "cited by" 反链;**厂商中立·无 schema registry·无中央权威**("能 cat 就能读·能 git clone 就能 ship");Knowledge Bundle = 分发单元,Concept = 单个 md 文档。

**🎯 关键:我们的 compass memory 本来就几乎是 OKF** — `.md` + YAML frontmatter(`name`/`description`/`metadata.type`)+ `[[name]]` 交叉链接 + `MEMORY.md` 索引 + daemon 算 link graph。**对齐成本极低**。

**三层架构定位(OKF / GEP / compass 互补不冲突)**:
| 层 | 是什么 | 我们怎么用 |
|---|---|---|
| **格式层 = OKF** | 知识怎么**存/交换**(静态·互操作·厂商中立) | 
