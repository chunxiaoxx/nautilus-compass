---
name: orgfuel-ORGG-26c9ea96b71ea1d9-2909bf97be
description: "判读档判例 JUDGE_RETRAIN_RUNBOOK_20261001 · 四 · 与 v5/飞轮共用纪律(🔴 必读)"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-26c9ea96b71ea1d9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_RETRAIN_RUNBOOK_20261001 · 四 · 与 v5/飞轮共用纪律(🔴 必读)
## 四 · 与 v5/飞轮共用纪律(🔴 必读)

- **这台机 = v5 框 E6 训练机**(/root/vdd+vdd2:ego_open100k_t1 15G/nanjev_ckpt 14G/
  e6 18G/agibot/genrobot 数据),E6 GRPO 训练在跑时**绝不抢 GPU**
- (GOALS W1:E5 达 30 条即首批 POST 1562,E6 训练是 v5 施工图主线)
- 我们的判分器训练 <1h/<¥2,窗口=E6 空档;开跑前必查 `nvidia-smi` 显存占用 <10%
- 训练脚本无需改超参(判据零放宽);40G 富余显存留给 E6 共存,不升 batch
