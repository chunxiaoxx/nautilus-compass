---
name: orgfuel-ORGQ-R144-cc8f26494e
description: "### R144 · 2026-10-04 23:1x-23:4x(用户拍:14B 判读器 smoke 立项+G1 值守"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R144
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R144 · 2026-10-04 23:1x-23:4x(用户拍:14B 判读器 smoke 立项+G1 值守读数)
- **smoke 立项**(用户拍):预注册判据档落 docs/metering/PREFOR_JUDGE14B_SMOKE_20261004.md(S1-S5 五门:训练完成/显存<36G/收敛/格式 20/20/读数申报;升格决策不在 smoke 判据内;A100 空窗执行,B 臂在跑即顺延)
- **G1 值守**:10/3 修复版 G/B 对核对判分史——R54(G 修复批)/R57(双臂差分终判 ΔJ1=+2.5pp)/R59(B2)均已判,**无未判材料**;今晚 relay g1_relay_b.log:G_EXITED 23:15:53+B_LAUNCHED 23:16:23 ckpt=1999,B 臂在等 gr00t CanSort 数据集下载(22:34 起,6.4G),材料未出不触发
- **turbo 下载复活**:前轮 STILL_DEAD 为 pgrep 时序误判——实测 PID 2002106 在跑,du 1.1G→2.4G 增长中(~1.75MB/s);启动脚本法留档 /root/dl_turbo_start.sh
- **#3102 服务页上站**:平台复验 sha16 一致,挂试金局卡;平台建议入册 sinks 第四件→**compass 拍:入**(回函 3105,owner+30 天续验义务);ack 清
- 下轮:④turbo 下载巡检(B 臂下载也在抢带宽,顺延预期);B 臂 rollout 材料出→触发判分;smoke 等 A100 空窗
