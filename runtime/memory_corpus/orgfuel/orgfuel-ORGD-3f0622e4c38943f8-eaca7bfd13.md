---
name: orgfuel-ORGD-3f0622e4c38943f8-eaca7bfd13
description: "[## 执行坐标(交接用;2026-10-05 开跑时回填)] - 机器/基座/配方:A100 223.109.239."
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-3f0622e4c38943f8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 执行坐标(交接用;2026-10-05 开跑时回填)] - 机器/基座/配方:A100 223.109.239.30:23236(paramiko;限流退避 115s);/root/vdd2/models/Qwen3-14B;环境=/root/venv_fw(torch 2.11.0+cu126/peft 0.21.0/transformers 5.5.0,smoke 同环境实测);
- 脚本:`tools/train_judge14b_upgrade.py`(smoke 同构迁移;GPU 守门>2G 退出不抢 B 臂);
- **U1 语料回填 [实测]**:全量 judge 语料=qid 分组防泄漏切分三件,A100 实物 sha256 前 16 位三件全对上 P2v2 档——split_train 1162 条(`35683198dd3c4992`)/split_dev 143 条(`942e4daeaedca2fb`)/split_test 149 条(`4bcaf1c9b551f336`),合计 1454;训练用 split_train 全量,3 epoch(≈873 步,MAX_STEPS_CAP=2000 取先到);
- **U5/U6 复核集回填(核对结果如实记)**:预注册原设想构成="判例勘误+人工抽检沉淀"——执行时核对判分语料仓(runtime/verdict_corpus/),**该构成无现成实物,不臆造**;回填=split_dev+split_test 全量 **292 条**(held-out,qid 分组切分保证与 train 零相交,n≥200 满足);构成差异如实申报:dev+test 与训练同语料同分布,比"勘误沉淀新题"口径偏易,对冲=同集两模型对拍(同题同 gold)+逐条读数落盘(eval292_14b/17b.json
