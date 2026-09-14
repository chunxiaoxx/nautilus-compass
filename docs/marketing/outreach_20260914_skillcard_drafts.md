# 技能卡投放物料 · 三份草稿(2026-09-14 · 待用户过目,不直接发)

> 方案正本:ecosystem_gtm_plan_20260914.md §三 · 技能卡本体已落仓:
> `skills/nautilus-compass-memory/SKILL.md`(英主双)+ `SKILL.zh-CN.md`(中主双)。
> 本档三份物料**全部是草稿**,过目通过、且各前置条件满足后才发。

## 投放前统一红线(逐条过)

- [ ] 正文=使用文档不是广告;「共创 AGI」不出现在任何投放正文(README 才有)
- [ ] 对外数字只出 sealed 集(0.754/0.700 e2e 等);**81.6% 不出口**;无脚本可复现的数字不出口
- [ ] 正文尽量不出现跑分(技能卡已按此写;讨论帖收尾用统一钩子问句代替自夸数字)
- [ ] 每渠道真实身份、不复制粘贴同文(三份物料角度已错开)
- [ ] GitHub API 用 `gh auth token` 取 token(PR 创建配方 9/14 已验证)
- [ ] 发布后 48h 无回响不追发;台账回写 community_engagement_log.md

---

## 草稿一 · awesome-openclaw-skills-zh PR(clawdbot-ai/awesome-openclaw-skills-zh)

**投放前侦察结论(9/14 实拉 README)**:该仓是 fork(上游
poiuyaaaa/awesome-moltbot-skills-zh),内容=ClawHub 官方技能库的中文翻译
**按下载量倒序 Top 100×7 分类自动同步**,行链接全部指向 `ClawHub/<name>`。
我们的技能不在 ClawHub 上——直接加行会偏离其收录口径。

**🔴 前置决策(用户二选一)**:

- **A1 · 先发 ClawHub(推荐)**:技能卡本体即发布单元,
  `npx clawhub publish skills/nautilus-compass-memory`(需先在 clawhub.com
  注册,用户账号操作)。发布后 `npx clawhub install nautilus-compass-memory`
  自然可用,awesome 表格行链接 `ClawHub/nautilus-compass-memory` 才名实相符,
  且顺带拿到 ClawHub 分发渠道(比 awesome 列表本身大)。
- **A2 · 直接 PR 加行(备选)**:链接给 GitHub 仓,PR 正文坦白"非 ClawHub
  同步来源,社区自发布;如不符合收录范围请直接关闭"。被拒即收,不二投。

**拟加表格行**(分类:🤖 AI 智能;排序说明:该表按下载量倒序,新技能
0 下载,建议行放表尾或由维护者另设「社区补充」段,PR 里写明听维护者安排):

```
| — | Compass 记忆 | nautilus-compass-memory | ClawHub/nautilus-compass-memory | 本地优先智能体长期记忆(MCP)。写入零 LLM 调用、数据不出机器;读取混合召回+漂移检测防重复犯错;所有对外数字附 sha256 清单+字节复算+ed25519 签名证据包。 |
```

(A2 备选行:链接列改 `github.com/chunxiaoxx/nautilus-compass`)

**PR 标题**:`feat: 补充技能条目 nautilus-compass-memory(本地优先记忆 · 可验证声明)`

**PR 正文草稿**:

> 新增一个记忆类技能条目。
>
> nautilus-compass-memory 是本地优先的智能体长期记忆(MCP):写入路径零
> LLM 调用(纯本地 BGE-m3,数据不出机器),读取时语义+关键词混合召回,
> 另带漂移检测(对照真实失败模式锚点集,防"同样的错误犯第二遍")。
>
> 它与表内现有记忆技能的差别在**可验证性**:对外公布的每个数字都以
> sha256 清单+字节级复算+ed25519 签名回执的证据包发布,两条纯标准库命令
> 即可独立复核(不信任作者也能验)。技能卡正文即使用文档:
> https://github.com/chunxiaoxx/nautilus-compass/blob/main/skills/nautilus-compass-memory/SKILL.zh-CN.md
>
> 排序位置按贵仓规则应由维护者定(新技能无下载量,放表尾即可)。
> 若收录口径仅限 ClawHub 官方同步来源,本条不符合,关闭即可,感谢。

---

## 草稿二 · WorkBuddyGuide 案例投稿(AlephAITech/WorkBuddyGuide)

**投放前侦察结论(9/14 实拉 README)**:该仓是 VitePress 站(workbuddy.homes),
收录=**真实案例投稿制**:`docs/cases/submissions/<独立目录>/` + 七段
CASE_TEMPLATE(场景与问题/使用的 Skill/任务描述/执行过程/实际效果/验收标准),
走 Case PR 模板;明确要求"实际效果:使用截图或其他结果证明"。

**🔴 前置条件(硬)**:必须先在 WorkBuddy 里**真实跑通一次** compass MCP 并
截图。下列草稿的「实际效果」段是占位——不编造,不拿别的环境截图充数。
建议最小真跑流程(约 15 分钟):WorkBuddy 装 MCP(指向
`python ~/.claude/plugins/nautilus-compass/mcp_server.py` 或云端端点)→
会话 A 让它记住一个项目决策 → 开会话 B 问同一问题验证召回 → 截两图。

**投稿目录**:`docs/cases/submissions/nautilus-compass-memory/`

**案例正文草稿**(按其七段模板):

