# 从迁移堵点到 Compass × Assay × 组织 Agent 进化路线

日期：2026-11-19

这份路线图把近期切换 agent、切换模型、切换平台、切换 Mac/NAS/云端宿主时遇到的真实问题，转成三类长期能力：

- **Compass**：在运行时保存上下文、发现偏差、阻止错误记忆进入生产。
- **Assay**：把每个重要结论变成可复算、可挑战、可签名的验证包。
- **组织 Agent**：在开工、切换、交接、收尾时执行统一动作，不靠个人记忆。

原则：**一次迁移事故应当留下一个可复用的守卫；一次验证失败应当留下一个可复算的反例。**

## 总判断

近期暴露的主要问题不是单点技术故障，而是四种连续性没有同时保住：

1. **身份连续性**：用户、项目、任务、工作树和回执没有始终绑定。
2. **状态连续性**：切换 agent 或平台后，下一方不知道准确的版本、边界、失败和下一动作。
3. **证据连续性**：文件搬过去了，但版本、模型、配置、消费者读回和正式验收没有一起搬过去。
4. **因果连续性**：模型输出或自造数据被误当作真实燃料、真实进展或独立验证。

因此，未来目标不是“迁移更快”，而是：**任何系统切换都能证明谁在什么版本上、拿了什么输入、做了什么动作、由谁复核、谁真正消费了结果。**

## 迁移问题到产品能力的映射

| 真实堵点 | Compass 应增加的能力 | Assay 应固定的验收 | 组织 Agent 应形成的动作 | 优先级 |
|---|---|---|---|---|
| 用户→项目→任务映射不可信，跨窗口容易串线 | `context capsule`：用户、项目、工作树、任务和权限的签名上下文；每次 recall/ingest/dispatch 都带 project scope | 身份三元组、scope、task_id、receipt_id 一起进 pack；映射缺失就是 `not_computable` | 开工前读 catalog 和项目合同；没有 project/task 绑定不得写入或发送 | P0 |
| 对话框 active/idle/notLoaded 与真实服务混淆 | 服务、线程、任务、消费者四层状态卡；progress receipt 不依赖聊天窗口刷新 | 每层分别出 health、artifact、consumer 三种证据，禁止一项代替另一项 | 开轮先报“本框身份+验收目标”，收尾写下一动作和证据坐标 | P0 |
| 迁移后工作树、live daemon、CI head_sha 不一致 | release manifest：源码 SHA、live SHA、plist、进程 PID、配置 hash、CI head_sha | pack manifest 必须绑定实际运行版本；未 push 或 head 不匹配直接阻断 | 每轮检查 dirty/ahead、live source hash、CI 是否跑过当前 head | P0 |
| 交接靠长文，历史和下一动作丢失 | 可移植 handoff capsule：主线、边界、失败、证据、下一件；`thread_recall` 与任务状态绑定 | 交接包本身可复算；消费方必须回写 readback | 一轮一件；收尾必写下一件；旧循环不能靠猜测复活 | P0 |
| 切换模型后出现 400/401/429/503、模型名错、渠道路由错 | channel capability registry：模型 ID、协议、思考参数、限额、凭证来源、最近 probe | 每个渠道有 preregistered smoke、负结果和原始响应摘要；不能把 fallback 当成功 | 换模型先做小探针；失败亮牌；不把“配置存在”报成“渠道可用” | P0 |
| NAS/NFS/HF cache/proxy/Tailscale 造成卡死、假在线或层层回退 | topology manifest：本机/loopback/Mac mini/cloud/NAS 的角色和边界；每层单独 health | 连接、模型、文件、消费者四层分别验收；记录 fallback 和超时 | 网络只改一层；先盘点再切换；保留可恢复备份和回滚动作 | P0 |
| 记忆文件搬了，但语义索引污染、旧 distill 倒灌 | source lineage、semantic status、migration watermark、可逆索引闸门 | 每张候选绑定 source/summary/anchors SHA；无 review receipt 不发布 | 原始历史永久保留；迁移后先做 recall regression，再开写入 | P0 |
| 9B 自蒸馏、自引用、模型自评造成因果倒置 | compression subject/verifier 分离；输入来源和模型 hash 固定；递归自指自动拒绝 | frozen split、外部判官、锚点覆盖、三态结果、signed receipt | 小模型只负责压缩，不负责证明自己压缩正确 | P1 |
| Gmail/GitHub/API 出现 HTTP 200 但语义错误、静默忽略参数 | typed adapter + schema checks + second-path probe；把“空结果”当待验证而不是零 | contract test、negative probe、原始响应和复算结果入 pack | 批量端点必须抽样逐条对账；404/0 条先反查对象和口径 | P1 |
| 多个 agent 都在工作，但没有消费侧闭环 | shared evidence bus：任务事件、状态、回执、readback、challenge | verifier 和 consumer 不是同一个自报字段；没有 readback 不能 close | Platform/Agent/V5/Compass 只共享最小投影，不共享未经验证的业务状态 | P1 |
| 外部发布、客户验收、平台提交与本地完成混在一起 | local/live/delivered/accepted 四态模型；对外动作需显式 gate | receipt 的 boundary 写清“内部/外部/客户接受”；失败永久上 wall | 不因本地完成自动触客；发送、部署、结算都保留当前授权和回执 | P1 |
| GPU/配额/存储费用成为隐形阻塞 | paid-resource preflight、lease、预算、checkpoint、stop reason | 资源使用、模型版本、输入输出 hash 和费用/时间一起记录 | 先做本地可复验准备，再申请 GPU；停机和回滚有明确 owner | P1 |
| 修复后没有回归，旧错误通知继续误导 | failure corpus、canary migration、watchdog 和 fresh-head CI | 修复必须带反例、复跑命令、最新 head 和消费者读回 | 过期 CI 通知不作当前事实；每次切换后主动复核新 head | P1 |

