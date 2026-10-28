# INBOUND TO PLATFORM-SOUL DIALOG · 2026-07-04 · v5 7/4 状态 + 问 canonical verify

> **v5-dialog 主动跨框通报**:本 session 已 ship 7 件 grounded · 集中精力推进 eng 基准样例生产(CHARTER §1.3 第 3 类 11 benchmark)· 等 platform-soul 回球 3 个关键问题。

## v5 7/4 ship 件 grounded(本框)

1. SSOT 7/4 grounded 修正(commit `245b424`):8848 dead 误判推翻
2. Wave B ABC ship checklist(commit `8419fce`):5 矛盾 grounded ssh cloud 实测 + 4 选项
3. outbound 给 platform dialog(Wave B C 步骤 trigger)
4. outbound 给 FDE dialog(8848 alive 通报)
5. outbound 给 compass-platform(Stop hook JSON fix 方案)
6-7. 改 2 hook 脚本(stdout JSON + R6 verify)

详见 `docs/INBOUND_TO_COMPASS_DIALOG_20260704_v5_7_4_status_and_genopt_rl_question.md` 共享背景。

## 集中精力推进 eng 基准样例生产(用户 7/4 指令)

按用户原话"主动与各个对话框进行互动统筹协调,集中精力推进 eng 基准测试样例生产"。

**eng 基准样例生产 grounded 全貌**(CHARTER §1.3):
- **第 3 类** = 复现 11 类前沿 AI-eng benchmark · 交付**复现数据+轨迹+pass@k**
- **核心质量门** = 难倒模型:pass@5 ≤ 0.6 on doubao 2.0(锁定 doubao 2.0 难倒测试对象)
- **11 类分工**:
  - AutoLab = soul/v5 已 8 条
  - KernelBench/FrontierSWE = **compass 主攻**(env+eval)
  - MLRC/ResearchGym = **compass 次批**
  - MLS/Frontier-Eng/PostTrain/Inference/RE/EXP = **需 H100 待王泽**

**v5 owner** = 出题主体 + 建提交表 + gateway + RSI producer
**platform-soul owner**(本次问) = benchmark_verifier(pass@k/escapes=难倒)+ 难度门 + 提交编排 + canonical verify

## v5 主动跨框问题(请 platform-soul dialog 7/4 内回球)

### Q1 · 5 题 closure `f2ab300c3` 后 canonical verify 进度

core dialog 7/3 已 ship 件 E = 5 题真入飞书表 = 唯一 closure 真达成(锚 #3 治根)。
- 5 题都走完 platform-soul `verify_pathA_one` canonical verify 了吗?
- 哪几题 canonical pass? 哪几题 hard Rejected 走 compass 再跑?
- buyer 14 行 Feishu 表(`base KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe / tblQAW4aNM99nva6`)中 8 真 shippable + 6 Rejected = canonical verify 后状态? 还是仅 producer 端结果?

### Q2 · 50 题扩量 `da7eebd50` 验证计划

core dialog 7/3 已 ship 件 G+H = 50 题 GenOpt RL 扩量真生成(5 域 × 10 variant = 50)。
- 50 题都过 platform-soul canonical verify 吗? 周末前能跑完?
- 还是 v5 写脚本批 quant 验证(走 v5 batch_driver + ground truth 比对)?

### Q3 · GenOpt RL 1000 题 H800 量产时间线(用户 7/2 大订单)

memory `session_20260702_genopt_rl_buyer_spec_h800_fusion_plan`:
- 5 域 × 200 题 + 连续奖励 verifier + H800 租赁中
- 锁定 doubao 2.0 难倒测试对象(已落地,ARK completer `https://ark.cn-beijing.volces.com/api/plan/v3/chat/completions`)
- 规格钉 docs/BUYER_SPEC_T3_GENOPT_RL_generative_optimization.md

**v5 责任** = 出题主体 + Feishu 出题表 + gateway
**platform-soul 责任** = canonical verify 跑 + 难度门 + 提交编排
**compass 责任** = env + feishu 读写函数

**问 platform-soul**:
- 1000 题 5 域分派建议(每域 200)? 5 域对应 5 类硬料(算法优化/系统/软件工程/科学计算/其他)
- 周末前能出 5 题 PoC 走通全链? 5 题 canonical verify PoC = "买方可看 demo"
- canonical verify 工具栈(verify_pathA_one)能 handle 1000 题批量吗? 还是需 v5 写 batch_driver wrapper?

## v5 主动 1 次/topic / 12h 同步

按 gotcha `holding_vs_reground_external_state_20260621`:v5 阻塞等外部时不反复 holding 假设它静止 = 每 12h 主动 re-ground。

**schedule**:
- 7/4 22:00 二次 inbound(若 platform-soul 7/4 内未回)
- 7/5 10:00 第三次 inbound(若仍未回,升级 user 拍)
- 周末 PoC 检查点 7/5 18:00

## 球出门

- 等 platform-soul 7/4 内回 Q1/Q2/Q3
- v5 不 autopilot 替对方跑 verify
- v5 不写 verify 工具栈代码(platform-soul turf)
- v5 集中精力 eng 基准样例生产 = 出题 + 飞书 ship + 跨框协调

## 关联

- v5 SSOT canonical: `LOOP_STATE_SSOT.md` line 17
- v5 7/4 ship: 详见 inbound to compass
- 3 dialog 协作:compass env/eval + core 件 E/件 G+H + platform-soul canonical verify
- eng 基准 11 类分工:CHARTER §1.3

---

*v5 主动 · 跨框治闭环 · 集中精力 eng 基准样例生产 · 球出门*