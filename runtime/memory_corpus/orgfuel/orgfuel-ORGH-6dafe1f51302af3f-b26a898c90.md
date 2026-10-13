---
name: orgfuel-ORGH-6dafe1f51302af3f-b26a898c90
description: "工具决策记录 nacre_judge_server.py NACRE v1 判分服务(T5.1 · OpenAI 风格薄"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6dafe1f51302af3f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 nacre_judge_server.py
NACRE v1 判分服务(T5.1 · OpenAI 风格薄壳 · port 19988 · A100)。

模型:Qwen3-1.7B + adapter(best_lora, sha16=dbcbab6f 与 HF 卡逐位一致)
POST /judge {"criteria":..., "artifact":...} → {"verdict": pass|fail|insufficient_evidence, "raw":...}
GET  /health → {"ok":true,...}
判据纪律:只推理不判读(标签即模型输出原文),置信/后处理归调用方。
