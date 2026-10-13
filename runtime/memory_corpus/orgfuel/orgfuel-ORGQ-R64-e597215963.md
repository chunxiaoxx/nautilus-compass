---
name: orgfuel-ORGQ-R64-e597215963
description: "### R64 · 2026-10-03 14:01(值守轮·rollout 主判据实验在跑,终判触发件定义) - **"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R64
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R64 · 2026-10-03 14:01(值守轮·rollout 主判据实验在跑,终判触发件定义)
- **v5 接函即跑 rollout**(13:32/13:34 两批,GPU 78%,pusht_rollout_eval.py full 27min+):全量批 133459=A1N/A1O 各 20 集完成、**A2F 13/20 在跑**;smoke 批 133210=A2F 2 集
- 已落盘读数 [实测]:A1N 20 集 **成功率 0/20**,mean_final_coverage 0.0861;A1O 0/20,coverage 0.0531;smoke A2F 2 集 0 成功但 **coverage 0.4664(A1N 的 5.4 倍)**。成功阈值 coverage>0.95——**主判据成功率恐全员零成功(地板效应),覆盖率或成唯一区分信号;判据零放宽:成功率判不动就如实报,不中途改义**
- env_fingerprint 设计合格入档:同 seed 序列跨窗配对(初始布局一致,差异只来自 ckpt)、success_def=terminated & info[is_success]、判读坐标注(A1N vs A2F=修复效应;A1O v1 协议混杂不进主判;噪声底=同臂双跑 |orig−noise|)——与我方判据定位一致
- **终判触发件(下轮)**:pusht_rollout_20261003_133459 全部 summary 落盘(A2F±A2N 完成)→按层1 冻结判据判:成功率差分(主,若地板则如实报)+coverage 差分(辅助,标注非冻结语义)+噪声底同臂双跑核验+ckpt_sha16 锚定
- 信箱 0 未读;G1 双锚未变(eab63d7f/340eff11);GitHub 通知同前噪声
