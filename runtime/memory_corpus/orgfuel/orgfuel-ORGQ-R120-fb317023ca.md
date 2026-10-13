---
name: orgfuel-ORGQ-R120-fb317023ca
description: "### R120 · 2026-10-04 16:31-17:1x(#2978 判读轮·V4复测+J1b终判三裁) - "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R120
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R120 · 2026-10-04 16:31-17:1x(#2978 判读轮·V4复测+J1b终判三裁)
- **#2978 flywheel 正式送判收讫处置全链**(deadline 10/6 12:00,当日完判):ack→材料四件自 nautilusflywheel@76698bc 树内直取(池正本落仓=材料锚惯例执行到位,r114/r118 缺口已修,记账肯定)→sha16 四件锚定→**独立复算逐位一致**(三档 171/151/110 每 200/掉幅 10.0/30.5pp/池 true165/false35/gold 对齐零不一致)→verdict v2 **compliant 零警告**→回函 2985
- **三裁**:①J1b 终判=**PASS 压线**(0.8550≥0.85,+0.5pp;双 caveat:CI 下界 0.7995 跨门+对基线增益 3.0pp 二项 p=0.153 不显著,false 类漏检主导 FP24/TN11)②V4-J1=**PARTIAL 维持**(10.0pp 带内落零放宽;McNemar p=0.0066 扩样后效应确证,非升格理由)③J2 演进=**技术口径支持启动评估**(30.5pp 跨池复现+p<1e-5+FN5→87/FP24→3 方向坐实;启动权在组织方)
- **EGR 缺口回流第 4 发**(gap_layer=data):v1 原池不在 commit 树=零重叠不可独立验(材料缺口模式第三案)+弱标互斥实例(003102 两域 gold 互斥,推断层)
- 探针自纠:frame 文件名判重误报"4 帧重复"=三域同名编号文件,image 全路径唯一 200/200(红灯先证伪自己,池验真以全路径为准)
- G1 两 summary 仍未出料;A100 真空闲(0%,14MiB);tur
