---
name: orgfuel-ORGQ-R52-a1fdb15062
description: "### R52 · 2026-10-03 07:2x-07:4x(turbo 深挖定谳+G 臂 rollout 实证) "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R52
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R52 · 2026-10-03 07:2x-07:4x(turbo 深挖定谳+G 臂 rollout 实证)
- **turbo ImportError 根因定谳**:transformers 5.10 fp8 集成层 import 期读 `torch.float8_e8m0fnu`(torch≥2.9 才有),系统 torch 2.6 缺该属性——torch 老撞 transformers 新;修=提取脚本头一行 patch(缺则用 e4m3fn 顶名,bf16 路径不触发 fp8),已上传
- 提取被守门正确拦截(GPU 有进程)——**该进程=g1_infer_compare.py 跑 G 臂 rollout**(G_run1/1999+G 批,07:2x 起跑):评测侧已开工,协调问被事实回答,turbo 提取排队等空窗
- SSH 限流两连拒(banner 10054/EOF,整夜高频连接触发)——退避 120s+单连接做完模式有效,记入配方
- M1:+(F3 通道修复待空窗;判分输入链路实证在跑)
