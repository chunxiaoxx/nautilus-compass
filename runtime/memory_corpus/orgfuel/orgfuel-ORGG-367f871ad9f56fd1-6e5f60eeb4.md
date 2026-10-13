---
name: orgfuel-ORGG-367f871ad9f56fd1-6e5f60eeb4
description: "判读档判例 2026-08-31-unified-verification-contract · 4. 落地路线(最小步"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-367f871ad9f56fd1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-31-unified-verification-contract · 4. 落地路线(最小步,不开新战线)
## 4. 落地路线(最小步,不开新战线)

1. **v0(纯文档,本文)**:合同 schema 定稿 + 四协议映射,等用户拍板。
2. **v1(首个正式案例)**:d13 定案按合同格式归档(claim=刀3 LoRA 有效/无效,verifier=V2 独立复算,prereg=d12 对照,verdict=待出)——用真案例校准 schema,不写代码。
3. **v2(最小接口)**:验证回执统一 JSON schema(`{claim_id, verifier_type, prereg_ref, verdict, receipt_sig}`)**独立成包**(桥的单向依赖点:两边依赖它、互不依赖),进台账;`_OUTBOUND` 函模板补齐 5 字段。此时对外"第三方验证平台"才有第一个可卖的接口——卖的是桥面上的回执,不碰两边数据池。
4. **V4 验证器**(具身侧,依赖飞轮框协同):不可仿真性测试 = 用仿真器重放候选数据,测其统计特征能否被仿真器分布再生;产出即具身数据的"Gate B"。
