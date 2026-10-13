---
name: orgfuel-ORGH-e91eab4f4d33ee2a-9b959702bf
description: "工具决策记录 judge_hotpath_cpu_timer.py #9 判分器热路径 · CPU 推理一例计时(202"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e91eab4f4d33ee2a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 judge_hotpath_cpu_timer.py
#9 判分器热路径 · CPU 推理一例计时(2026-10-02)。

对照口径:JUDGE_HOTPATH_INTEGRATION_PLAN S2(ingest P95 增量 <100ms 线);
GPU 读数已有(R4:A100 P50=30.1ms/P95=42.2ms),本件测 CPU 是否可行。
prompt 组装与 tools/train_judge_lora.py 逐字同款(无作弊通道版)。

运行位置:A100 同机 CPU(G1 只占 GPU;torch 限 8 线程=判分器独立进程部署口径,不抢训练)。
用法:python3 judge_hotpath_cpu_timer.py <anchor_v0.jsonl> [model_path]
输出:stdout 读数 + hotpath_cpu_report.json
