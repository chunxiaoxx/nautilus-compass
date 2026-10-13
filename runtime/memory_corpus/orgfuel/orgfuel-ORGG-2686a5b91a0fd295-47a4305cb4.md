---
name: orgfuel-ORGG-2686a5b91a0fd295-47a4305cb4
description: "判读档判例 NACRE_NATIVIZATION_ROADMAP_V0_20261007 · 四、原生专家技能:"专家="
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-2686a5b91a0fd295
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 NACRE_NATIVIZATION_ROADMAP_V0_20261007 · 四、原生专家技能:"专家=域判例的函数"(分域原生化)
## 四、原生专家技能:"专家=域判例的函数"(分域原生化)

- **创新机制**:各域专家技能不靠通用大模型 SFT,靠**域判例集蒸馏**(Agent Distillation,NeurIPS 2025 已证可行)+域判据验证门——软件工程判读/具身标注/各垂直域,每个域=判例集+小模型+验证证书三件套。
- **为什么是我们**:蒸馏的教师信号与质量门都是我们独有(判分器+判据冻结);数据飞轮(v5 轨迹/flywheel 具身)天然产判例。
- **实验设计(E-NACRE-4)**:具身域首发——VL-3B 底座+flywheel 标注判例(vdd4 已有栈),照 nacre-embodied-v1 命名入册;判据=flywheel 四验门预注册。
