---
name: orgfuel-ORGD-a97968a4cec41f28-1cc3e742cd
description: "[## 3. 起 daemon(GPU + reranker)] - `setsid + </dev/null`:必须。"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-a97968a4cec41f28
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 3. 起 daemon(GPU + reranker)] - `setsid + </dev/null`:必须。普通 `nohup ... &` 后跟长 for-loop 在同一 ssh 命令里会让 ssh 挂(实测 exit 255 + daemon 没活)。检查就绪要**另起一条 ssh** poll `ss -tln | grep 9876`。
- 实测:BGE 12.1s 载入 GPU → `listening 127.0.0.1:9876`。
