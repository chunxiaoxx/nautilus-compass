---
name: orgfuel-ORGF-4c7db7e689a52a28-0df28c0e78
description: "flywheel 档案 loop_night_R149_20261008.md # LOOP 值守轮 R149 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-4c7db7e689a52a28
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R149_20261008.md
# LOOP 值守轮 R149 留痕 2026-10-08 08:2x(QC17 404 破译+正确清单重发轮)

> WEB-SYS 值守 cron 轮。中心环=QC17 首发车 404 群伤的根因破译与重发。

## 本轮动作
1. **例行**:信箱 0/外环双 CLEAN。
2. **QC17 首发车 404 群伤根因破译**:
   - 现象:57 件仅 3 件落盘,余 404(chunk-003/005/... 全不存在)。
   - 破译:该库 video 布局=**单 chunk**(cam_high 仅 chunk-000,file-000..202 共 203 箱,~135 集/箱);与 data 分箱(chunk=ep//1000,27 箱)完全无关。R148 用 data 分箱推 video 路径=错(唯一幸存件 file-005 是 ep567 恰好 chunk-000 的巧合)。
   - info.json "video_files_size_in_mb: 200"=单文件口径(~200MB/件),总量 135 件≈27G(vdd4 余 37G,放得下但挤,W2 前注意清理)。
   - **权威映射源=meta/episodes_chunk000.parquet**:per-cam chunk_index/file_index/from_timestamp/to_timestamp 四列俱全(帧抽取时间窗直接白送);本地 episodes.jsonl 是半残错误文本(勿信)。
3. **正确清单重发**:_qc17_ep_video_map.json(20 集×3 相机映射+时间窗)+_qc17_urls2.txt(45 对×3=135 件);aria2 PID 
