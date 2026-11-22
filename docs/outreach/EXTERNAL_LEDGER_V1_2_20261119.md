# Compass 与 Assay 对外主线台账 V1.2

> 截止时间：2026-11-19（美国东部时间）。Gmail 中模真真最新来信为 2026-11-20 11:57 +0800。
> 本台账只记录已经读到的证据、当前边界和下一动作。邮件与 GitHub 回复均保持草稿状态，未代替用户发送。

## 一、主线目标

Compass 和 Assay 共用一条组织主线，但验收对象不同。

- **Compass** 负责让多个对话框和 agent 能可靠地记住、召回、按项目隔离，并把历史压缩成可复用的经验。
- **Assay** 负责把模型、记忆系统和 agent 的公开声称变成可复算的题包、判据、回执和公开墙。
- **外部闭环** 负责把合作邀请、验证请求、漏洞报告和分发渠道接回来，形成“收到 → 读懂 → 回复 → 实做 → 公开证据”的链路。

北极星仍然是第一次由外部团队正式接受并完成的独立复算。公开发出邀请不等于客户接受，issue 打开不等于复算开始。

## 二、当前状态

| 主线 | 当前结论 | 证据与边界 |
|---|---|---|
| Compass 本地记忆入口 | [实测] 本机 BGE daemon 9876 在跑，V5 本地召回成功，最近一次约 1.9 秒。新写入的外联观察可被 `session_search` 找到，但 BGE semantic recall 对同一新观察连续两次未命中 | 文件写入成功，语义索引的新鲜度仍未验收 |
| Compass 远端项目隔离 | [实测] 8770 三个项目 scope=project 请求均 HTTP 200，但重复请求稳定返回 0 hits | 服务可达，远端记忆命中和历史连续性仍未验收 |
| Compass 权限 | [实测] 当前转发到 8770 的 v14 project 入口在没有 Authorization、X-Tenant-ID、X-User-ID 时仍返回 HTTP 200 和项目记忆摘要。代码签名也没有 `Depends(auth_user)`，写入路径仍未做白名单校验 | 对应安全报告为 P0 未收口事项。可信的“用户→项目”权限映射仍是核心缺口 |
| Assay 协议与工具 | [实测] Assay Protocol v0、VerifyPack、assay-verify、jev-trust 和公开判据文件在仓库中 | 工具存在不等于有外部客户复算 |
| 外部验证请求 | [实测] 六个 GitHub issue 仍开放，均未出现维护者确认。MemOS #2440 已因不活跃关闭 | 目前没有一笔外部复算已完成并被对方接受 |
| 对外合作收口 | [实测] 模真真最新邮件已读，Gmail 已建立回复草稿，未发送 | README 横幅、专稿、横评和赞助仍未承诺 |

## 三、渠道矩阵

| 渠道 | 已读到的事实 | 当前动作 | 责任边界 |
|---|---|---|---|
| GitHub issue/PR | 有开放验证邀请、技术交流和安全披露。六个记忆项目 issue 仍开放 | 先把逐条回复写入 `GITHUB_FOLLOWUP_DRAFTS_20261119.md`，逐条审阅后再发 | GitHub 评论一旦发出无法撤回，必须逐条确认 |
| Gmail | 模真真合作来信、安全报告、mcptry 列表通知、AtomGit 入驻说明和 olud.ai 收录通知均已读 | 模真真已有未发送草稿。安全报告应另起确认草稿。其他邮件进入待办 | 不把收件箱已读当成已回复 |
| HF Discussions | `challenge-2026/challenge_data#2` 已被 owner 关闭，0 条对方回复 | 归档，不重复开新讨论 | 关闭不等于对方接受验证 |
| Discord | 仓库有普通频道和论坛频道发布脚本，历史上有成功回执 | 当前没有本轮新鲜回执，标记为不可验 | 不能用旧截图代替当前渠道状态 |
| dev.to | 当前只读到 Digest，历史台账记录流量低 | 暂不把它列为主投放渠道 | 新文章必须有公网 URL 和回读 |
| X、知乎、小红书、B站、抖音、快手、视频号 | 模真真提出可同步这些账号，当前未收到具体排期或发布链接 | 先索要账号清单、发布形式和专稿大纲 | 没有发布 URL 就不算同步完成 |
| MCP Registry、mcptry、olud.ai | Compass 已被目录收录。mcptry 给出 55/100，olud.ai 给出项目页和 badge | claim、badge 和公开入口放到安全评估之后 | 目录排名和 badge 只证明收录，不证明运行质量 |
| AtomGit/G-Star | GitCode 已回信，要求创建账号、导入仓库、README 标识并提交 G-Star 申请 | 形成清单，等实际账号和导入动作 | 邮件说明不是入驻完成凭证 |
| 飞书/其他私域论坛 | 当前 Codex 工具目录没有可用的飞书连接，本轮没有把飞书状态写成已核对 | 需要在有连接或浏览器会话后单独盘点，保留未核状态 | 不把本地文件或旧会话当成飞书回执 |

## 四、GitHub 外部线程

### 仍开放、值得跟进

