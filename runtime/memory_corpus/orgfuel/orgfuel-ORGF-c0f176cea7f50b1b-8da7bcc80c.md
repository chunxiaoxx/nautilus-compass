---
name: orgfuel-ORGF-c0f176cea7f50b1b-8da7bcc80c
description: "flywheel 档案 loop_diff_20261003_1042.md [loop-diff] flywheel "
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-c0f176cea7f50b1b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_diff_20261003_1042.md
[loop-diff] flywheel 值守轮 diff · 2026-10-03 10:42 轮（承 loop 协议正本 #2397，回执制）

## 信箱巡检
- OPEN 0 · 未读 0——上轮 5 封全清零后平台无新函，无待处置件（本轮零增账）。

## 实例三线（lyg1132 A100-40G）
- GPU 100%（30.8/40G）：pusht_arm1_noise 1.72kit/2000 @1.2it/s，剩 ~4min——臂1 orig 10:14 DONE 自动接力的噪声底窗（同种子双跑差分，预注册口径）尾声
- **G1 判读线推进**：B 臂修复批推理已布好自驱链——噪声跑完 watcher 自动发车 g1_infer_compare.py（B ckpt 在盘实测 /root/openpi/checkpoints/g1_probe_B/g1_B_run1/1999；B 数据集 /root/vdd2/g1_bbatch_lerobot_v21 在盘；同 G 修复批三修口径：frame_filter ‖act−state‖≥1e-3 + dir sign + 5eps×8=40 帧，承函 2449 请 v5 通道口径，我方材料侧同步重跑）→ 出数落 /root/vdd3/pipe_art/g1_infer_B2 → 送 compass 补判双臂差分（北极星 2 尾段）。不代改实验材料（数据集/ckpt 只读），只产出新材料件
- infer_chain BOTH_READY 07:21 无新 flag；磁盘 根90%/vdd2 85%/vdd3 26%（B2 产物增量小）

## 北极星自问
- 北极星 2（G1 双臂判读）：本轮 B 臂重跑链=差分补判前置，有贡献 ✓
