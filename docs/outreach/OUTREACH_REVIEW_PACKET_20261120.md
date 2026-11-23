# 外部回复审核包 · 2026-11-20

状态：用户已批准。Nagizaaz、模真真、a2a-x402 和六个 GitHub 独立复算邀请已经发送。CodeSense 当前任务协作函仍待确认发送通道。

审核方式：每条可回复线按“批准发送 / 修改后发送 / 分阶段推进”处理。总体口径是积极开放、先建立联系、边合作边补齐证据。已发送内容保留邮件 message ID、线程 ID 或 GitHub comment ID。

发送回执：[20261120-outreach-send-receipts.json](/Users/chunxiao.wang/Projects/nautilus-compass/runtime/org-continuity/20261120-outreach-send-receipts.json)

统一沟通原则：把对方视为潜在合作伙伴和同行朋友，先表达感谢与合作意愿，再共同确定最小可行试点、证据和下一次回读。技术边界用于保护双方复现质量，不用于降低合作热情。

## P0 · Nagizaaz 安全报告

- 渠道：Gmail，线程 `1a1ab9487dc51507`
- 主题：Compass v14 未认证 recall、项目越权和 ingest 路径边界
- 建议动作：**可审核，建议发送积极的协调披露确认函**
- 回复核心
  - 感谢报告并按协调披露处理。
  - 本地 v14 recall 已要求 Bearer JWT 和明确用户到项目映射。
  - `scope=user` 继续关闭。
  - 本地 8097 未认证请求返回 401。
  - 本轮针对性安全测试 26 项通过。
  - 8770 远端探针超时，仍属于部署检查未闭合。
  - 不声称生产环境已经修复，不给出未经验证的部署承诺。
  - 邀请对方继续协助复核部署结果和后续负向测试。
- 审核重点
  - 是否接受“先回事实状态、后补生产验证”的语气。
  - 是否保留“用户到项目映射”作为剩余问题。
- 草稿：[draft_nagizaaz_security_reply_20261120.md](/Users/chunxiao.wang/Projects/nautilus-compass/docs/outreach/draft_nagizaaz_security_reply_20261120.md)
- Gmail 草稿 ID：`1a1f72c912c39a97`

## P1 · 模真真合作

- 渠道：Gmail，线程 `1a1ec46eb8783d00`
- 主题：README 横幅、专稿、媒体矩阵和模型中转站横评
- 建议动作：**可审核，建议发送积极合作确认函**
- 回复核心
  - 同意推进合作。
  - 优先做开发者向专稿和官方媒体同步。
  - README 顶部先做一个月可撤销试点。
  - 横幅、简介、链接、展示位置和统计方式先由对方提供。
  - 横评先确认样本、指标、时间安排、结果展示和赞助方式。
  - 对外内容明确区分实测、推断和无法验证。
- 审核重点
  - 是否接受一个月可撤销 README 试点。
  - 是否把“模型中转站横评”列为第一阶段合作内容。
  - 是否需要补充媒体平台清单或署名要求。
- 草稿：[draft_mozhenzhen_reply_20261119.md](/Users/chunxiao.wang/Projects/nautilus-compass/docs/outreach/draft_mozhenzhen_reply_20261119.md)
- Gmail 草稿 ID：`1a1f721452100358`

## P1 · a2a-x402 #198

- 渠道：GitHub issue
- 对方问题
  - NAU 账本怎样防篡改并保持审计能力。
  - stake/delegate 怎样依据交付证据释放。
- 当前状态：**证据尚未补齐，建议先发合作确认，再分阶段补充技术证据**
- 可以审核的回复方向
  - 感谢提问，并明确表达希望开展联合核对和实现交流。
  - 说明会区分设计文档、当前代码和真实回放。
  - 请求对方提供首选测试账户或 fixture。
  - 约定使用只读 probe 比较两个账本，并提供脱敏 trace。
- 建议首封回复
  - 先确认合作意愿和交流方向。
  - 对当前尚未核实的实现字段保持准确表达。
  - 约定下一封补充代码链接、回放结果和脱敏 trace。
- 当前技术回复仍需保持准确
  - 不能把历史设计文档写成生产保证。
  - 不能宣称 hash chain、atomic settlement、no-revert 已在当前线上路径完整验证。
- 审核重点
  - 建议先发短确认函，再补充实现链接和脱敏 trace。
