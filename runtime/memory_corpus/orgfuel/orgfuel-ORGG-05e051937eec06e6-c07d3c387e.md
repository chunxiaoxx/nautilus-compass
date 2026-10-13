---
name: orgfuel-ORGG-05e051937eec06e6-c07d3c387e
description: "判读档判例 P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003 · 四 · S3 训练"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-05e051937eec06e6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003 · 四 · S3 训练执行(唯一 GPU 段)
## 四 · S3 训练执行(唯一 GPU 段)

- 触发:训练单 commit 后由人批准执行(不自动租机);租 4090(1.65/h),API 层租/释(承 _redact 遮罩坑:release 走 broker API 原子调用)。
- 守门:脚本首行 assert CUDA 可用,否则退出码 42(不静默 CPU 跑)。
- 下载纪律:模型走 modelscope 通道(HF 大文件断流定谳);transformers≥4.57(Qwen3 兼容定谳)。
- 产物拉回:challenger adapter + train log + 机内完成的 S4 评估原始输出(见下)。
