---
name: orgfuel-ORGM-letta-wrong-repo-lesson--e9ce639c45
description: "--- name: letta-wrong-repo-lesson-20261004 description: "Let"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGM-letta-wrong-repo-lesson-
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

---
name: letta-wrong-repo-lesson-20261004
description: "Letta #3450 发错仓考古——主仓已变 landing page 禁 eval 类 issue,正确归属 letta-evals;发外联 issue 前必查目标仓 AGENTS.md"
metadata: 
  node_type: memory
  type: project
  originSessionId: c62a754e-c031-437d-a37a-0d217fbf3144
  modified: 2026-10-04T05:56:28.388Z
fact_status: inferred
---

10/4 Letta 重提交考古:原 #3450 被 github-actions[bot] 七项校验自动关是表象,**根因=发错仓**。letta-ai/letta 主仓已变为 intentionally small landing page(AGENTS.md 明文:benchmarks/evaluations/experiments/academic research 类 issue 属禁止用途,现役代码在 letta-ai/letta-code,评测框架在 letta-ai/letta-evals)。

**Why:** star 数/包名/仓名直觉≠现役归属;守门机器人只报"模板缺项"不报"发错仓",按表面信息补模板=永远过不了。

**How to apply:** 外联开 issue 前三查:①目标仓 AGENTS.md/README 定归属;②.github/workflows 有无 issue-guard 类机器人(校验逻辑直接读 yml 拿精确短语);③维护者活跃度(最近 issues 处理)。letta-evals#340