- 草稿：[draft_a2ax402_198_reply_20261109.md](/Users/chunxiao.wang/Projects/nautilus-compass/docs/outreach/draft_a2ax402_198_reply_20261109.md)

## P1 · 六个独立复算邀请

共同回复原则

- 说明免费独立复算仍然有效。
- 先冻结版本、数据集、配置和判据。
- 结果分为 agree、disagree、not computable。
- 发布命令、原始读数和可复算 receipt。
- 每次只回复一个 issue，发送后保存 comment URL。
- 语气保持友好，明确表达愿意共同冻结配置、共同复算、共同解释结果。

### MemTensor/MemOS #2534

- 审核动作：积极推进合作，邀请对方确认当前 release 和 benchmark owner。
- 需要对方确认当前 release、benchmark artifacts 和公平配置。

### supermemory #1831

- 审核动作：积极跟进并确认 ENG-1321 是否为合作入口。
- 重点确认 Linear `ENG-1321` 是否是当前承接路径。

### MIRIX #141

- 审核动作：积极询问是否仍需要免费复算，并表示可以配合其当前节奏。
- 需要对方给出当前版本、benchmark 和代表性配置。

### Graphiti #1950

- 审核动作：积极跟进，邀请 Graphiti 或 Zep 指定维护入口。
- 需要对方确认 Graphiti 或 Zep 当前维护入口和代表性配置。

### mem0 #7514

- 审核动作：积极重提三臂 write-compression 和 DolphinBench 复算。
- 需要对方确认当前 branch/release、维护者和数据入口。

### LongMemEval-V2 #13

- 审核动作：积极推进小型认证 pilot，并邀请对方共同定义最小范围。
- 需要对方确认 benchmark 版本和 signed receipt 形式。

完整英文草稿：[GITHUB_FOLLOWUP_DRAFTS_20261119.md](/Users/chunxiao.wang/Projects/nautilus-compass/docs/outreach/GITHUB_FOLLOWUP_DRAFTS_20261119.md)

## P0 · CodeSense 平台阻塞反馈

- 渠道：晓天荟聚平台技术支持和 CodeSense 甲方对接人
- 当前状态：**已按当前任务坐标重写为共同排障口吻，待审核**
- 原因
  - 草稿引用的是旧任务 `91237 / 99234145 / 57048066`。
  - 当前主任务正本是 `91240 / 99356508 / 57035605`。
  - 直接发送会把旧试验和当前甲方任务混在一起。
- 草稿中可保留的事实
  - `RewardFileNotFoundError`。
  - `OSS mirror failed`。
  - 平台产物目录没有 reward 文件。
  - 本地 21/21 只能说明本地验证通过。
- 发送前必须补齐
  - 当前任务 ID、子任务 ID、包 ID。
  - 当前平台回执和甲方拒收返修记录。
  - 是否继续使用旧任务作为历史案例。
- 当前建议
  - 使用当前任务坐标重写版。
  - 以共同定位 reward 链、artifact 回传和受控复验为主线。
  - 保留本地 21/21 作为辅助证据，不写成平台验收。
- 当前草稿：[CODESENSE_CURRENT_PLATFORM_COOPERATION_DRAFT_20261120.md](/Users/chunxiao.wang/Projects/nautilus-core/ops/ali_phase2/CODESENSE_CURRENT_PLATFORM_COOPERATION_DRAFT_20261120.md)
- 旧草稿：[CODESENSE_PLATFORM_BLOCKER_DRAFT_20261119.md](/Users/chunxiao.wang/Projects/nautilus-core/ops/ali_phase2/CODESENSE_PLATFORM_BLOCKER_DRAFT_20261119.md)

## 暂不新增回复的条线

### 数聚变

- 已发送 p1-3 任务边界和来源确认请求。
- 当前等待 manifest。
- 暂不重复追函，收到后直接进入 Gate A 链路。

### Platform 治理父任务

- 父任务 `v7tk_1795190863904` 和两个子任务已经入队。
- 当前等待结构化 receipt。
- 暂无新的外部回复动作。

### Flywheel verifier 和压缩线

- 属于内部技术验证。
- 当前没有外部回复动作。

### Venture r4

- 当前为 `review_pending/revise`。
- 先完成内容复审，再考虑对外发布或预览。

## 审核顺序建议

1. Nagizaaz 安全协调函。
2. 模真真合作回复。
3. a2a-x402 #198 合作确认函。
4. CodeSense 当前任务共同排障函。
5. 六个 GitHub 独立复算邀请逐条确认。

