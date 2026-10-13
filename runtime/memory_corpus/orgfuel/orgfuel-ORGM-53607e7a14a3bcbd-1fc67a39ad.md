---
name: orgfuel-ORGM-53607e7a14a3bcbd-1fc67a39ad
description: "记忆条目 daemon-v32-rootcure-20260930.md 2026-09-30 云 daemon 根治方"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-53607e7a14a3bcbd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 daemon-v32-rootcure-20260930.md
2026-09-30 云 daemon 根治方案 v3.2(用户令"真正长期有效的方案")全链落地,待窗口切换。

**根因四层**(实证):PyList 32KB/向量 8x 膨胀(根本)/LRU 与 pkl 回读互搏/in-flight 无豁免/bind 在 warmup 后(冷启动断服)。

**四刀**(runtime/cloud_daemon_v32_20260930.py,commit 94a7ef7f→01eba599):
1. numpy float32 化(惰性转换旧 pkl,单测 cosine 等价 1e-6)
2. 容量预算 300k 向量替代 MAX_PROJ=8 硬逐(churn 根因);**红线自修:MAX_PROJ=64 在 75 项目场景仍硬逐 11 个(压测实抓)→降级纯护栏 256**
3. listen 前置+warmup 后台+load 锁(重启零断服)
4. MSG_PEEK ping/status 豁免(churn 期监控不瞎眼)

**合成压测实证**(tools/v32_synth_bench.py):75 项目×600 向量仿生产规模,np 驻留 **175.8MB vs PyList 等效 1408.7MB=8.0x**,与生产 cache 实测 1469MB 吻合;J1 生产预期 RSS<3.5G 可达。

**蓝绿备件**(ops/v32_bluegreen_deploy.sh 五步幂等+runbook):已 upload 云端(md5 c5d64636);blue 步内置 <4000MB 熔断(系统仅 4.3G);**窗口铁律=10/1 08:53 记忆判据读数之后**;回退一步零确认;孤儿 pkl 10261 个/1469MB 刀 D 分离单
