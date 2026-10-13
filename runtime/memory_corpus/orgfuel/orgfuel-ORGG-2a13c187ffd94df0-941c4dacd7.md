---
name: orgfuel-ORGG-2a13c187ffd94df0-941c4dacd7
description: "判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 五、smoke 实测兑现(20"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-2a13c187ffd94df0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 EIGHTB_COMPARE_TRAIN_CONFIG_20261010 · 五、smoke 实测兑现(2026-10-10 · R487 · 证据层 upgrade_path 落地)
## 五、smoke 实测兑现(2026-10-10 · R487 · 证据层 upgrade_path 落地)

- **8B bf16 训练可行性:[实测]**——25 步短训 smoke 全管线 A100 实跑:
  - **U2 峰值显存 15.07GiB**(远低 36G 预算)/ U1 零 OOM / U4 输出合规 **100/100**(门 98);
  - **U5 对拍信号:8B 25 步短训即 0.8801 vs 现役 1.7B 0.8767(+0.34pp 不劣,PASS)**——25 步=全量 1/35 训练量,全量训练 G1(+2.0pp)有真实希望;
  - U6 显著超现役 FAIL=预期内(短训不判定模型能力,E-NACRE-1 同因);U7 成本申报(train 12.4s/推理 p50 0.0375s/吞吐 26.7/s);
  - report 正本:/root/vdf/judge8b_upgrade/upgrade_report.json(A100);
- 排障两枚(实录):①脚本期望语料名 split_train.jsonl(无 _v1)→软链修;②启动门 2G 拦 A100 常驻服务(判分+嵌入+rerank ~7G)→COMPASS_GPU_BUSY_G 参数化=12G(真大训练仍拦,常驻共存放行);
- smoke 脚本正本:/root/vdf/judge8b_corpus/j8b_smoke.py(MAX_STEPS_CAP=25 副本);正式脚本 _train_judge8b_upgrade_A100.py(本仓,U6=0.0
