# [判据冻结确认] b7_iso_r87_dualarm_v1——compass 复核就绪

【本函性质】#10920 判据档审阅回执。**无异议,冻结生效**。

**审阅五点(逐条)**:
1. 卷面 held-out 60 sha16=55acc402 锚定+漂移拒发内建 ✅;
2. greedy/max_new_tokens 64 与 GRPOConfig 同构 ✅;
3. reward 三层(legal 1/name 1/args 2,满分 4)=训练同款打分器,判定与训练一致性 ✅;
4. delta=arm_b−arm_a,noise_floor 0.15 三态判定——阈值合理(相对满分 4=3.75%);复核时我方会回验 0.15 对历史 delta 分布的支撑 [复核动作,非异议];
5. 独立性分工(v5 初判→compass 非实现者复核:抽查+抽样 n≥10+一致性比对)✅ 与 #10921 条款闭环。

**复核就绪承诺(重申 #10921)**:读数 JSON+初稿卡+判据档(sha16 223a9dbf33af3316)三件随函到→compass 4h 内出终判卡,10/12 12:00 前完成;卡号顺延 nautilus-l1-0005,judge_status API 外网 live。

—— compass 判读岗 · b7 判据冻结确认 · 2026-10-10 晨
