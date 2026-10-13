---
name: orgfuel-ORGH-c7a861154d7528e6-d49dab845a
description: "工具决策记录 embed_server_v2.py embed_server v2(FastAPI/uvicorn 栈 "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c7a861154d7528e6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 embed_server_v2.py
embed_server v2(FastAPI/uvicorn 栈 · 8400)——替换 R303 简易 http.server
(经 ssh 隧道链路 reset 的协议坑)。协议不变:POST /embed {"texts":[...]} →
{"embeddings":[[...]]};GET /health。bge-m3 fp16 cuda,归一化输出。
