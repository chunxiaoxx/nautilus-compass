---
name: orgfuel-ORGM-820d4e7f921ae62a-6acdd23a17
description: "记忆条目 lmev2-pipeline-smoke-proven-20260830.md --- name: lmev2"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-820d4e7f921ae62a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 lmev2-pipeline-smoke-proven-20260830.md
---
name: lmev2-pipeline-smoke-proven-20260830
description: LME-V2 评测管线 GPU 机全链路打通(六坑定案)——BGE 线程竞态须单 worker/newapi 审查拦截题干换 ARK judge/32k context 硬要求;续租一键复跑命令在 TRANSFER_RUNBOOK
metadata: 
  node_type: memory
  type: project
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  fact_status: measured
---

# LME-V2 管线 smoke 全通(2026-08-30 · GPU 机 651799)

3 题烟测全绿:haystack 索引→memory 检索→reader 生成→judge 打分→aggregated_metrics.json 落盘。1.5B smoke 模型 0% 正确=预期(smoke 只验管线非分数)。正式 reader 全量 451 题待续租跑。

**三个复发级陷阱(跨 session 必读)**:
1. **BGE meta tensor 竞态**:torch 2.10+sentence-transformers 组合下,`SentenceTransformer` 构造在 ≥2 线程并发时 100% 报 `Cannot copy out of meta tensor`,主线程单发恒 OK。任何"多线程里懒加载 embedding 模型"的代码在此环境都要单线程化(`--prompt-workers 1`)。
2. **newapi 中转内容审查**:j
