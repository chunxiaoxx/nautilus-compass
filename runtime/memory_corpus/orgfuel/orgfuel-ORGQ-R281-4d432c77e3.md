---
name: orgfuel-ORGQ-R281-4d432c77e3
description: "### R281 · 2026-10-07 早(loop v2 R5:int8 崩修复+脚本 v2 重发) - **in"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R281
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R281 · 2026-10-07 早(loop v2 R5:int8 崩修复+脚本 v2 重发)
- **int8 轨崩根因**:peft 0.13.2×bnb 0.50.2 版本代差(dispatch_bnb_8bit 访问已移除的 memory_efficient_backward)——与 compat 记忆"peft×transformers 坑"同族;且 v1 设计最后才写 CSV,崩=丢 bf16/fp16 全部数据(教训:长实验必须边跑边写)。
- **脚本 v2**:merge 后量化绕法(LoRA merge_and_unload→save→纯 CausalLM 量化加载,完全绕开 peft×bnb hook;统一 merged 权重=各精度公平)+per-config try 容错+边跑边写 matrix.csv。已重发车[实测]:merge 落盘✓、进程 3821367 在跑、bf16 双轨过、fp16 进行中——全轨约 15-20min,收数下轮判门。
