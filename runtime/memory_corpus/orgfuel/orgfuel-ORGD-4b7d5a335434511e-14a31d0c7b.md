---
name: orgfuel-ORGD-4b7d5a335434511e-14a31d0c7b
description: "[## DoD] - [x] episode 引擎 + spec 校验(8 测试:分组/跳跃/跨组/帧级/缺字段/单帧/"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-4b7d5a335434511e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## DoD] - [x] episode 引擎 + spec 校验(8 测试:分组/跳跃/跨组/帧级/缺字段/单帧/校验×2)
- [x] subject/TTL/chain + 向后兼容(8 测试:v0.2 字节不变·过期·错配·链·spec)
- [x] verifypack 全量 77 passed(旧 61 零回归)
- [x] CLI 端到端冒烟:build→verify --ttl-days→check VALID;重签过期回执→EXPIRED
- [ ] 首个实弹 episode pack(NanoJev Tier-2 重放或 flywheel Day0 验收)
