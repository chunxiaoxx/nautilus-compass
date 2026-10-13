---
name: orgfuel-ORGG-ab0cfe0b22e08626-de63ab82e3
description: "判读档判例 VB_RUN_PREREGISTER_20260927 · 执行坐标(条件式深夜窗,约 15-25 分钟) "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ab0cfe0b22e08626
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 VB_RUN_PREREGISTER_20260927 · 执行坐标(条件式深夜窗,约 15-25 分钟)
## 执行坐标(条件式深夜窗,约 15-25 分钟)

1. bench clone:`Wayfound-AI/mini-vending-bench` @`058eb6d` →
   `runtime/vb_bench_20260927/mini-vending-bench`(干净 clone,非复用)
2. bench 侧 patch:`git apply C:/Users/chunx/nautilus-v5/docs/vb_bench_side.patch`
   (87 行:getAgentModel 显式 ChatCompletions+BENCH_CONFIG loader+supplier 隔离;
   物理验证 9/27 01:04 存在 3757B ✓)
3. 依赖:`npm install`(node ≥24 已在机)
4. v5 侧 API:`cd C:/Users/chunx/nautilus-v5 && python _run_v5_api_18001.py`
   (前置:仓 HEAD 必含 **899f2d1**(tool_calls 非空时 content=None——
   @openai/agents JS SDK 规矩,MiniMax planning 文本同填两字段=工具被丢,
   v5 昨夜 30 日零工具根因);当前 HEAD c309d73 已含 ✓;SelectorEventLoop 已处理)
5. 跑法五步:见 `C:/Users/chunx/nautilus-v5/docs/VB_ONBOARDING_PACK_20260926.md`
6. 产物:final_score.json + run_outpu
