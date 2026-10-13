---
name: orgfuel-ORGG-9bc4dd8d29713fb4-4ad2a1ba2e
description: "判读档判例 JUDGE_RETRAIN_RUNBOOK_20261001 · 三 · A100 40G 现成环境(202"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-9bc4dd8d29713fb4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_RETRAIN_RUNBOOK_20261001 · 三 · A100 40G 现成环境(2026-10-01 实测)
## 三 · A100 40G 现成环境(2026-10-01 实测)

- 连接:`.cache/gpu_a100.env`(双线 223.109.239.30/180.127.11.167:23236,root)
- 全套就位:torch 2.6.0+cu126 / transformers 4.57.6 / peft 0.13.2 / bnb 0.50.2 / modelscope
- 我们部署件(sha256 三折已验与本地一致):
  - /root/runtime/verdict_corpus/split_{train,dev,test}.jsonl(1162/143/149)
  - /root/tools/train_judge_lora.py(MODEL_ID 现指 modelscope 本地路径,重训前改回或重下)
  - /root/runtime/judge_lora/(上一轮产物)
- 模型缓存:Qwen3-1.7B 在 /root/.cache/modelscope(HF 直连/hf-mirror 大文件断流,一律走 modelscope)
