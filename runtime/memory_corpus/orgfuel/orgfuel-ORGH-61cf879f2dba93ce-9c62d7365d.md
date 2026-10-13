---
name: orgfuel-ORGH-61cf879f2dba93ce-9c62d7365d
description: "commit a28738c86d3b 2026-08-22 feat(gate-b): d3 真燃料 Gold ×2 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-61cf879f2dba93ce
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit a28738c86d3b 2026-08-22
feat(gate-b): d3 真燃料 Gold ×2 · ③类部落事实靶点实证 + 判据门两处探针自误杀修复
- d3(飞书单选 payload · transfer 去提示化):同 d2 燃料,transfer prompt 只给可观察
  需求(最终名单),id 透传机制只存在于 source 经验——三级分类中③类的直接落地
- 实录:Gold ×2(r5/r15 · verify 重放 rc=0 · control 全败 10/10)→ 合约
  cnt_gold_replication_20260822 判据达成(3 Gold 其中 ≥2 真燃料)
- 探针自误杀修复(红灯先证伪自己 · 语义 oracle 4 案例不放宽):
  · ```json fence 剥壳(source/control 反复 provider_output_invalid 根因之一)
  · AST 安全子集放行 Starred/Set/Sub/BitOr/NamedExpr/Slice + max/min/len/
    any/all/next/range/zip/set(eval globals 同步);属性访问与 prompt 外内建仍拒
- 诚实记录:r4/r7/r8/r9/r10/r12/r13 treatment 多数语义正确但死于传输层;
  control 干净失败 0 次通过 = ③类 headroom 稳定的直接证据

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
C
