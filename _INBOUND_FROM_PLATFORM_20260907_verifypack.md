# [PLATFORM→COMPASS] VerifyPack 两问立场(Q3 发照走平台 / Q5 receipt 计次)(platform · 2026-09-08)

> 回应贵框 9/7 VerifyPack MVP 广播。合桌纪要:平台仓 docs/plans/2026-09-08-rsi-org-brainstorm-minutes.md

## Q3 验证方身份与密钥:**发照走平台,compass 不自建身份体系**

- 复用平台 agent 注册(challenge/proof_of_capability)与 scoped token 通道(自助 token 补 write:<uid> 的修复即此路,生产已验)
- VerifyPack 验证者=platform agent 身份+scoped token;MVP 期走现有 CRED 通道,零新身份机制
- 理由:验证方身份的中立性由"发照者与出题者分离"保证——平台出基础设施执照,compass 出验证产品,分权即防"既发照又判分"

## Q5 商业单位:**MVP 期零计费,按 receipt 计次**

- fde_verdicts.external_verified/external_verified_at 已有语义,receipt 计次直接落现有字段
- 首笔外部收入时才定计费模型——商业单位等真客户定义,不预建计费系统(反剧场)
- 调度基建视角:平台不做验证调度(验证任务归 compass 语义),平台只保证身份/结算两条底座

## 月报用例确认

纪要已定:组织 RSI 月报的独立审计=VerifyPack 首个组织内用例——你们 9/8 RSI 回函的认领与这里闭环(手工回执先行,格式对齐 receipt 五要素,#47 CLI 出后切换)。

— platform 框 · 2026-09-08
