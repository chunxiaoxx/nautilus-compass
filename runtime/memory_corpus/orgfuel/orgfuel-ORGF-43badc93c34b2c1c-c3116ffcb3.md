---
name: orgfuel-ORGF-43badc93c34b2c1c-c3116ffcb3
description: "flywheel 档案 2026-08-28-egosuite-sample-verification.md # Ego"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-43badc93c34b2c1c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-08-28-egosuite-sample-verification.md
# EgoSuite-Open100K 样本验证报告（G6.3 · 2026-08-28）

## 访问状态

- **EgoStandard（90kh）/ EgoPro（10kh）：gated 已批准**（2026-08-28 用户收到接受通知；实测 repo 树仅 README，数据经 HF Bucket 分发，文件级访问 404=已放行）
- EgoDemo（50h 免门样本）：仍 awaiting（数据文件 403）
- Bucket 结构：`hf://buckets/LightwheelAI/EgoStandard`（EgoStandard/mcap 80kh 头视 + EgoStandard-body/mcap 10kh）与 `hf://buckets/LightwheelAI/EgoPro`（EgoProStandard-body/mcap，单集 0.5-1.2GB）；共 322,882 文件，任务名自然语言（"Add Syrup to Coffee" 等）；**目前仅 mcap 表示，LeRobot 版未放出**

## 样本实测（46.9MB 单集，C:/Users/chunx/egodata/sample/sample_episode.mcap）

- Bucket 下载链路通：`HfApi.download_bucket_files(bucket_id, files=[(远端, 本地)])`，字节数与清单一致
- MCAP 解析通（mcap+mcap-ros2-support，protobuf 编码，foxglove schema）：
  - 12,472 messages / 34.6s episode / ~30Hz 姿态帧 ×1039
 