## 三条产品主线

### 1. Compass：从记忆服务变成连续性控制面

Compass 下一阶段的核心不是继续堆 recall 功能，而是提供四个稳定对象：

```text
Context Capsule   谁/在哪个项目/哪项任务/什么权限
Evidence Capsule  输入/版本/配置/输出/哈希/失败
Handoff Capsule   当前主线/边界/剩余问题/下一动作
Consumer Receipt  谁真正读取/采用/拒绝了结果
```

所有跨对话和跨平台工具都只消费这些对象的最小投影。这样迁移时搬的是可验证上下文，而不是一堆聊天记录。

### 2. Assay：从成绩验收扩展到迁移验收

Assay 要覆盖的不只是 benchmark 分数，还要覆盖：

- **迁移完整性**：原始文件、manifest、版本、配置、权限和回滚包是否齐全。
- **运行连续性**：服务启动后是否使用了预期代码和模型，是否真正被消费者使用。
- **语义连续性**：迁移前后的 recall、drift、thread 和任务状态是否可复算。
- **组织连续性**：交接方能否在新环境中仅凭 handoff capsule 重现下一动作。

迁移验收至少采用三态：

```text
agree          独立复算通过
disagree       独立复算发现不一致
not_computable  缺输入、权限或消费者证据，不能冒充通过
```

### 3. 组织 Agent：从“会干活”变成“会迁移、会交接、会验收”

每个 agent 角色都要有固定的迁移动作：

**开工前**：读 agent catalog、项目 AGENTS、当前合同、版本和资源账本。  
**切换时**：生成 context capsule、记录旧环境和新环境、跑最小 smoke。  
**执行中**：所有关键动作写 evidence capsule；失败保留原始错误。  
**收尾时**：写 handoff capsule、consumer receipt、下一件；未 push、未验收、未消费不得写 done。  
**复盘后**：把新事故加入 failure corpus 和 Assay criteria，不只写一篇回顾文章。

## 分阶段落地

### P0：先补连续性底座

1. 落地 `context capsule` 和 project/task scope，解决可信用户→项目映射。
2. 把 live source、launchd、daemon、CI head_sha 收进一个 release manifest。
3. 将当前 memory review candidate 改成 VerifyPack + Ed25519 receipt；没有签名回执不发布。
4. 为每个跨对话任务补 consumer readback，解决“做完但没人真正使用”。

### P1：把迁移经验变成可重复测试

1. 建立 migration canary：切换一个 agent、一个模型、一个项目后，自动跑 recall、drift、MCP、权限、CI、readback。
2. 建立 provider/channel failure corpus：模型未知、配额 429、协议 400、认证 401、网关 503、静默 200。
3. 建立 topology manifest：本机、loopback、Mac mini、cloud、NAS 的角色和可回滚路径。
4. 把 GitHub/Gmail/平台 API 的静默成功陷阱写成 adapter contract tests。

### P2：让 9B 和涡轮机制真正进入科学闭环

1. 9B 只做压缩 subject，不做 verifier。
2. 固定训练/验证 split、模型 hash、输入 pack、锚点和独立判官。
3. 只有独立 receipt 通过后，压缩结果才有资格进入 fuel pool 或长期记忆。
4. 对每次压缩做回归：事实保留、时间/路径/数字准确、矛盾不被抹平、递归自指被拒绝。

## 成功标准

这条路线完成后，以下说法都必须能够被机器复算：

- 任意任务都能回答“谁在什么项目、什么版本、什么权限下完成了什么”。
- 任意迁移都能回答“哪些原始材料被保留、哪些语义被重建、哪些尚未验证”。
- 任意模型切换都能回答“新渠道是否真实可用、何时失败、失败是否被误报成成功”。
- 任意记忆发布都能找到 source、criteria、verifier、signature 和 consumer readback。
- 任意失败都不会因为换 agent、换平台或换存储而消失。

当前实物基线：Compass 历史复核正在运行，最近读数为 235/355、6 条候选、0 条正式发布；本路线图不是把这个数字报成完成，而是把它纳入今后的可复算迁移与验收体系。

## 证据入口

- Compass × Assay 能力差距：`docs/assay/COMPASS_ASSAY_GAP_REVIEW_20261119.md`
- Assay 协议：`docs/protocol/ASSAY_PROTOCOL_V0.md`
- 当前服务与复核回执：`runtime/cross-dialog-receipts/20261119-R574.json`
- 当前复核进度：`runtime/scratch_distill_pilot_20261104/semantic-review-progress.json`
- 近期 CI/切换盲区记录：`ci-blindspot-unpushed-cross-dialog-r574-20261119.md`、`ci-lint-regression-r573-20261119.md`
- 迁移与 BGE 宿主记录：`docs/plans/MACMINI_MIGRATION_PACK_20261016.md`、`docs/plans/BGE_HOST_MIGRATION_FIVEQ_20261016.md`
