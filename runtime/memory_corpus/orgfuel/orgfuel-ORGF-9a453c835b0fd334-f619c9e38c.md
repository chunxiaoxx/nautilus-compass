---
name: orgfuel-ORGF-9a453c835b0fd334-f619c9e38c
description: "flywheel 档案 loop_night_R101_20261006.md # LOOP 值守轮 R101 留痕 2"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-9a453c835b0fd334
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 loop_night_R101_20261006.md
# LOOP 值守轮 R101 留痕 2026-10-06

## ①信箱:OPEN 1(#9941 四验 f171-f180)→即时办闭环
- REF 2cf3011,十单四验门 **10/10 PASS**;final_patch 10/10(连续第三批)
- 落库 inserted 10/skipped 0 实测(fail 2 照收);回执 SENT 9945+409 双确认+ack+done
- **燃料四验累计 64 单**(今夜 4 批 39 单全绿)

## ②实例与管道:EgoSuite/DROID 发车分岔
- **EgoSuite 撞 gated 仓**(mertalbaba/Robo-EgoSuite-VLA 需授权,16K 即停,非公开)——转 blocked-external:需 HF 页面申请访问(用户动作)或换非 gated 镜像;原脚本进程残活待清(下轮查实后杀,归属=我方)
- **DROID 单发车 DROID_ALIVE**(lerobot/droid_100 公共仓,meta 全量+数据清单序≤5GB,flag=_droid_dl_final.txt 自守望)
- 系统/vdd4 盘稳定(37G/48G)

## ③主力件:四验 SLA+发车处置(如上);BP v3 候批中/骨架 v0 落地后无新推面

## ④留痕:本件+loopdiff r101

## ⑤外部触达 0;**拍板新增第 6 项:EgoSuite gated 仓处置**(A.用户 HF 申请访问/B.换非 gated 数据源/C.暂缓 EgoSuite 只跑 DROID)

## 下轮:DROID 下载收件(_droid_dl_final.txt)→QC 计量链;egodroid 残进程
