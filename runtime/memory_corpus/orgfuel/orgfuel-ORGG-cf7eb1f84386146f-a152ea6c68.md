---
name: orgfuel-ORGG-cf7eb1f84386146f-a152ea6c68
description: "判读档判例 JUDGE_UPGRADE_7B_FIRSTRUN_20261004 · 一 · 执行读数 [实测] ## "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-cf7eb1f84386146f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_UPGRADE_7B_FIRSTRUN_20261004 · 一 · 执行读数 [实测]
## 一 · 执行读数 [实测]

- 脚本:`tools/e1_main_j2_batch_judge_7b.py`(v4 定版仅三处改:模型路径/输出文件名/judge 署名,判据零改动)
- 模型:Qwen2.5-VL-7B-Instruct bf16(实例 /root/sysmodels/),环境 /root/venv(transformers 4.57.6)
- 跑动:498 题 283s(~0.6s/题,快于 3B 4bit 版 2.4s/题),显存峰值 16.4G(与预备档预估 16G 一致),timeout=0,断点续跑无触发
- 材料 sha16:CSV `c0a6bc1cbfd9d10a` / jsonl `8be5af8f27177a6d` / log `86b183201d4e21a8`(本地 `runtime/e1_judge_pack/upgrade_7b/`)
- csv/jsonl 对齐零不一致(本地独立复算)
