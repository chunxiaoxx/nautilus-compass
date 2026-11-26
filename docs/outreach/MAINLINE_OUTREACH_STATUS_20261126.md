# 主线与对外联系当前状态 · 2026-11-26

> 本快照把主线正本、当前工作树和外部渠道回执放到同一坐标系中。它只记录读回结果，不代表已经发送新的邮件、评论或平台函件。
>
> 观测时间为 2026-11-26 03:20 EST。外部邮箱和 GitHub 使用只读连接器读取。历史审核包仍保留，当前状态以本文件和各自的原始回执为准。

## 一、这一轮的验收目标

- 把 Compass 主线收敛到一个可验证的下一动作。
- 区分外部对接中的已回执、只保留在本地的草稿和仍未得到对方接住的主动邀请。
- 保留停止门、版本门和发布边界，不把服务存活或分发上架写成客户验收。

## 二、主线状态

### 北极星

主线正本把北极星定义为首个外部主动复算请求，战略顺序是开业零瑕疵、首个真实客户单与首次外部复算、装订线开张。[实测] 本轮找到了一次已经完成的外部只读账本复算，但它属于 A2A 结算账本合作，不是记忆基准客户单，也没有形成 Compass 的付费交付或客户验收。首个外部记忆基准复算仍未闭合。

证据坐标为 `docs/soul/MAINLINE_ROADMAP_20261101.md`、`docs/soul/mainline_architecture_20261004.md` 和 GitHub `google-agentic-commerce/a2a-x402#198`。

### 记忆与验证能力

- **M5 记忆门**　[实测] 直接向 `127.0.0.1:9876` 发送 `{"action":"ping"}` 返回 `pong=true`，当前 PID 为 2285，daemon 源哈希前缀为 `bf52cf66`，重排端点为 `127.0.0.1:8401`。这证明传输层可响应，不替代召回质量或消费者验收。
- **停止边界**　[实测] `python3 runtime/loop/stop_gate.py --json` 返回 `blocked=true`。canonical round 为 589，local round 为 207，production round 为 1267，均超过硬停阈值 200。当前不应继续启动值守轮、读队列或写循环状态。
- **验证产品**　[推断] assay、jev、VerifyPack 的下一瓶颈已经从“是否存在”转为“是否有外部版本、数据、判据和非实现者回读”。本轮 A2A 复算证明只读核验路径可用，但没有替代记忆基准试点。
- **发布门**　[实测] 取证时基线 HEAD 为 `ae9ab1ba30a74b3502fed4c5505ad6a49d8fe038`，本地领先 `origin/main` 43 个提交，工作树有 13 个既有运行态改动。本快照及其基线修订随后以 `3b4816c6`、`6de39c53` 归档。`runtime/release/compass-3.4.0-readiness-20261123.json` 是 11 月 24 日快照，记录的 3.4.0 元数据对齐、完整测试、构建、全新安装、canary、客户验收和 CodeSense R25 平台前置验证仍未闭合。该快照早于当前 HEAD，不能直接当作当前构建结果。
- **连续性门**　[实测] `runtime/org-continuity/codesense-91240-core-cognition-capsule-20261123.json` 记录的 `source_head` 仍为 `8606fdb4`，已经落后当前 HEAD。其 `assay_signature` 为 `not_signed`，`consumer_readback` 为 `pending`。这是一项待补的交接一致性问题，不能把 capsule 当作当前 HEAD 的完整证明。

### 主线判断

[推断] 现在最有价值的动作不是继续增加通用宣传入口，而是冻结一个外部试点的版本、数据、配置和三态判据，再取得对方或独立消费者的回读。A2A #198 已有对方和可读 fixture，最接近小范围试点。MemOS、Supermemory、LongMemEval 仍是更符合 Compass 记忆验证主线的候选，但本轮没有维护者接住。

## 三、对外联系与对接

### 已形成外部闭环

#### Nagizaaz 安全报告

- [实测] Gmail 线程 `1a1ab9487dc51507` 的最新来信为 2026-11-23。报告人阅读了 commit `17e89e78`，确认 `auth_user`、用户到项目映射、`scope=user` 限定和路径穿越过滤符合报告要求，并给出两条部署侧负向检查。对方明确写明将报告视为 resolved，同时询问是否发布 advisory 并署名 Nagizaaz Shaik。
- [实测] GitHub `chunxiaoxx/nautilus-compass#66` 已关闭，最新公开状态更新为 fixed and deployed。
- [实测] 通过本机 SSH 转发的 `127.0.0.1:8770` 对无 Authorization 的 `GET /v1/v14/recall?q=security-probe&scope=user` 返回 HTTP 401，响应体哈希为 `c170a99d754276f25c9ee9be950e78a35e63d48c500cb43f993c78f37d19d92f`，响应正文为 Bearer JWT required。伪造的 `X-Tenant-ID` 没有绕过鉴权。
- [不可验] 本机没有 `~/.config/compass/v14_bridge_auth_header`，本轮没有刷新或生成凭据，因此尚未执行“有效 token + 路径穿越 project”那条 403 与无逃逸文件探针。报告人已接受修复与当前生产环境两条负向检查仍需分开记录。
- 下一步应在已有授权凭据可读时完成第二条探针，再决定 advisory 和署名口径，暂不发送新的确认函。

