# Einsia AI 调研:相关性与合作空间 V1(2026-10-08 · R365)

> 用户令"全面搜索调研分析清华 Einsia AI Lab 实验室与我们的相关性和合作空间"。
> 口径:全部公开来源(官网直抓/WebSearch/GitHub API),[实测]/[推断]分层标注。

## 一、对方定谳(是谁)

- **Einsia AI**:2021 年成立,核心团队来自**清华大学与国家级超算中心**(AI 日报播客口径)[推断,单一来源];官网 einsia.ai 直抓[实测]:定位 "Where AI Learns How Experts Work"——proactive agents + frontier benchmarks + open research infrastructure,"one profession at a time"。
- **注意**:不存在"清华 Einsia AI Lab"这一实体——"SIA Lab"是清华 AIR×字节联合中心(撞名易混);Einsia 与清华的关系是**团队渊源+联合研究**(SWE Refactor Bench 为清华联合 Navers Lab 发布)[实测·媒体报道]。
- **旗下实物五件**:
  1. **Vida** — proactive agent("100 use cases by 2026"),未公开[官网自报];
  2. **Einsia for Overleaf** — 科研写作 agent 插件(Overleaf 内)[官网];
  3. **AgentGit**(2026-09 开源,媒体报道"全球首个开源 Agent 会话协作平台")— agent 会话上下文的保存/分享/交接/复用,slogan "Code is cheap, show me your talk"[实测·官网+多源报道];
  4. **Navers Lab** — 其研究臂:Frontier-Eng Bench(47 个**无标准答案**工程任务,2026-05,GPT-5.4 报称最佳)、AI4AI-Bench(arXiv 2608.20318,LLM agent 递归自我改进的算法设计基准)、BrowserBC(浏览器操作轨迹→自然语言技能卡)、PPTBench;
  5. **SWE Refactor Bench**(2026-09,**与清华联合发布**)— 测 C→Rust 迁移是"真重构"还是"刷漆式作弊"——**反作弊评测**同题域[实测·搜狐/新浪财经报道]。
- **GitHub 实况[实测]**:org `Einsia`(Einsia-lab/Einsia-Overleaf-Agent 均 0 star,仓库轻);第三方镜像 SFionaH/AI4AI-Bench、coreyleung-art/OpenChronicle fork(local-first screen-context memory,MCP 暴露)——**开源声量小,媒体声量大**。

## 二、与我们的相关性(五维)

| 维度 | 对方 | 我方 | 判读 |
|---|---|---|---|
| 基准同业 | Navers Lab 出题(47 无标答) | harness 榜+免费 L1 收录+独立判读 | **互补:他们出题,我们判**[推断] |
| 轨迹数据 | AgentGit=会话可存/可交接 | XERJ agent-session-trajectories 包(hub.xerj.org 槽位) | **同空间强共振:会话=一等数据资产**[推断] |
| 反作弊判分 | SWE Refactor 反"刷漆" | 诚信判分/U 态/反自报纪律/预注册 | **同题域,方法论可互引**[推断] |
| 判分器可靠性 | (未见公开) | caliber-bench 元基准 | 我方独有,可补其盲区[推断] |
| 学术渠道 | 清华系+Overleaf 学术生态 | PRECOR 短文/paper 线 | 互引与联发通道[推断] |

## 三、合作空间(三案,按启动成本排序)

- **案 A · 基准互认(最短路径,10/12 后即触)**:邀 Frontier-Eng Bench / SWE Refactor Bench 上我方 harness 榜免费 L1 收录(判据预注册+独立判读);同时向 Navers Lab 提供 caliber-bench 判分器可靠性对照。我方给:独立判读背书;对方给:题源与学术渠道。
- **案 B · 轨迹数据同业**:AgentGit×agent-session-trajectories 格式互认——我方捐赠包可作 AgentGit 生态首个第三方轨迹语料示例;其"会话交接"场景是我方轨迹包的直接消费画像。
- **案 C · 学术线(慢)**:SWE Refactor(清华联合)与我方判分纪律互引;PRECOR 短文引其 Frontier-Eng(47 无标答=判据张力绝佳案例)。

## 四、行动建议

1. **不立即开 issue 撒网**(letta/letta-evals 教训:主仓 landing page 禁 eval 类,先三查);其 GitHub 声量小,触点优先级=官网 contact/邮件 > issue。
2. **时点=10/12 开业后**:届时我方有具体可给之物(榜位/判读卡/判例集),首触以案 A 邀请函形态,开放式不推销。
3. 触前功课:深读 AgentGit repo 会话格式 + Frontier-Eng 判分协议(判分器是谁/可复算性)——判读岗窗口排 10/12 后。
4. 优先级:**中**——非死线件;Einsia 是基准同业里少数"出题方+反作弊同题域"双对口,值得 10/12 后第一封外联。

## 来源

- 官网直抓:https://einsia.ai(产品矩阵/AgentGit slogan/Navers Lab)[实测]
- 媒体: geekpark/zhihu(Frontier-Eng 47 题)/sohu·新浪财经(SWE Refactor 清华联合)/eastmoney·sohu(AgentGit 发布)/Apple Podcasts AI 日报(团队清华+超算渊源)
- GitHub API: org Einsia 仓库/镜像仓[实测]
- 关联:[[external-ledger-v1]] 外联台账新增候选行(10/12 后触)

—— compass · EINSIA-RESEARCH-V1 · R365
