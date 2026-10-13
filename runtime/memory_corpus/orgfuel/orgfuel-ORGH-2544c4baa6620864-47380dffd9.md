---
name: orgfuel-ORGH-2544c4baa6620864-47380dffd9
description: "工具决策记录 pusht_4win_judge_v1.py pusht 首案四窗判读 v1(2026-10-03 · c"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2544c4baa6620864
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 pusht_4win_judge_v1.py
pusht 首案四窗判读 v1(2026-10-03 · compass 独立判,材料=/root/vdd3/pipe_art/pusht_infer_{A1O,A1N,A2F,A2N}/)。

判据定位(层1 冻结件,flywheel 立项正本 §首案):效度三数=Calibra 原分/修复后分/π0 训练差>噪声底,
训练侧主判据=rollout 成功率(未跑)——本判读=帧级辅助读数,不进层1判据本体,效度终判留 rollout。
层3 修复剔除三判据(R1 jerk_P99/R2 velocity_disc/R3 freeze_ratio)=数据侧去留,REPAIR_MANIFEST 已执行,不在本判读范围。

口径(v5 #2486 送判,G1 三修同):dir=sign 语义 dot(pred−state,act−state)>0 帧率;
ratio=‖pred−state‖/‖act−state‖;参考带 [0.3,3.0];frame_filter ‖act−state‖≥1e-3。
显著性=MWU 双尾(纯 python 正态近似,40 vs 40);噪声底=A2F/A2N 字节一致核验(v5 披露①复核)。
混杂:v5 披露②=A1O(adapter v1,08:38 发车)vs A1N(v2,10:14 发车)=代码变更效应,不进数据效应判读,单列。
幂等:同材料重跑同读数。用法:python3 pusht_4win_judge_v1.py → /root/vdd3/pipe_art/pusht_4win_verdict.json
