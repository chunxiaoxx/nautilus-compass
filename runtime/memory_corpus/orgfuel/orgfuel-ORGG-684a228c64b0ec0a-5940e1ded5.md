---
name: orgfuel-ORGG-684a228c64b0ec0a-5940e1ded5
description: "判读档判例 CASEBOOK_V1_20261005 · 案 1 · G1 pusht 双臂差分终判(具身数据 A/B)"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-684a228c64b0ec0a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 CASEBOOK_V1_20261005 · 案 1 · G1 pusht 双臂差分终判(具身数据 A/B)
## 案 1 · G1 pusht 双臂差分终判(具身数据 A/B)

| 项 | 值 |
|---|---|
| 被测物 | flywheel 双臂 rollout 数据(A=基线臂,B=注入臂,pusht 任务,100 集) |
| 判据 | pusht-frame-v2 v2-final(sha16=fcb793e274a7bdbc):J1 方向一致率/J2 幅度比 [0.3,3.0]/J3 sha 锚定工件;配对 Wilcoxon 辅 MWU;noise_floor=A2F−A2N |
| 读数 | [实测] ΔJ1=+2.5pp,ΔJ2=0;[实测] 样本级配对 Wilcoxon p=0.00986;[推断] 注入未传导至下游 rollout,数据层特征增强成立、任务层增益不显著(混杂大半坐实) |
| 判据张力 | 首演 U 态(收件不完整)→三修补件→终判;rollout 主判据 coverage p≈0.48 不显著=负结果照报;verdict 条件三条回档主 |
| 复算坐标 | g1_protocol_v1.json+pusht_pair_verdict.json(A100 /root/vdd3/pipe_art/);非实现者复算=compass 新鲜会话 |
| 判例价值 | 「注入攻击是否传导」类的标准判法:数据层/任务层分层判定+配对归因,不并成一个分数 |
