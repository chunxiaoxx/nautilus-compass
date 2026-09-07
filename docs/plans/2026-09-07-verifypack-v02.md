# VerifyPack v0.2 立项(2026-09-07 用户拍板)

> trace: verifypack-v02-20260907 · 层级:roadmap ①圆心最小产品
> 一句话:**第三方数据效用验证的协议化**——把「信件人工验证流」升级为「可验签的自足协议」。

## 1. 问题(measured)

flywheel→compass 的 batch001 复核请求已展示完整流程,但载体是 markdown 信件:
- 声称值在 json,复算靠人工读指引,回执无密码学签名;
- 结算方(买方)无法独立验真「验证确实发生过且结论一致」;
- 每次验证的协议开销(信件往返)不可规模化。

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

## 3. 现有资产盘点(measured)

| 资产 | 位置 | 复用 |
|---|---|---|
| utility-metrics-protocol-v1-frozen | flywheel 仓 | claims 结构直接继承 |
| scripts/verify_pack.py | flywheel 仓 | build 命令的底 |
| 复算路径惯例 | flywheel 手几何函最小验证代码 | verify 命令的形态 |
| 签名回执惯例 | compass 逐函 agree/disagree 格式 | receipt 的内容结构 |
| 宪法边界 | compass CLAUDE.md/回执惯例 | 独立技术验证≠客户验收≠结算决定(写进 spec 前言) |

## 4. DoD(可裁决)

- [ ] Spec v0.2 文档 + CLI 三命令+check;
- [ ] **batch001 用新协议端到端跑通一次**(build 已有包→verify 复算 6 条 L1→receipt 签名→check 验签通过);
- [ ] 手几何四量复算作为第二个包样本;
- [ ] flywheel 确认协议可用(回执形式)。
- 时间:9 月内;依赖 9/9-9/10 batch001 人工复算完成(需求输入)。

## 5. 边界与红线

- compass 只做验证方技术设施,**不作客户验收或结算决定**(宪法,写死在 spec);
- 数据不出验证方最小必要范围:verify 只读包内产物+声明路径,不拉全量数据;
- v0.2 全开源(repo 内),商业模型(按次/订阅)等真实第三方需求出现再定。
