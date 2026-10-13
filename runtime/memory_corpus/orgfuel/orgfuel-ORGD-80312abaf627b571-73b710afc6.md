---
name: orgfuel-ORGD-80312abaf627b571-73b710afc6
description: "[## 案 5 · pusht rollout n=20 初判案（PARTIAL-U）] - **背景**：层 1 主判"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-80312abaf627b571
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 案 5 · pusht rollout n=20 初判案（PARTIAL-U）] - **背景**：层 1 主判据首判（冻结语义：成功率=coverage>0.95/300 步）。
- **判据**：v1 冻结语义；判据零放宽三不（不改阈值/不延长步数/不以代理顶替）。
- **材料锚**：四窗 ckpt_sha16（A1O=`b9b23d51d273aea4` / A1N=`1968c1c003880bb8` / A2F=`70bfbff386c8ea5c` / A2N=`629583967b49e1bb`），n=20/窗同 seed 配对，env_fingerprint 设计合格。
- **判读**：成功率四窗全 0/20——地板效应差分判不动（0 vs 0），U 态；辅助 coverage 均值 A2F×2.02 vs A1N 但 MWU p≈0.48 不显著（n=20 方差大，均值差由少数高覆盖集驱动）；噪声底=逐集 0.0。
- **claims**：[实测] 地板判不动照报；[实测] coverage 不显著如实报（不为叙事挑读数）；[实测] 噪声底=0。
- **边界**：PARTIAL-U 出件即触发终判条件决策（三条：协议修订/coverage 入判据/扩集数——主定夺选扩集数，即案 6；前两条冻结语义不动）。
- **复算**：`_r65_deploy_rollout_judge.py`；判读函 `runtime/loop/_r65_mail_rollout_verdict.md`。
