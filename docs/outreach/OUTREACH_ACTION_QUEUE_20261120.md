# 外联推进队列 · 2026-11-20

状态口径：用户已批准全部审核项。Nagizaaz、模真真、a2a-x402 和六个 GitHub 独立复算邀请已经按积极合作口径发送。CodeSense 当前任务协作函已通过 Platform 内部信箱转交，等待平台/甲方外部路由回执。统一采用积极开放、对外皆师友、共同复现和分阶段合作的口径。

发送回执：[20261120-outreach-send-receipts.json](/Users/chunxiao.wang/Projects/nautilus-compass/runtime/org-continuity/20261120-outreach-send-receipts.json)

## P0 · 安全报告确认

### Nagizaaz Shaik · Compass v14 安全报告

- 渠道：Gmail，线程 `1a1ab9487dc51507`
- 报告：未认证的跨项目 recall 读取，以及 ingest_obs 的 project 路径逃逸
- 当前状态：[实测] Gmail 已发送，message `1a1f9e74735155a1`，thread `1a1ab9487dc51507`
- 处理边界：先完成 v14 认证、项目名白名单、负向测试和部署暴露面核对，再发修复状态。没有把“收到报告”写成“漏洞已修复”。
- 证据：`docs/outreach/draft_nagizaaz_security_reply_20261120.md`、Gmail draft `1a1f72c912c39a97`

## P1 · 已有明确合作窗口

### 模真真 · README、专稿、媒体矩阵、横评

- 渠道：Gmail，线程 `1a1ec46eb8783d00`
- 对方最新来信：[实测] 2026-11-20 11:57 +0800，明确表示可按 README 顶部横幅、简介、专稿和媒体矩阵推进，并询问我方最希望得到哪类支持。
- 当前状态：[实测] Gmail 已发送，message `1a1f9e74c70b070a`，thread `1a1ec46eb8783d00`
- 草稿请求对方先提供专稿大纲、横幅、专属链接、媒体账号清单、横评指标和赞助方案。收到后再做内容审阅和可撤销入口试点。
- 证据：`docs/outreach/draft_mozhenzhen_reply_20261119.md`、`docs/outreach/MOZHENZHEN_CONTENT_PACK_20261119.md`

### google-agentic-commerce/a2a-x402 #198

- 渠道：GitHub issue
- 对方问题：[实测] 2026-11-09 询问 NAU 账本如何保持防篡改和可审计，以及 stake/delegate 释放前如何验证交付。
- 当前状态：[实测] 已发送积极合作确认，GitHub comment `7045584975`。
- 草稿：`docs/outreach/GITHUB_FOLLOWUP_DRAFTS_20261119.md` 中已有英文版本。
- 发送前依赖：必须先从当前平台实现读取真实账本和交付验证机制，补齐实现链接和脱敏 trace，避免把设计意图写成生产保证。

## P1 · 六个独立复算邀请

以下线程仍开放，已完成逐条积极跟进。对应英文草稿保留在 `docs/outreach/GITHUB_FOLLOWUP_DRAFTS_20261119.md`。

| 线程 | 当前状态 | 回复目的 |
|---|---|---|
| MemTensor/MemOS #2534 | 开放，0 评论 | 请求当前版本、基准工件和公平配置 |
| supermemory/supermemory #1831 | 开放，已有 Linear ENG-1321 回链 | 确认 ENG-1321 是否为承接路径 |
| Mirix-AI/MIRIX #141 | 开放，0 评论 | 询问是否仍需要免费独立复算 |
| getzep/graphiti #1950 | 开放，0 评论 | 请求当前版本和代表性配置 |
| mem0ai/mem0 #7514 | 开放，0 评论 | 重提三臂压缩实验和 DolphinBench 复算 |
| xiaowu0162/LongMemEval-V2 #13 | 开放，0 评论 | 提议小型认证 pilot 和 signed receipt |

[实测] 六条邀请均已逐条发送，并完成评论回读。MIRIX、mem0、LongMemEval-V2 通过 gh CLI 补发，原因是 GitHub connector 返回 403。

## P2 · 暂不重开

- MemTensor/MemOS #2440：不活跃关闭
- Hindsight #5584：已有评测许可，原线程关闭，等待新入口
- XERJ #1138：轨迹包、hub 槽位和 recipes 已完成
- Orb #1074：对方明确不属于 benchmark harness
- openharness #1300：对方明确不属于该项目
- OWASP agent-memory-guard #35：reply-hook 方案已被采纳
- HF challenge_data #2：数据集 owner 已关闭，0 条回复

## 审阅闸

1. Nagizaaz 和模真真邮件已发送，等待回信。
2. a2a-x402 #198 已发送合作确认，等待对方提供 fixture 或回复。
3. 六个独立复算邀请已逐条发送，等待维护者回应。
4. CodeSense 当前任务协作函仍需确认平台/甲方发送通道。
