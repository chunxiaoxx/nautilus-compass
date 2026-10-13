---
name: orgfuel-ORGF-6d2fec4cf96275c3-3be77bf59f
description: "flywheel 档案 g1_train_checklist_body.md # flywheel → v5:G1 训练"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-6d2fec4cf96275c3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 g1_train_checklist_body.md
# flywheel → v5:G1 训练适配清单(填空级——我方推到此处,最后一道训练域硬坎交你们)

> 用户令"G1 开启推动",我方按 fallback 把数据/配置/注册全部做完(见下"已完成"),**openpi 本地数据集加载=最后一道坎,归你们训练域**。GPU 仍空转。

## 一、我方已完成(全部实测坐标)

1. **G/B 双数据集 v2.1 格式**:/root/vdd2/g1_gbatch_lerobot_v21 与 g1_bbatch_lerobot_v21
   (tasks.jsonl/episodes.jsonl/info.json v2.1 三件+data/videos 硬拷贝;G=42eps/99805 帧)
   转换器:/root/g1_v3_to_v21.py(原 v3 目录未动)
2. **openpi 双配置已注册**:src/openpi/training/config.py 尾部追加 `g1_probe_G`/`g1_probe_B`
   (Pi0 LoRA:paligemma gemma_2b_lora+action gemma_300m_lora;weight=gs://openpi-assets pi0_base;steps=2000;batch 8;backup=config.py.bak_g1)
   验证脚本 /root/g1_verify_config.py → REG_OK
3. **权重**:gs://openpi-assets/checkpoints/pi0_base(openpi 原生 CheckpointWeightLoader,零格式适配)
4. **判分窗**:compass 18889 已确认就绪;预注册变更一已
