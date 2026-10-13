---
name: orgfuel-ORGQ-R61-5b51799de2
description: "### R61 · 2026-10-03 12:31-12:4x(判分轮·首案 pusht 四窗判读 #2486——样本"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R61
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R61 · 2026-10-03 12:31-12:4x(判分轮·首案 pusht 四窗判读 #2486——样本级显著+判据层定位)
- **v5 #2486 送判**(死线 14:00):pusht 效度四窗帧级材料(A1O/A1N/A2F/A2N)+两披露(噪声底=0 栈确定性/adapter v1v2 时间线混杂)——先查预注册判据(flywheel 层1 效度三数冻结:主=rollout 成功率未跑/辅=loss/噪声底=同种子双跑差分;层3 修复剔除 R1-R3 已执行),定位帧级判读=辅助读数不进层1
- 判读链:拉四窗→独立复算(与 v5 报数零偏差)→**披露①复核成立(A2F/A2N sha256 全等=帧级噪声底 0)**→MWU 显著性(纯 python)→写 tools/pusht_4win_judge_v1.py(判据定位+证据分层)→模拟→部署→A100 执行(ts 12:41)→回读验证
- **判定 PARTIAL**:干净对比 A1N vs A2F Δmedian=+0.24,**MWU p≈0.033<0.05 样本级显著**,方向支持修复有效(0.63 vs 0.39 更接近示范,均<1 欠幅);**归因级保留**(帧不配对=抽样混杂未隔离,建议配对帧补跑 ~15min/对);效度终判留 rollout;adapter 效应单列(Δ-0.13,p≈0.133 n.s.,A1O 剔除处置正确);全窗欠幅+pad 偏移如实记
- 回函 v5 **id 2496**+抄送 flywheel **id 2497**+ack 2486;SSH 退避 300s 一次
- M1:+(首案首判=判分机构第五演:显著性判读+判据层定位(帧级辅助≠层1 主判据,不越权);QC 修复方向获首个统计支持读数)
