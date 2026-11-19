# Compass 3.x × Assay：能力认识与实际发挥复盘

日期：2026-11-19
结论等级：`partial_ready`
原则：**自报不算；存在代码不等于形成组织能力。**

## 结论

我们已经在理念和工具层真正认识到 Assay 的意义，但还没有把它变成 Compass、Platform、Agent、V5 和历史记忆工作的统一生产闸门。

更直白地说：

- **Compass 3.x 的能力已经存在**：本地语义记忆、drift 检测、MCP/A2A、跨 agent 合约、治理工具、燃料与蒸馏路线、独立判官工具。
- **Assay 带来的关键认识已经写出来**：结果必须绑定字节、判据必须预注册、验证者必须和实现者分离、结论必须允许 `agree / disagree / not_computable` 三态、回执必须可被第三方重新计算。
- **真正的组织使用还不完整**：很多工作仍停在服务存活、日志计数、模型输出或本地 JSONL 候选；没有统一走完 `claim → criteria → pack → independent verify → signed receipt → consumer readback → wall`。

因此答案是：**认识到了，但还没有完全发挥出来。当前正在从“有能力”收敛到“每件重要工作都按 Assay 方式验收”。**

## Compass 3.x 到底提供了什么

代码和发布资料表明，3.x 不只是一个 BGE 检索插件：

| 能力 | 3.x 的原始定位 | 当前实际状态 |
|---|---|---|
| 长期记忆 | BGE-m3 本地记忆、混合检索、时间和项目范围 | [实测] 9876 daemon、8400 embed、8401 MPS rerank 正常；当前 recall 延迟已调到约 1.5–2.3 秒 |
| Drift | 对当前提示和真实失败锚点比对，在行动前提示偏离 | [实测] 有 2,934 条 verification log、3,263 条 usage log；最近的 drift mitigation sidecar 只有 11 条，尚不能证明所有 drift 都形成了后续行动闭环 |
| 跨 agent 协作 | thread recall、platform bridge、proof of impact、governance audit/lock/dispatch | [代码存在] 工具已注册；[不可验] 尚未证明每个 Platform/Agent/V5 任务都绑定了真实 project、task、receipt 和消费结果 |
| Evolution engine | extract fuel → external verdict → distill | [实测] 当前 distill 写入冻结；历史候选 235/355 已复核，仍有 120 条待处理，正式发布 0 条 |
| Assay judge | 预注册判据、VerifyPack、三态 verdict、Ed25519 receipt、public wall | [代码存在] `assay/`、`tools/verifypack/`、`scripts/verify_receipt.py` 均存在；[实测] 当前记忆复核 worker 只生成 hash-bound JSONL 候选，还没有把全部候选转成正式签名回执并进入 wall |

## Assay 真正改变了什么

Assay 解决的不是“再加一个 judge 模型”，而是解决以下信任问题：

1. **模型说完成，不等于完成。** 必须拿原始输入、固定版本和可复算规则重算。
2. **实现者自己打分，不算独立验证。** 实现、验证、消费要分开。
3. **无法计算不是通过。** `not_computable` 必须留在记录里，不能被压成成功或失败。
4. **一次签名不够。** 回执要绑定 pack manifest、代码/配置身份、时间和验证者，并且第三方可以脱离签发者重验。
5. **失败不能删除。** disagree、not_computable、challenge、errata 都要留在 wall 上。

这是我们以前经常没有贯彻到底的地方：把“服务在跑”“有文件”“模型返回了结果”“某个窗口说完成”当成了任务闭环。

## 现在已经发挥出来的部分

### 1. 记忆读取闸门已经开始按 Assay 思路工作

- 未经语义复核的 `distill-*` 不进生产索引。
- 非红色 drift 的 `session_*` 不进生产索引。
- 原始卡片保留，不能靠删除噪声伪造干净。
- 复核队列绑定 source、summary、narrative、anchors 的 SHA256。
- 双独立审查器使用 MiniMax-M3 和 Kimi k3-256k。
- 当前 `hold` 不会被自动发布。

这已经不是普通的“模型总结后写回记忆”，而是开始具备证据闸门。

