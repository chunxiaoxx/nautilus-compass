---
name: orgfuel-ORGD-1ada64e7623491c6-333da044ca
description: "[## 升格判据(全 [实测] 层)] | # | 判据 | 门 | 说明 | |---|---|---|---| | "
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-1ada64e7623491c6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 升格判据(全 [实测] 层)] | # | 判据 | 门 | 说明 |
|---|---|---|---|
| U1 | 训练完成 | 全量 judge 语料(qid 分组防泄漏版,条数以语料实物为准,执行时回填)零 OOM 正常退出落 adapter | 复用 smoke 配方(train_judge14b_smoke.py,MAX_STEPS 按全量重定,预注册改为 ≤2000 步或 3 epoch 取先到) |
| U2 | 显存峰值 | <36G | 同 smoke S2 |
| U3 | 收敛 | loss 末 20 < 首 20 | 同 smoke S3 |
| U4 | 格式合规 | 抽 n=100 题推理,JSON 判读输出合规 ≥98/100 | 比 smoke S4(20/20)加大样本 |
| U5 | **判别力不劣门** | 现役判读器判绩账复核集(n≥200,同题同集同 gold):14B gold 一致率 ≥ 现役 1.7B 同集读数 | 不劣=可换;核心门。复核集=判例勘误+人工抽检沉淀(非训练集,qid 不相交) |
| U6 | **判别力显著门** | 同 U5 集:14B ≥ 现役读数 +3pp | 达此档=**推荐**切换;仅达 U5 未达 U6=保留 1.7B 现役、14B 记档待语料增长再评 |
| U7 | 成本申报 | 推理时延 P50/P95+吞吐+VRAM 如实入档,不设门槛 | 装订定价与热路径评估用;14B 慢是预期,只申报 |
