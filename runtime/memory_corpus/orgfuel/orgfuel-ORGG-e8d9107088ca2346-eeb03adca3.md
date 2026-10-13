---
name: orgfuel-ORGG-e8d9107088ca2346-eeb03adca3
description: "判读档判例 2026-09-07-verifypack-v02 · 2. v0.2 范围(最小) ## 2. v0.2 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-e8d9107088ca2346
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-07-verifypack-v02 · 2. v0.2 范围(最小)
## 2. v0.2 范围(最小)

1. **协议文档 VerifyPack-Spec v0.2**:包结构(manifest/claims[]/repro_script/env_decl/receipt);
   claim 分级沿用 L1(无环境可复算)/L2(需环境,降级核对内部一致性)。
2. **CLI 三命令**:`verifypack build`(数据方生成自足包)/`verify`(验证方复算,逐条
   agree/disagree+复算值)/`receipt`(生成签名回执,ed25519,含 claims 哈希)。
3. **验签**:`verifypack check` 供结算方——验签名+对 claims 摘要,不重算。
4. 密钥:验证方身份密钥对(首版 compass 框一把,后续多验证方注册)。

### 不在 v0.2(推后)

- 链式审计/时间戳服务(Aegis 式合规件);
- 多验证方共识;
- 计费(先协议后生意,商业模型等 batch001 复评)。
