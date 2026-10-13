---
name: orgfuel-ORGH-6715bbe860c0afcc-4d54f77d61
description: "commit 2441386fc3f3 2026-08-22 feat(gate-b): v1 真燃料 spec + t"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6715bbe860c0afcc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2441386fc3f3 2026-08-22
feat(gate-b): v1 真燃料 spec + thinking-block 解析修复 · 双真燃料实测均 delta=0
- v1(freshness)spec:边界口径 headroom 设计(transfer 不泄露口径)· 语义 eval oracle · 10 测试
- fix(provider): anthropic 解析拼接全部 text block(glm-5.3 偶发 thinking-first 导致 provider_output_invalid)
- 实测:c2e 与 v1 双真燃料 control 均一次做对 → 通用工程常识对 glm-5.3 无 headroom
- 🔬 方向性结论:真燃料 Gold 须用项目特异经验(飞书单选 id 透传/Windows codepage 写入/
  部署怪癖)——这恰是 Verified Memory 产品的真实卖点:团队私有验证知识,非通用常识