#### A2A settlement 对接

- [实测] GitHub `google-agentic-commerce/a2a-x402#198` 仍 open，13 条评论，最近更新时间为 2026-11-24。双方已经完成只读 `settlement.ledger` 复算，t1、t2 摘要重算与链式前驱检查均有记录，对方承认外部复算并询问联合只读 pilot 的时间表。
- [实测] 当前线程里的最后一条我方评论已经把 check #4 标记为我方 closed，并说明历史条目的 `ts=null` 边界。此线程已经具备版本、fixture、方法和回读坐标，适合整理成最小试点包。
- 下一步是内部冻结 pilot 包和验收字段，未获新的发送授权前不追加评论。

### 有明确新动作但尚未形成可发送草稿

#### 模真真合作

- [实测] Gmail 线程 `1a1ec46eb8783d00` 的最新未读来信为 2026-11-26。对方询问团队是否看过完整合作材料，邀请先提供常用模型清单，以便生成专属链接并安排专稿初稿和一个月试点。
- [实测] 合作内容包括开发者专稿、官方媒体矩阵、README 顶部横幅与简介，以及可选的模型渠道横评。它属于潜在分发和合作线，不等于验证客户单。
- [实测] Gmail 当前草稿列表和 `in:drafts mozhenzhen` 查询均未发现对应的 Gmail 草稿。仓内 `docs/outreach/draft_mozhenzhen_reply_20261123.md` 只是本地文件，不能写成已经进入邮箱待发。
- 下一步需要先在本地确定模型清单、试点链接位置、可撤销条件和统计口径，再由用户决定是否回复。

### 已发出但尚未被维护者接住的独立复算邀请

- **MemTensor/MemOS #2534**　[实测] open，1 条评论且来自 `chunxiaoxx`，没有维护者回复。需要对方给出当前 release、benchmark artifacts 和公平配置。
- **supermemoryai/supermemory #1831**　[实测] open，2 条评论分别为 Linear linkback 和 `chunxiaoxx` 跟进，没有维护者技术回复。现有承接线索是 `ENG-1321`。
- **xiaowu0162/LongMemEval-V2 #13**　[实测] open，1 条评论且来自 `chunxiaoxx`，没有维护者回复。需要对方确认 benchmark 版本和 signed receipt 形式。
- [不可验] MIRIX、Graphiti、mem0 等历史审核包中的其余 issue 本轮没有重新读回，不把旧包的 open 或 closed 状态当作当前状态。

### 分发与生态入口

- **AtomGit / G-Star**　[实测] Gmail 线程 `1a19af3855127e5a` 有 2026-11-02 的未读入驻指南。当前没有本轮读回的账号创建、项目导入、镜像同步或 G-Star receipt。
- **mcptry**　[实测] 2026-11-19 来信确认 Nautilus Compass Memory 已被列入目录。目录排名和检查结果属于分发证据，不等于运行质量、客户使用或付费转化。
- **olud.ai**　[实测] 2026-11-01 来信确认项目被收录。它同样只证明目录分发。

## 四、历史材料的纠偏

`docs/outreach/OUTREACH_REVIEW_PACKET_20261120.md` 是历史审批包。它写入的 Gmail 草稿 ID 和“已发送”语气不能覆盖本轮 Gmail 只读结果。当前对外事实以原始 Gmail message/thread、GitHub issue/comment 和本快照中的证据坐标为准。

## 五、本轮结论与唯一下一项

- [实测] 安全报告已得到报告人源码级确认，本机转发的匿名边界返回 401，A2A 已形成一次外部只读复算，模真真正在追要合作输入。
- [推断] Compass 主线的关键缺口仍是首个外部记忆基准复算与可回读的客户交付。通用曝光已经有入口，维护者接单和冻结试点仍未发生。
- [不可验] 当前 3.4.0 全量构建、有效 token 路径穿越负向探针和消费者读回尚未在本轮独立完成。

**唯一下一项**　取得已有授权凭据的只读来源后完成第二条安全探针，保存 403 与无逃逸文件证据。完成后再把 A2A 试点包和模真真合作输入分别整理成可审核草稿，不在本轮自动发送。
