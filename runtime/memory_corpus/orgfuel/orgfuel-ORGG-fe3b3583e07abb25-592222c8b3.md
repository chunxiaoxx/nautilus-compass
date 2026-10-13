---
name: orgfuel-ORGG-fe3b3583e07abb25-592222c8b3
description: "判读档判例 NACRE_NATIVIZATION_ROADMAP_V0_20261007 · 五、推理时域适配:"判分器"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fe3b3583e07abb25
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 NACRE_NATIVIZATION_ROADMAP_V0_20261007 · 五、推理时域适配:"判分器 TTT"(测试时训练,新技术引入)
## 五、推理时域适配:"判分器 TTT"(测试时训练,新技术引入)

- **创新机制**:新域/新基准冷启动(无足量判例时),不做全量重训,做 **TTT 式小幅适配**(该域少量判例即时微调,判据 sha 锁定,用完即弃或验证后入 registry)。
- **学界依据**:TTT for Long-Context(OpenReview 2026)证明小量上下文特定训练优于推理时搜索——迁移到判分域适配。
- **实验设计(E-NACRE-5)**:caliber-bench 首个外部域单(如 L1 收录的某 harness 域)冷启动,TTT 适配 vs 零适配对照。