### 2. Compass 服务开始用实测而不是自报

最近对 BGE 链路做了拆分：

- query embedding、文件扫描、重排分别计时；
- 证明慢点在同机 MPS reranker 的候选宽度和 token 长度，不是“BGE 在云上”；
- 对 `30×8192`、`30×512`、`16×512` 做固定查询 A/B；
- 当前小样本中，闸门允许的记忆卡 hit@5 没有下降，16×512 中位重排约 1.49 秒。

这属于 Assay 的测量习惯已经进入运行维护，但仍是小样本回归探针，不是正式客户验收。

### 3. 负结果开始保留

当前复核结果中大量条目保持 `hold`，低锚点、源文不支持、模型意见不一致都没有被包装成成功；9B 也只做过单条真实历史 smoke，没有被宣布为全历史接受。

## 仍然没有发挥出来的部分

### 1. 组织记忆还没有完成正式 Assay receipt 闭环

当前 worker 的 `approved_receipt_candidate` 只是“满足当前机械门槛的候选”，不是正式的 signed receipt。缺的环节包括：

- 统一的 VerifyPack；
- 独立 verifier 身份；
- Ed25519 签名和公钥指纹；
- 第三方可复算的 receipt check；
- 写入 wall 的 agree/disagree/not_computable 记录；
- memory consumer readback。

所以现在可以说“审查在进行”，不能说“组织记忆已经被 Assay 认证”。

### 2. Drift 还没有成为行动闸门

有 drift 分数、有 mitigation log、有规则命中，但目前没有证据证明：每次红 drift 都绑定了具体任务、负责人、修复结果和外部消费结果。它更像一个已经能报警的传感器，还不是完整的闭环控制器。

### 3. 跨对话治理仍有断点

目前仍存在：

- 用户→项目→任务→回执映射没有完全验收；
- 多个 Codex 对话框 active/idle/notLoaded 和真实服务状态没有统一账本；
- shared worktree 仍有脏改动；
- 提交、CI、live process、consumer readback 之间仍可能错位。

这说明 governance 工具已经有了，但组织还没有强制每项工作都经过 governance + receipt。

### 4. Fuel 和 9B 压缩还没有被 Assay 认证

9B 可以生成摘要，不等于摘要保留了源文关键事实；当前只有机械锚点 smoke 和正在进行的双模型源文复核。没有完成固定训练/验证集、冻结 split、独立判官、模型版本身份和 signed result，就不能把压缩结果当成训练燃料或长期记忆。

## 下一步收敛闸门

以后 Compass 的重要工作统一采用这条短链：

```text
Claim
  → preregistered criteria
  → source-bound verification pack
  → verifier ≠ implementer
  → agree / disagree / not_computable
  → Ed25519 receipt
  → consumer readback
  → public/internal wall
```

先落地三件事：

1. 把当前 `distill-source-review` 候选转成真正的 VerifyPack + signed receipt；没有 receipt 就不能发布记忆。
2. 给每个跨对话任务补齐 `user_id / project_id / task_id / artifact_sha / verifier / consumer_readback`，解决可信的用户→项目映射。
3. 把 9B 压缩验证作为 Assay subject 运行：固定输入、固定模型 hash、固定指标、独立复核、失败原样留档。

完成这三件事后，Compass 才真正从“功能齐全的记忆和治理插件”变成“组织可以依赖的压缩×验证基础设施”。

## 证据坐标

- 3.x 能力与公开定位：`README.md` 的 memory/drift/governance/Assay sections。
- Assay 原则：`docs/protocol/ASSAY_PROTOCOL_V0.md`。
- 第三方验签入口：`scripts/verify_receipt.py`。
- VerifyPack receipt 实现：`tools/verifypack/receipt.py`。
- 当前服务与记忆复核状态：`runtime/cross-dialog-receipts/20261119-R574.json`。
- 当前复核进度：`runtime/scratch_distill_pilot_20261104/semantic-review-progress.json`。
- 当前重排 A/B 探针：`runtime/cross-dialog-receipts/20261119-rerank-ab.json`。
