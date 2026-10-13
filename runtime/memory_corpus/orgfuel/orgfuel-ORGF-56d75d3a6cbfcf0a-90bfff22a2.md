---
name: orgfuel-ORGF-56d75d3a6cbfcf0a-90bfff22a2
description: "flywheel 档案 loop_night_R161_20261008.md # LOOP 值守轮 R161 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-56d75d3a6cbfcf0a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R161_20261008.md
# LOOP 值守轮 R161 留痕 2026-10-08 16:4x(W2 语料预产起步轮)

> 用户令"继续 LOOP 自动推进(W2 语料预产)"。池盘点+gold b3 双落地。

## 本轮动作
1. **池判读覆盖盘点**(nautilus-db 直查):fuel_trajectories 165 行,全 label_origin=verifier(flywheel 通道);**完整五门 gates 137/165**;28 行无 G1 系 10/4 首批旧格式存量(判读格式演化前,verdict pass18/fail10 在)——非新缺口,补全边际小,不动(如实记录)。W2 SFT 1465 样本 v5 侧已独立核,RL 池 152/82=v5 排产——池侧供给无缺口。
2. **gold 扩样 b3 批抽帧落地**(W2 后 LoRA 重启条件 gold 100+ 的供给侧):
   - 选集=qc17_report 冻结率最低 5 集(13483=0/10699=11.1%/14950=16.1%/13013=24.2%/14714=26.9%)——**QC 读数反哺 gold 选集**(病集不进基准)。
   - runtime/_goldset_a3_sample_b3.py(robotwin_unified cam_high,时间窗=ep_video_map,INSET 0.3s,tasks 取 parquet);实例跑 5/5 集×8 帧=40 帧落 runtime/goldset_a3_b3(+manifest 含 task/frame_ts_rel/freeze 字段位)。
   - 资产复用:零新下载(QC17 已取件)。
3. 新坑:MSYS 路径转换炸 s
