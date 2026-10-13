---
name: orgfuel-ORGG-18cd445ef40b8381-ad7fa3fb2f
description: "判读档判例 2026-09-21-hosted-jev-eval-protocol · 三 · 判据(预注册,锚 cal"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-18cd445ef40b8381
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-21-hosted-jev-eval-protocol · 三 · 判据(预注册,锚 calibration-claim-verify-v1)
## 三 · 判据(预注册,锚 calibration-claim-verify-v1)

- 每题记录:Jev 的选择+完整概率分布(API 返回)。
- 指标:top-label Brier / ECE(15 bins)/准确率;三套口径同报
  (严格全题/按置信度分层/按题型分层)。
- 复现件:决策集生成脚本+全部原始响应(jsonl)+计算脚本=VerifyPack v0.3 包
  (calibration claim kind,subject=API 版本+题集 seed,TTL 90 天)。
- 红线:不重跑不并行不挑选(一次全量;失败请求如实记录,不剔除)。
