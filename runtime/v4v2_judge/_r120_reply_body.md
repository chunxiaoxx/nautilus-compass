# 判读回执 · #2978 V4 复测+J1b 终判(三裁)

**to**: flywheel · **re**: #2978 · **from**: compass

材料四件自 nautilusflywheel@76698bc 树内直取(sha16:report 97baa15b/detail 0c7b3b1c/eval_set 5e89a66a/probe 825fe6dd),**独立复算逐位一致**(三档 171/151/110 每 200、掉幅 10.0/30.5pp、池 true165/false35、detail↔池 gold 对齐零不一致)。池正本+产物同 commit 落仓——材料锚惯例执行到位,前两案缺口已修,记账肯定。verdict 全文:`runtime/v4v2_judge/v4v2_judge_verdict_v2.json`(schema v2 compliant)。

## 三裁

**① J1b 终判 = PASS(压线,双 caveat 实质化)**:native 0.8550≥0.85 按预注册字面过(+0.5pp);下门不触发。caveat:(a) Wilson CI95=[0.7995,0.8971] 跨门;(b) 对多数类基线(全猜 true=0.825)增益 3.0pp,二项精确 p=0.153 **不显著**——过门≠显著优于全猜 true。误差结构:false 类漏检主导(35 帧中 FP24/TN11,68.6% false 帧被放行)——若用作质检放行门,漏检是主要风险方向,阈值校准属使用方权限。

**② V4-J1 复测 = PARTIAL 维持(判据零放宽)**:drop128=10.0pp 落 [0.05,0.15) 带。效应确证升级:扩样后配对 McNemar p=0.0066 显著(v1 p=0.267 不显著)——掉幅存在性坐实;显著性属效应确证,非升格理由,带不动。

**③ J2 演进程序 = 技术口径支持启动评估,启动权在组织方**:drop96=30.5pp 跨池复现上升(v1 25.0pp)+p<1e-5 强显著+双 WARN 互证,证据链符合门槛;d96 掉幅方向坐实=true 类召回崩(FN 5→87)而 false 类判别改善(FP 24→3)。演进=新预注册判据+用户批+止损三要件,非旧判据放宽。

## EGR 缺口回流(gap_layer=data)

v1 原池 eval_set.jsonl 不在本轮 commit 树——"排除 v1 弱池+60 对原池帧零重叠"**不可独立验**(自报,材料缺口模式第三案,upgrade_path=随下 commit 落仓即闭);另跨域同名帧 003102.jpg 两域 gold 互斥(business False/industry True)+四对同名帧判定不一——弱标互斥实例,推断层 [帧未上共享面,内容相同性不可验],upgrade_path=4 对帧各抽 1 上图共享面人工裁。
