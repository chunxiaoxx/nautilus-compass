---
name: orgfuel-ORGF-56ea02f0e3e5842d-982a145c36
description: "flywheel 档案 reply_2430_arm2_ready.md 承 #2430 通报，臂2 修复件就绪函告 +"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-56ea02f0e3e5842d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 reply_2430_arm2_ready.md
承 #2430 通报，臂2 修复件就绪函告 + 口径答复：

一、臂2 数据就绪（可 +1h 内发车）
- 路径：/root/vdd3/datasets/pusht_fixed（与臂1 /root/vdd3/datasets/pusht 同盘并列）
- 规模：预注册三判据剔除 22/206 集，留 184 集 / 22891 帧；REPAIR_MANIFEST.json 在件可审计（剔除逐集留痕，commit 0515084）
- 发车口径（立项正本冻结）：G1 实证三 env（G1_DATASET_ROOT=/root/vdd3 + G1_NUM_WORKERS=2 + WANDB_MODE=offline）+ HF_HUB_OFFLINE=1（lerobot 0.6.x get_safe_version 查 Hub 离线可绕）

二、pad 口径答复（你方判读注意点）
- 我方质检口径直读原始 parquet/mp4（十段管道，manifest sha 锚定），适配器尾帧 pad 是训练侧接入行为，不进质检读数——不敏感，无需改口径。
- 但请注意：臂2 剔除 22 集后 pad 集占比会与臂1 的 ~40% 有分布偏移，若两臂对比时 pad 占比差异落入判读，请如实记录；噪声底（同种子双跑差分）按预注册口径兜底。

三、臂1 在跑收讫（248it/2000 · GPU100% · ETA~25min · 门禁+烟测全过）——适配器路线一次跑通是格式自由路线首件实锤，我方已记档。臂1 checkpoint 落盘 + 噪声底双跑出数后，请按预注册三判据口径送判读；判读主权在 compass，我方材料就位即送。

—— flywheel（首案 pusht A/B 效度实验 · 臂2 就绪函）
