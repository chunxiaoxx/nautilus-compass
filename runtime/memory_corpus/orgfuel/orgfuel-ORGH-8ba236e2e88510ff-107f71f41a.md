---
name: orgfuel-ORGH-8ba236e2e88510ff-107f71f41a
description: "commit 106a035907c3 2026-07-17 fix(bmb): VCF 题埋进 3000 真实变异(做"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8ba236e2e88510ff
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 106a035907c3 2026-07-17
fix(bmb): VCF 题埋进 3000 真实变异(做实体量)+ 修 make_delivery rmtree bug
- 用户质疑 6KB 太小:VCF 题从 30 变异→**3001 真实变异**(本地 ClinVar 镜像拉 Benign/VUS 背景,
  致病埋其中)· 未压缩 99KB/题 = 真实 exome 子集体量;发送包 6KB→45KB
- 3000 变异逼模型用批量注释工具(brute-force 不可行)= 更贴买方'需真工作流';难度更强
- fetch_background_local:从本地 ClinVar SQLite 拉大量真实背景(瞬时/零限速/真数据)· --n-background 默认 3000
- 唯一性:本地 QC 全扫 3001 变异,致病命中=1(#1/#2 均);验证器 0 REJECT/0 WARN;发送包无内部泄露
- 🔴 修 make_delivery.py rmtree 整个 _DELIVERY 的 bug(误删 NOTES/网页)→ 只清 data/*.zip 保留手写件
- DELIVERY_NOTES/网页/发送 zip 同步更新
