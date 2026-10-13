---
name: orgfuel-ORGH-30eb922ac9e0b59f-71a398f6d6
description: "工具决策记录 train_judge14b_upgrade.py 14B QLoRA 判读器升格跑(PREFOR_JUD"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-30eb922ac9e0b59f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 train_judge14b_upgrade.py
14B QLoRA 判读器升格跑(PREFOR_JUDGE14B_UPGRADE_20261005.md U1-U7)。

配方=tools/train_judge14b_smoke.py 同构迁移(peft 三件套补丁/4bit nf4/LoRA r16/AdamW 1e-4)。
U1 全量语料 3 epoch(MAX_STEPS 上限 2000,取先到)零 OOM 正常退出落 adapter
U2 显存峰值<36G / U3 loss 末20<首20
U4 test 抽 n=100 三态输出合规≥98/100(smoke S4 同构口径,如实申报)
U5/U6 复核集=split_dev+split_test 全量(292 条,held-out):14B vs 现役 1.7B champion 同集对拍,
       U5=14B≥1.7B(不劣);U6=14B≥1.7B+3pp(显著,达此档推荐切换)
U7 推理时延 P50/P95+吞吐+VRAM 如实申报(14B=4bit,1.7B=bf16,口径差异注记)
qid 零相交核查:复核集与训练集按 qid_of(id) 派生键,交集必须为空,结果落 report。
启动守门:GPU 显存占用>2G 即退出(B 臂/flywheel 优先,不抢卡)。
