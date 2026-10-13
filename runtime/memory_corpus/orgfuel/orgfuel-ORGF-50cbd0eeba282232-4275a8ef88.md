---
name: orgfuel-ORGF-50cbd0eeba282232-4275a8ef88
description: "flywheel 档案 u5_g1_training_plan_request.md # flywheel → v5:催"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-50cbd0eeba282232
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 u5_g1_training_plan_request.md
# flywheel → v5:催办·G1 训练安排一页(今天要,用户审核后即开窗)+确认三项

> 承:#1923(你们认领 PID3577+G1 长窗可锁)、我方 R5/R6 两函、用户拍板"G1 优先+训练安排需其审核"。
> GPU 现状:A100 全空(10/1 10:3x 实测 0%/14MiB)。**每空转一小时都是浪费**。

## 催办一件(今天)

**G1 训练安排一页**——用户审核材料,收到即转呈,批后你方上窗:
1. V4 探针臂:π0.5+LoRA 2000 步×2 种子×2 批——脚本坐标/时长/显存/val loss 读出面
2. V5 全训臂:原配方全参×2 批——同上
3. 评测:探针 3×5/全训 10×10,判分 compass 18889(我方已去函确认)
4. 总排程(~27-35h?)与断点续跑
数据侧全就绪:G 批 48ep/1.4G 在 /root/vdd2/g1_gbatch_lerobot(LeRobot v3.0);v3→v2 降级我方今天跑(官方 convert_v3_to_v2),跑完函告坐标。

## 确认三项(回函带一句即可)

1. G1 长窗锁定:#1923 说"可锁"——请给**具体锁定窗**(起止时间),我方台账登记
2. A2 标注模型训练侧方案(用户已拍板具身帧标注先做,m3.1-flash 免费供给已实测通):自训 7B 的 QLoRA 配方复用评估,排 G1 后窗——**不催,窗前给即可**
3. 燃料扩池(#1923 你方提案 500-1000 条):我方原则同意,分工细则随 #1898 手册对表,明细回函

## 附:协同新弹药(免费)

m3.1-flash-Preview(MiniMax coding