| 线程 | 当前读数 | 回复目标 |
|---|---|---|
| [MemTensor/MemOS #2534](https://github.com/MemTensor/MemOS/issues/2534) | 开放，0 条评论 | 确认当前版本、基准工件和配置，邀请对方给出维护者联系人 |
| [supermemoryai/supermemory #1831](https://github.com/supermemoryai/supermemory/issues/1831) | 开放，只有 Linear `ENG-1321` 回链 | 询问 ENG-1321 是否是承接人，避免继续让 issue 无人负责 |
| [Mirix-AI/MIRIX #141](https://github.com/Mirix-AI/MIRIX/issues/141) | 开放，0 条评论 | 询问是否仍需要免费独立复算 |
| [getzep/graphiti #1950](https://github.com/getzep/graphiti/issues/1950) | 开放，0 条评论 | 询问当前版本和可复算入口 |
| [mem0ai/mem0 #7514](https://github.com/mem0ai/mem0/issues/7514) | 开放，0 条评论 | 把实验三臂、数据和交付形式重新压缩成三句话，邀请确认 |
| [xiaowu0162/LongMemEval-V2 #13](https://github.com/xiaowu0162/LongMemEval-V2/issues/13) | 开放，0 条评论 | 提议从一个小型认证 track 开始，先确认维护者是否愿意接收 signed receipt |
| [google-agentic-commerce/a2a-x402 #198](https://github.com/google-agentic-commerce/a2a-x402/issues/198) | 对方提出两项技术问题，线程仍开放 | 补齐 NAU 账本、交付证据和 stake release 的准确口径，已有本地草稿但仍未发 |

### 已关闭或已完成，不再重复追

| 线程 | 结果 |
|---|---|
| MemTensor/MemOS #2440 | 2026-11-14 因不活跃自动关闭，`not planned` |
| vectorize-io/hindsight #5584 | 对方先给过评测许可，之后线程关闭。我们已经留下默认版本和 LongMemEval-S 计划，等待新的入口，不重复 ping 原线程 |
| xerj-org/xerj #1138 | 轨迹包、hub 槽位和 recipes 已完成，对方关闭线程。独立 eval offer 仍可在新 issue 或实际 seed 到位后启动 |
| Th0rgal/orb #1074 | 对方明确说明 Orb/Core 是编排控制面，不是 benchmark harness，礼貌关闭 |
| autonomous-ai/openharness #1300 | 对方回复“Not a task for this project”后关闭，按不匹配归档 |
| OWASP/www-project-agent-memory-guard #35 | 对方确认 `install_guard()` reply-hook 方案已进入 main，属于已采纳成果 |
| alibaba/page-agent #770 | 对方无回复关闭，按收尾类记录，不重开 |
| pydantic/pydantic-ai #14167 | 我方 11-22 17:40Z 所发邀请函（他线/用户所发）。pydanty[bot] 18:07Z 分诊 needs information 并关闭 issue（issue tracker 只收缺陷类）＝婉拒口径，不重开。若需触达 pydantic 生态，改走邮件或 discussions（2026-11-23 R583 终态落档） |

## 五、Gmail 重点事项

### 1. 模真真合作

- 线程：`1a1ec46eb8783d00`
- 最新发件人：`bd@mozhenzhen.com`
- 对方明确愿意推进 README 顶部横幅、项目简介和专稿同步，也提出模型中转站真假与价格横评。
- 我方已经建立 Gmail 草稿：`1a1f721452100358`，仍未发送。
- 已准备我方内容包：`MOZHENZHEN_CONTENT_PACK_20261119.md`，包含中文简介、专稿提纲和横评方法，便于对方回复后直接进入审稿。
- 草稿当前要求对方先提供专稿大纲、横幅和专属链接、媒体账号清单、横评样本和指标、赞助方案。这样可以先验证方法，再决定入口和赞助，不替对方结论背书。

### 2. 安全报告

- 线程：`1a1ab9487dc51507`
- 报告人：Nagizaaz Shaik，2026-11-05 私下发信。
- 报告内容指向 `/v1/v14/recall` 未认证跨项目读取，以及 `/v1/v14/ingest_obs` 的 project 路径逃逸。
- [实测] 当前工作树的 `compass_http_v09.py` 仍能看到这两处风险形态。我们随后用无认证请求验证了 8770 转发入口仍能返回 `nautilus-v5` 项目摘要，没有保存正文。
- 该邮件目前已经读到，但没有找到已发送的确认回函。需要先修复或做临时隔离，再发一封只确认收到和当前处理阶段的回复。

### 3. mcptry 与 olud.ai

- mcptry 给出 Compass 页面分数 55/100，建议公开 `initialize` 和 `tools/list`，以及补充 icon 和 website。公开工具发现与认证边界需要安全评估，不能为了排名直接放宽。
- olud.ai 已建立项目页并提供 badge，声称页面每日重建。claim 和 badge 属于分发动作，排在安全边界核对之后。

### 4. AtomGit/G-Star

- GitCode 已给出明确入驻步骤。当前缺的是账号、镜像导入、README 标识和申请回执，不是材料理解问题。

## 六、下一轮的可验收顺序

1. **P0 安全闭环**。确认远端实际暴露面，盘点 v5 和其他消费者，补认证与项目名白名单，跑负向测试，再给报告人发确认草稿。
2. **P1 模真真回复**。审阅 Gmail 草稿后发送。拿到对方方法、样本和链接后，再决定 README 一个月试点、专稿和横评的具体形式。
3. **P1 GitHub 回收**。一次只回复一条，先从 MemOS #2534、supermemory #1831 和 LongMemEval-V2 #13 开始。每次回复后读回 comment URL，写入台账。
4. **P1 第一笔外部复算**。任何项目确认版本和数据后，冻结 criteria、pack、环境和三态判决，再开跑。没有对方确认就不把本地复现报成客户单。
5. **P2 目录与分发**。安全边界通过后再处理 mcptry claim、olud.ai badge、AtomGit/G-Star、README 横幅和中文媒体同步。

## 七、收口判据

- [实测] 有收件箱或 issue 原文、回复时间、正文和对方回执 URL。
- [实测] 复算有冻结的 criteria、输入包、代码版本、原始输出和独立复核。
- [推断] 只有在证据齐全后，才可以把线程标为“合作进行中”。
- [不可验] 目录排名、邮件打开、issue 打开、历史截图、进程存活都不能代替客户接受或安全修复。
