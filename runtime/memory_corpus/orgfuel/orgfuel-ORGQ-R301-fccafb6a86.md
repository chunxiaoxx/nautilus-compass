---
name: orgfuel-ORGQ-R301-fccafb6a86
description: "### R301 · 2026-10-07 晚(loop v2 R8:巨物载入止血✅+吞吐瓶颈实锤+消费方治理函) - "
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R301
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R301 · 2026-10-07 晚(loop v2 R8:巨物载入止血✅+吞吐瓶颈实锤+消费方治理函)
- **巨物快速止血✅[实测]**:SKIP_BIG 阈值 200→600MB(两处,备份 bak_20261007_big)→重启→**loaded=500 skipped=0**(502MB 首次真载入),RSS 2.98→6.12G(预算内,内存 15G 总余 8G)。查询慢源头消除。
- **定性转移[实测]**:载入后 overload 仍持续(+148/2min 不退,CPU 107%)——**吞吐瓶颈实锤**(入站率>单机 CPU embedder 上限),非巨物问题。最大嫌疑=v5 brain 重试流无退避。
- **双函**:v5 退避请求(10385,指数退避+断路器+峰值降频;生效判据=reject 速率降)+platform 升级(10386,长期 GPU embedder/扩容排产+BYZ 判例建议)。
- 巨物拆分工程降级:载入止血后拆分 urgency 下调(内存可容忍),保留值守窗长线。
