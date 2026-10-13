---
name: orgfuel-ORGM-f170e538d44bb29b-691bdef092
description: "记忆条目 lmev2-judge-401-envvar-pitfall.md --- name: lmev2-judge"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-f170e538d44bb29b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 lmev2-judge-401-envvar-pitfall.md
---
name: lmev2-judge-401-envvar-pitfall
description: LME-V2 judge 401 根因=启动时 source .ark_env(ARK_API_KEY)而非 judge.env(OPENAI_API_KEY)——harness 默认读 OPENAI_API_KEY;生成不受影响可 rejudge 补救
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  fact_status: measured
---

2026-09-04 cheap-tier web full run(654686)判分阶段全 401 "API key format is incorrect"。

**根因**:上游 harness 的 `--evaluator-api-key-env` 默认 `OPENAI_API_KEY`(evaluation/harness.py:221)。昨晚启动命令用了 `source /root/.ark_env`(只导出 `ARK_API_KEY`)→ judge 客户端拿空 key → 401。9/3 d12 成功是因为用了 HANDOFF 命令 `export $(cat /root/e2e/judge.env | xargs)`(judge.env 里变量名正是 `OPENAI_API_KEY`)。三个 env 文件(/root/.ark_env /root/e2e/judge.env /root/e2e/ark.env)是同一把 key(b8ed...),key 本身没
