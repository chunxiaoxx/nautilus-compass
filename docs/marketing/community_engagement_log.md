# 社区互动台账(dev.to + GitHub · 2026-09-08 起)

> 纪律:真实身份、每 repo/作者每天 ≤1-2 条、技术价值优先、链接只在自然相关时给、
> 不在 bug issue 推销、不复制粘贴同文刷帖(=spam 举报+封号风险)。质量>数量。

## 已发布

| 时间 | 平台 | 位置 | 角度 | 链接 |
|---|---|---|---|---|
| 9/8 深夜 | GitHub | mem0 #7260(rate limit 缺失) | 写侧零 LLM=架构级止血+scoped token+探针开源 | issuecomment-5587908156 |
| 9/8 深夜 | GitHub | MemOS #2345(本地嵌入源) | HF_HUB_OFFLINE 配方+BGE-m3 vs 小模型实测 | issuecomment-5587909009 |
| 9/8 23:3x | dev.to | 4602572(mateo_ruiz 评论) | 两层检测+反问未声明失败模式 | ⏳ 草稿待用户网页贴(API 端点 404) |
| 9/9 凌晨 | Gmail | **Trajko 回复**(sorovince@gmail.com) | 见 seeds 段 | 1a081c3beb4e3281 |

## Seeds 名单(优先维护:点名致谢/优先回复/进 issues 讨论)

1. **Trajko**(sorovince@gmail.com)——9/4 主动来信,Hivemind 量化平台架构师(4 agent 团队/7471 自检/OOS Sharpe +0.87),Operator Skepticism Protocol 作者,自荐 drift/评测方向合作(附简历)。9/9 已回:数字更新(0.890 vs 0.774 反超)+试用邀请+Reproducibility Wall 首位邀请+合作口径(无席位,开源协作为先)。**跟踪:48h 内若回→深聊;quant 场景是好用例。**

## dev.to 评论草稿队列(用户批量贴,每条 20 秒)

1. **4599143**(Mem0 实操教程 @mukesh_13,9/7):
> Nice walkthrough. One data point for the pruning/extraction tradeoff: we ran extraction-based (mem0 2.0.19) vs no-extraction (verbatim + local embedding, intelligence at read time) head-to-head on LongMemEval-S retrieval, full 500 — extraction lost on retrieval accuracy (0.774 vs 0.890 P@1) and adds a paid LLM call per write. Worth benchmarking pruning aggressiveness against no-prune-verbatim before committing.

