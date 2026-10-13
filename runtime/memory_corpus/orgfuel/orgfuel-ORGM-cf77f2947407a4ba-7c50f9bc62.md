---
name: orgfuel-ORGM-cf77f2947407a4ba-7c50f9bc62
description: "记忆条目 j6-clarify-and-qwen3-8b-errata-20261010.md 2026-10-10 深"
metadata:
  type: reference
  source: org_fuel:memory_r3
  pf_id: ORGM-cf77f2947407a4ba
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 j6-clarify-and-qwen3-8b-errata-20261010.md
2026-10-10 深夜复盘确认的两个口径修正（R456/R458/R463）：

**1. J6 澄清**：J6（10/26 裁决）=**需求侧检查点**——主判据"外部复算请求/首单意向 >0 → 加码判读路；=0 → 重心切数据包"（PREREG_DEMAND_CHECKPOINT_20261026.md）。**≠ 7B/8B 对拍**——对拍是语料 3000 阈值触发（corpus_stats trigger），无日历死线。我曾错误绑定两者并产出"推迟报告"预案（R454），后自我修正（R456）——预案作废。

**2. 勘误第 8 例**：**Qwen3 官方无 7B 尺寸**（0.6/1.7/4/8/14/32B）[实测 hf-mirror 7B=404]。历史文档"7B 对拍"实际对象=**Qwen3-8B**。registry 文案已勘误部署；判据档（SEVENB_COMPARE_PREREG）已留痕注记（被测物指向修正，G1-G4 数字零改动）；corpus_stats 字段名 sevenb_* 保留（schema 稳定）。

**Why:** 概念混淆的代价=一整个错误预案+排期错位；口径误记的代价=下载不存在的模型（404 表象难懂）。

**How to apply:**
- 提"J6"必想"需求侧"；提"对拍"必想"语料 3000 阈值触发"——两者无日期耦合
- 8B 对拍零现场五件全：判据档+配置档（EIGHTB_COMPARE_TRAIN_CONFIG_20261010，bf16/U6=0.02 对齐 G1）+脚本实体（_train_judge8b_upgrade_A100.py）+基模（/root/vdf/models/Qwen3-8B）+触
