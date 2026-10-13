---
name: orgfuel-ORGD-8156ea4d09993c72-a4162ad4bd
description: "[## 二 · 7B+ 判官需求档] - **判别力需求**:dim1(完成度三态 完整/部分/未动)是 3B 盲区(零"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-8156ea4d09993c72
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 二 · 7B+ 判官需求档] - **判别力需求**:dim1(完成度三态 完整/部分/未动)是 3B 盲区(零方差);升级后 dim1 恢复判读资质的门槛=对主包 498 帧出非零方差三态分布,且与 OOD 400 题同口径。若 7B 仍零方差→判别力问题在任务设计层(完成度判据对 VL 模型不可分),反馈组织方改判据而非再升模型。
- **资源配置**:A100 34G 空窗实测在(13:08 探针 0%/14MiB);Qwen2.5-VL-7B bf16≈16G,守门脚本(`_gate_keeper` 模式 free≥16000MiB)直接换阈值;3B 判读 2.4s/题×898≈36min,7B 预算×2.5≈90min,单窗可完成。
- **管线复用**:`tools/e1_main_j2_batch_judge.py` v4 配置(bf16+PIL 入参+字段级正则解析+占位符示例)换模型路径即用;判据/prompt 零改动(判据不因模型升级而变——只许更严纪律)。
- **验收判据(预注册,升级时冻结)**:①dim1 三态非零方差;②dim2 与 v4 读数相关性报告(变化要解释);③OOD/主包双包同口径;④全档留痕同六轮制。
