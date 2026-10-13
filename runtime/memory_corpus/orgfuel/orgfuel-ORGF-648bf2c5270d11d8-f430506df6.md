---
name: orgfuel-ORGF-648bf2c5270d11d8-f430506df6
description: "flywheel 档案 2026-09-03-egodemo-format-demo-pack.md # 格式演示样例包"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-648bf2c5270d11d8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-09-03-egodemo-format-demo-pack.md
# 格式演示样例包 demo_pack_001 · MANIFEST 归档

> 2026-09-03 · 生成于 GPU 服务器（EgoDemo gated 已批准），视频不入仓，本文件为包清单归档。

```json
{
  "pack": "demo_pack_001",
  "nature": "格式演示样例：向客户展示交付格式（LeRobot v3.0 结构+caption+frames_info）与标注深度。数据来自开源集，实采交付数据将另行提供。",
  "spec_checklist": [
    {
      "item": "交付格式 LeRobot v3.0",
      "status": "PASS",
      "note": "EgoDemo 原生 LeRobot v3.0（data parquet+videos+meta）"
    },
    {
      "item": "单目（非鱼眼）",
      "status": "DEMO",
      "note": "取双目头视角之左目；光学畸变待实采样例标定核实"
    },
    {
      "item": "视频规格",
      "status": "DEMO",
      "note": "1920x1456@30fps（像素量超 1080p 级）；开源 demo 片段"
    },
    {
      "item": "caption 200 字 + frames_info",
      "status": "PASS",
      "note": "由官方语义标注生成；实采将由采集元数据+AI 标注复核生成"
    },
    {
  
