---
name: orgfuel-ORGG-b17a92df645e1a0d-adb332bbe2
description: "判读档判例 2026-09-19-mechanism-pivot · 二 · 机制解三支柱(区块链结构的正确移植) ##"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b17a92df645e1a0d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-19-mechanism-pivot · 二 · 机制解三支柱(区块链结构的正确移植)
## 二 · 机制解三支柱(区块链结构的正确移植)

### 支柱一 · 产出即打包(attest-at-generation)
比特币交易签名是钱包**自动**做的,用户无感。对应物:**assay-sdk**——任何 agent
框架跑评测/产出声明时,一个函数调用自动产出 VerifyPack 格式证据包+签名。
生产者不需要理解协议(就像 git 用户不需要懂 merkle 树,commit 天生带哈希)。
**对框架是纯增益**:自动保存评测产物+自动生成可发布成绩页+免费第三方签名——
像 coverage 工具一样会被集成,这就是"先加入者先赚"的机制化。

### 支柱二 · 验证即消费前提(verify-on-consume)
比特币节点自动验证每笔收到的交易,不通过就拒收。对应物:**compass 记忆层是
A2H2A 的咽喉**——agent 消费信息必经记忆层。把验签+可复算性标记做进 ingest 的
默认步骤:带 receipt 的记忆自动验签打标 `verified`;不带的标 `self-reported`。
**这个结构位置只有我们有**(竞品记忆层没有判据库和验签器)。MCP 工具
`assay_verify` 同理:任何 MCP 客户端装了 compass 就能对任何产物验签——验证
能力经 MCP 分发,像 DNS 解析一样无感。

### 支柱三 · 激励内生(HTTPS 式默认态反转)
Let's Encrypt 没有说服任何网站买证书——它把证书成本降到零,然后**浏览器把
无 HTTPS 标记为"不安全"**,默认态反转,不参与的人开始需要解释。我们的对应:
SDK 免费+自动化(验证成本→零)→墙/记忆层/榜