2. **4584021**(「Memory is the Part That's Real」 @mukesh_13,9/5):
> Agreed — and the under-discussed half is judging whether memory actually helps. We caught our own AI judge failing silently 5 times during one 500-question eval (14.2% of answers mislabeled). Cross-harness numbers in this space mostly aren't comparable; judge hygiene is the missing foundation.

3. **4579358**(选型指南 @realmrmemory,9/5):
> For the comparison matrix: one school worth adding is no-extraction/local-first — verbatim storage, local embedding, retrieval intelligence at read time (BM25+dense fusion, question-type routing). Cheaper to run (zero LLM at write) and in our head-to-head it beat extraction on retrieval accuracy.

4. **4486125**(ContextForge vs Mem0 vs Zep @alfredoizjr,8/25):
> Useful roundup. If you do a follow-up: same-questions-same-criteria head-to-heads with published scripts are what actually move this space — self-reported numbers from different harnesses aren't comparable. We publish ours (including failed experiments), ~$3.50 to re-run.

5. **4607317**(MCP Memory Server 选型 @mind_anthony,9/8):
> Good overview. One axis often missing from these roundups: write-path cost & privacy — whether the memory layer calls an LLM/cloud on every write, or stays fully local. It changes both the egress profile and running cost dramatically.

6. **4602572**(Procrastinating/意图-行动差距 @IT Path Solutions,9/10 收到·用户转):
> This distinction is the right one — and it's sharper than our post. We framed the intention-action gap as an evaluation problem; you're pointing at the layer below it: progress detection. A rewritten plan is a log event. State changing is an event in the world. Confusing the two is how an agent looks busy forever.

> Two examples from this same project. Our local memory daemon kept passing "is it running?" checks — process alive, port listening — while a stale instance accepted connections and answered nothing. The liveness signal said healthy; the state-based probe (a real round-trip that required a response) said half-dead. And we now preregister pass/fail gates before eval runs — explicit failure conditions, in your state-machine sense — because an agent (or a team) will otherwise negotiate the definition of progress after seeing the result.

> The version we landed on for claims themselves: every "this changed" carries a content hash and a signed receipt, so "state actually moved" is verifiable in bytes rather than narrative. Your framing generalizes that from claims to agent loops. Worth a follow-up post — thanks.
>
> (repo 在回复尾部自然带一次即可:github.com/chunxiaoxx/nautilus-compass)

## GitHub 互动目标池(gh CLI 可直接发,每轮挑 1-2 个)

- mem0/Letta/Zep/MemOS/Cognee 的 **discussions**(评测/选型类,非 bug)——GraphQL 拉取待接
- 新 fresh issue 里 security/scoring 类(有真经验的才评)
- 我方 repo:issue 24h SLA · Reproducibility Wall PR 照登

## 密度目标(用户 9/8 拍板:加大)

- dev.to:发文从周 2-3 提到**隔日更**(素材:判分卫生学/失败实验系列/130 天舰队故事/白皮书拆章);评论每天 3-5 条新鲜相关帖
- GitHub:评论每天 2-3 条目标池;follow-ups(有人回复继续聊)

## 2026-09-10 21:36 (dev.to v3 主帖发布)

- **动作**: 草稿 4621352 翻转发布(PUT 200 → GET 复验 published_at=2026-09-10T13:36:53Z)
- **URL**: https://dev.to/chunxiaoxx/we-beat-mem0-on-longmemeval-s-retrieval-116pt-p1-full-500-with-a-fully-local-memory-layer--2i35
- **title**: We beat mem0 on LongMemEval-S retrieval (+11.6pt P@1, full 500) with a fully local memory layer — no LLM at write time(发布后锁死,勿再动)
- **tags**: ai,llm,opensource,machinelearning · ai_disclosure=fully_autonomous
- **正文要点**: 表格对打 0.890/0.774 · Sealed not claimed 段(verify 命令内联)· 81.6% 不入包坦白 · 94.4% 口径 caveat
- **同日 GitHub 资产配套**: v3.2.0 Release + Profile README + Discussions #56/#57(verify 链接全部可解析——44 commit 已推,不再是死链)
- **值守**: 1-2h 内查 views/评论;评论模板在 launch_plan §6

## 2026-09-11 巡检(Gmail/dev.to/GitHub/HN 全景)

- **Gmail**:Trajko 9/10 回信=礼貌 ack 无行动(链路收尾,不再触达);「雷鸣云」vzykyv@gmx.com=推广服务推销(spam 不回);Reddit Pro 关键词追踪通知(u/Nautilus-compass 监听 "Nautilus",本周 1 条新对话可看)
- **dev.to v3 主帖**:26 views/1 reaction/2 评论——@ahmetozel 高质量技术评论(write-time bet 论点共鸣),回复草稿见下;另一条 tinu.be spam
- **GitHub**:stars 19;CI 连红 4 commit(根因=verify_batch001_recheck.py unused import,已修);punkpeye #14065 open 等 merge;Discussions #56/#57 无新回复
- **HN**:49641875 仍埋,无变化
- **API 判死两路**:dev.to POST /api/comments(V0/V1 均 404,端点已废→评论网页贴);第三方仓 PR 创建(anti-abuse 超 24h 未解→网页一键)

### 回复草稿(@ahmetozel · 待用户网页贴,dev.to API 已废)

@ahmetozel thanks — that's exactly the failure mode that pushed us this way. The strongest version of it we hit: even *within* "facts", what looked like the right granularity at write time turned out wrong at read time. Retrieving whole sessions for user-utterance questions capped that type's P@1 at 0.20; switching to turn-level chunks (sliding window of 2) for that question type alone took it to 1.00 — and we could only learn that by watching what readers actually asked. Read-side routing IS the schema, kept where it can still change.

## 2026-09-11 夜 · 直邮第二批已发 + awesome 线收束

- **直邮第二批 2 封已发**(用户拍板「现在发」):Di Wu(xiaowu200031@gmail.com,Gmail id 1a09133a322b6a35)+ Haitao Li(liht22@mails.tsinghua.edu.cn,id 1a09133d73371720);正文=direct_mail_batch2_20260910.md 原稿
- **awesome 线收束**:wong2(PR+Issues 全关,纯手动维护→终结);appcypher(2026-08-01 已 archive 只读→终结);**主力只剩 punkpeye #14065(open/MERGEABLE/CI 绿,等 merge)**。教训:选列表先查生命体征(archived/has_issues/pushed_at),star 数会骗人
- **dev.to**:@ahmetozel 评论回复已由用户网页贴上(API 写评论端点已废,网页是唯一路)
- **直邮台账累计**:Trajko(9/10 发→9/10 礼貌 ack,链路闭环不再触达)+ Di Wu + Haitao Li,共 3 封全个性化

## 2026-09-14 夜 · 生态嵌入线首日(两件落地)

- **awesome-ai-memory PR #19 已开**(§1 聚合记忆层表格,Letta 后字母序位;API 全程自动化,反滥用窗口已过)https://github.com/XiaomingX/awesome-ai-memory/pull/19
- **阮一峰周刊自荐 issue #11676 已发**(v2 文案:集体记忆传承定位+治理/组织记忆/胶囊三牌+克制愿景;用户过目点头)https://github.com/ruanyf/weekly/issues/11676
- 观察:周刊每周五出,48h 无收录不追发;PR #19 等维护者(该仓 9 PR 排队,正常)
- 方案正本:docs/marketing/ecosystem_gtm_plan_20260914.md(五层矩阵+五张牌+技能卡设计+排期)
- 同日背景:punkpeye #14065 维护者已放行待 Glama 评分落格(badge 已 rated A,已回复通知);GLM 生态另发现 awesome-openclaw-skills-zh 渠道(技能卡投放目标)

## 2026-09-14 午 · 技能卡+三物料成稿(全部待用户过目,未发)

- **技能卡落仓**:`skills/nautilus-compass-memory/SKILL.md`(英主+中文段)+ `SKILL.zh-CN.md`(中主+英段);三段结构(何时用/如何接/如何验),卡内所有命令路径逐个实测存在(install.sh/daemon_start.sh/install_to_agent.py/verifypack 双命令+公钥);正文零跑分数字,差异点=验证能力本身
- **投放侦察(实拉两仓)**:awesome-openclaw-skills-zh=ClawHub 官方库下载量 Top100 中文同步(fork),行链接全指 ClawHub→**前置决策 A1 先 `npx clawhub publish`(推荐)/A2 直接 PR 坦白非同步来源**;WorkBuddyGuide=VitePress 案例投稿制七段模板,「实际效果」必须真跑截图→**前置=WorkBuddy 真跑 15 分钟**
- **三份物料草稿**:docs/marketing/outreach_20260914_skillcard_drafts.md(表格行/PR 正文/案例七段/讨论帖全文+发放顺序建议 A1→讨论帖→案例)
- 状态:**草拟完成,等用户过目与前置决策,未发**;发放顺序建议:ClawHub publish → 讨论帖 → WorkBuddy 案例

## 2026-09-14 下午 · awesome-zh PR 已投(A2 方案拍板)

- **用户拍板**:A1(ClawHub 先行)暂缓——自驱授权 6 路全撞 Chrome app-bound 反窃取墙(复制 profile/junction 均不解密会话 cookie,clawhub API 只有设备流一途);改走 **A2 直接 PR**
- **PR #43 已开**:https://github.com/clawdbot-ai/awesome-openclaw-skills-zh/pull/43(state=open·mergeable·+7/-0 已独立核验 diff);表格行「Compass 记忆/nautilus-compass-memory」放分类 1 表尾,链接列指向 GitHub 仓,PR 正文坦白"尚未上 ClawHub,后续发布后可改条目;若口径仅限 ClawHub 同步来源关闭即可"
- **前置动作**:main 推送 b62ceda..a12c08c(消除 PR 内技能卡死链——9/1 PR 提审老教训复发预防)
- **新坑记录**:目标仓 README 实为 HTML 表格(web_reader 转 markdown 造成误判,差点按管道表插行);bash /tmp 与 Windows python /tmp 非同一目录(C:\tmp vs AppData\Temp),跨端传文件必走显式 Windows 路径
- **待办**:ClawHub publish(等用户 2 次点击授权后随时可补,PR 里已预告"后续改条目")·讨论帖(openclaw-community/openclaw-hub → Show and tell,素材就绪未发)·WorkBuddy 案例(等真跑截图)

## 2026-09-14 傍晚 · 讨论帖已发 + 跨框同步函两封(用户拍板「现在发+同步各框」)

- **讨论帖 #166 已发**(已核验在线·Show and tell·by chunxiaoxx):https://github.com/openclaw-community/openclaw-hub/discussions/166——批准稿原文(3 分钟接入+VerifyPack 两命令+结尾钩子问句;OpenClaw 主仓 discussions 关闭,社区 hub 是正场地)
- **跨框同步函**:v5(id 227,记忆门对直写路径的影响+daemon 两次死亡时间戳对表)·flywheel(id 228,RSI 闭环流程与判据库同构+投放两件+batch002 不催);platform 今早已收 RSI 闭环通报(id 220),四框信息面已齐
- 观察:48h 无回响不追发(讨论帖/PR #43 同规)
- **剩余队列**:ClawHub publish(用户 2 击)→PR #43 链接升级;WorkBuddy 案例(等真跑截图)

## 2026-09-15 午后 · 9/8 外发线对账收口+四渠道稿处置

- **对账**:9/8 七封(flywheel 线执行,机器之心/量子位/PaperWeekly/Zep/MemOS/mem0/Datawhale)与 Gmail 发件逐一吻合,零回信按 48h 纪律收束;错位 tag v3.1.2 已删远端(指向营销提交却触发 PyPI 工作流,CI 红源头)
- **Cognee 讨论 #5070 已投**(topoteretes/cognee · General):head-to-head 互跑邀请帖(我们跑你们的 harness,你们跑我们的,双方发布)——API 直投成功
- **TLDR/Letta/Latent Space 三表单**:Next.js/客户端渲染,程序化提交撞浏览器墙(app-bound,同 ClawHub 授权案),转交用户 30 秒×3 粘贴(稿在 kol_outreach_20260908.md §6)

## 2026-09-15 下午 · 传播第一层第一枪:EN 架构文 dev.to 已发

- **id=4660567 · published_at=2026-09-15T15:39:18Z(已验)**:https://dev.to/chunxiaoxx/why-your-agents-memory-layer-should-make-you-prove-it-wrong-343i
- title 创建时定死;ai_disclosure=fully_autonomous;正文=两个架构赌注+免费复算邀请钩;合规:只用可复算数字集
- 用户侧待发(不冲突):HN(纯文本稿 essay_architecture_en_hn.txt)·知乎/公众号(排版 HTML)·三表单(TLDR/Letta/LatentSpace)
- 值守:1-2h 查 views/reactions;评论回复走网页贴(API 评论端点已废)
