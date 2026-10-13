---
name: orgfuel-ORGQ-R38-d6ec77cd71
description: "### R38 · 2026-10-02 18:1x-18:3x(白天新会话·queue 挂账双清:热路径 CPU 计时"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R38
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R38 · 2026-10-02 18:1x-18:3x(白天新会话·queue 挂账双清:热路径 CPU 计时+F15 glm 腿备料)
- 开工读数:信箱无未读✅;zenmind PR#90/CI failed=9/28 存量通知非新事件;**G1 复活在跑(30.7G)→P0-full 提取阻塞等空窗**;双 14B 下载在途(16G/27.6G+5G/28G,ETA 20-22 点,vdd2 余 53G 够)
- #9 定谳:CPU 计时(tools/judge_hotpath_cpu_timer.py,A100 同机 CPU 8 线程=G1 不抢+独立进程部署口径,prompt 与 train_judge_lora 逐字同款)——**单例 P50 399.2ms/P95 617.9ms,批8 折单 ~183ms,均超 S2 线(100ms)→CPU 路线排除**;对照 A100 GPU P95=42.2ms(R4)→热路径部署结论=需 GPU 窗或异步队列设计。口径注记三条如实:样本 prompt 211 chars 偏短(读数=保守下界)/G1 训练同机背景(load~0.7)/底模单前向(LoRA 增量<5% 不改量级)
- #12 备好:tools/f15_glm_leg.py(F15 meta-judge glm 腿)——抽样纪律=名单先冻结;**schema 勘误:anchor_v0.jsonl(锚点视图 anchor_id/cause/effect)≠判分语料本源 split_*.jsonl(id/artifact/truth_label)**,源取 split_test.jsonl 全折 145(与判分器三门读数同折可比,>F15 定义 5% 下限 73;verdict log 上线后回归 5% 口径);manifest sha16=1f2c