> ### 场景与问题
>
> 一人 + AI 的多会话开发:周一在会话里定好的项目规范、踩过的坑、配置
> 口径,周四新开会话全部归零——要么重新解释一遍,要么 AI 按旧理解把
> 错误重犯一次。聊天记录搜索救不了语义改写,人工笔记又没人维护。
>
> ### 使用的 Skill
>
> - **作用**:本地优先长期记忆 MCP 服务器(写入零 LLM 调用,数据不出
>   机器;读取混合召回;漂移检测在每次提问前对照历史失败模式)。
> - **来源**:开源 github.com/chunxiaoxx/nautilus-compass(Modified MIT,
>   亦有 PyPI 包 `nautilus-compass` 与云托管自助版)。
> - **安装**:
>   ```bash
>   git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
>   bash ~/.claude/plugins/nautilus-compass/install.sh
>   bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
>   ```
>   在 WorkBuddy 的 MCP 配置中添加该服务器(command: python,
>   args: `~/.claude/plugins/nautilus-compass/mcp_server.py`)。
> - **必要配置**:无(默认本地运行;如用云托管改为
>   `https://compass.nautilus.social/mcp/` + Bearer token)。
>
> ### 任务描述
>
> 会话 A(周一):「记一下:这个项目的依赖升级必须走
> `--no-isolation` 构建,上次不带这个参数构建直接失败;另外测试出口码
> 会被管道吃掉,验证必须看实际输出。」
> 会话 B(周四,全新会话):「帮我把依赖升到最新版。」——不重复交代背景。
>
> ### 执行过程
>
> 1. daemon 后台常驻(开机一次);MCP 服务器按需拉起。
> 2. 会话 A 的决策经 `ingest_obs` 落为本地向量记忆。
> 3. 会话 B 提问时,`recall` 混合召回命中周一条目并注入上下文;
>     若提问模式贴近历史失败锚点,`drift_check` 先行告警。
> 4. 权限与安全边界:全部数据留在本机;云托管版按用户隔离 + scoped
>     token(默认只读本项目)。
>
> ### 实际效果
>
> [🔴 占位:待 WorkBuddy 真跑截图——会话 B 未被告知任何背景,回答中
> 直接引用了周一的构建参数与验证口径;附 drift 告警一例(如有)]
>
> ### 验收标准
>
> - 新会话零背景交代下,能答出 N 天前的具体决策细节(不是泛泛而谈)
> - 关机重启后记忆仍在(本地持久化)
> - 数据不出机器(可用抓包/日志佐证)
> - 可验证性:项目对外数字有 sha256+签名证据包,两条标准库命令可复核

---

## 草稿三 · OpenClaw discussions 帖(使用文档体)

**前置**:确认讨论区入口(OpenClaw 官方仓 Discussions,发前定 URL;
选 Showcase / Show and tell 类目)。标题发布后不可改,定稿再发。

**标题(候选,定一)**:
`nautilus-compass-memory — local-first agent memory where every published number is byte-verifiable`

**正文草稿**:

> Sharing a skill card + MCP server we built for a problem we kept hitting:
> session memory that dies with the session, and memory layers whose
> benchmarks you just have to trust.
>
> **What it is.** Local-first long-term memory for agents over MCP. Zero LLM
> calls at write time — raw text embedded locally with BGE-m3, no data leaves
> the machine. Read time does hybrid semantic + keyword recall, plus drift
> detection: every prompt is scored against an anchor set of real failure
> patterns before the agent acts (the "stop repeating that mistake" half).
>
> **Connect in ~3 minutes** (Claude Code / Cursor / Cline / Continue / Zed /
> any MCP client):
>
> ```bash
> git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
> bash ~/.claude/plugins/nautilus-compass/install.sh
> bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
> ```
>
> Hosted option (self-serve, no local model): `https://compass.nautilus.social/mcp/`
> with a scoped Bearer token.
>
> **The part we care about most — verify, don't trust.** Every number this
> project publishes ships as a sealed evidence pack: sha256 manifest, claims
> recomputable from payload bytes, ed25519-signed receipt. Two stdlib-only
> commands:
>
> ```bash
> git clone https://github.com/chunxiaoxx/nautilus-compass && cd nautilus-compass
> python -m tools.verifypack verify runtime/verifypack/arma_summary/pack --out /tmp/my_receipt.json
> python -m tools.verifypack check runtime/verifypack/arma_summary/pack \
>   --receipt runtime/verifypack/arma_summary/pack/receipts/receipt.json \
>   --pubkey f7554b8709b7fe36f5a63e7f76cf2a31f827aee5724ff8dd4f11772d1aa3e8be
> ```
>
> The Reproducibility Wall publishes contradicting numbers with the same
> prominence as favorable ones — bring your own key, sign your own receipt,
> that entry outranks any self-report.
>
> Skill card (drop-in, OpenClaw-compatible SKILL.md, bilingual):
> https://github.com/chunxiaoxx/nautilus-compass/tree/main/skills/nautilus-compass-memory
>
> Closing question, genuinely asked: every number we publish is a
> sha256-manifested, byte-recomputable, signed evidence pack — would your
> memory layer survive that bar?
>
> (If it matters to anyone: Chinese README here —
> github.com/chunxiaoxx/nautilus-compass/blob/main/README.zh-CN.md)

---

## 发放顺序建议(供用户参考)

1. **先 A1(ClawHub publish)**——它让 A2 的表格行名实相符,也让技能可
   `npx clawhub install`,是三件里唯一"发了就有永久分发面"的动作。
2. 草稿三(讨论帖)引用技能卡与 ClawHub 条目,放 A1 后发最顺。
3. 草稿二(WorkBuddy 案例)受真跑前置约束,最后发。
