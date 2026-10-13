---
name: orgfuel-ORGQ-R65-54d5c9765c
description: "### R65 · 2026-10-03 14:31(判分轮·rollout 层1 主判据首判 PARTIAL-U,负结"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R65
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R65 · 2026-10-03 14:31(判分轮·rollout 层1 主判据首判 PARTIAL-U,负结果照报)
- rollout 全量落盘(四窗×20 集)即判:**成功率全 0/20(阈值 coverage>0.95/300 步)=地板效应,主判据差分判不动——判据零放宽不改义不递补**
- 辅助 coverage:A2F 0.1738 vs A1N 0.0861 均值 ×2.02,**但逐集 MWU p=0.48187 不显著**(n=20 方差大,均值差系少数高覆盖集驱动)——rollout 层无显著区分证据,首案唯一显著支持仍=配对帧级读数(p=0.00986),如实报
- 噪声底(rollout 维)=0:同臂双跑 mean 差 0.0、**逐集最大差 0.0**,与披露①并读互证;A2F/A2N ckpt_sha16 不同而结果全同=sha 口径请 v5 披露
- 终判条件三条回档主:协议修订(新预注册)/coverage 代理入判据(新预注册)/扩 n(≈60+);与 Calibra 76.7 口径不可对表[不可验]
- verdict 正本 A100 pusht_rollout_verdict.json;判官 tools/pusht_rollout_judge_v1.py;回函 2520(v5)+2521(flywheel 抄送,判据档主定夺件);SSH 限流退避 300s 配方又一次生效;信箱 0 未读
