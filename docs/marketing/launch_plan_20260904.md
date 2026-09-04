# 发布与推广营销规划 · v1(2026-09-04 落仓)

> 依据:用户拍板五层传播顺序([[propagation-layer-order-20260904]])+ 商业方案 90 天时序(§4)。
> 本文档=发布期(9/5-9/30)执行正本;商业线正本见 [business_plan_20260904.md](business_plan_20260904.md)。
> 纪律:对外发布动作一律用户拍板后执行;数字门已全开(终检 26e8b76)。

---

## 0. 总原则(不可倒置)

影响力从专业圈向下辐射:**专业信任 → 市场 → 大众**。先发故事营销会把产品定格成"故事"而非"基础设施"。
每层有自己的成功判据,不达不催下一层;下一层可以提前准备,不提前发布。

## 1. 物料清单与状态

| 物料 | 层 | 状态 |
|---|---|---|
| launch post(r/LocalLLaMA 主帖 + X 7 条) | ① | ✅ 成品(终检修复 26e8b76),仅 paper2 arXiv 链接留回填位 |
| 英文架构立场长文(~1900 词) | ① | ✅ 成品 v1,拼写终检 9/5 通过(数字对 SCOREBOARD·OKF 术语查证 Google Cloud 官方规范) |
| dev.to 适配版 | ① | ✅ [20260905_devto_position_paper.md](20260905_devto_position_paper.md)(front matter+liquid 仓库卡,9/10 与博客同日) |
| 第二帖(LME-V2 判分卫生故事) | ① | ✅ 英文成品 v1(8c5bc78),cheap-tier 数字已定案可填 |
| paper2(判官盲区,arXiv) | ③ | 🟡 材料定稿待用户提交(账号登录是用户动作),提交后 1-2 天出 ID |
| 中文圈三件(架构文中文版/知乎答/公众号技术文) | ② | 🔴 未写(第①层发布后启动,素材全在 ARCHITECTURE.md) |
| HN 提交文案(标题+首评) | ① | ✅ 见 §14 |
| 落地页 hero 刷新(75.4/81.6) | ④ | 🟡 待确认落地页是否已刷(e1b3e37 提过 agent.json 上云,落地页待验) |

## 2. 渠道矩阵

| 层 | 渠道 | 打法 |
|---|---|---|
| ① 英文业界 | r/LocalLLaMA | 主帖周二-周四 9-11am ET(=北京 21-24 点)技术帖黄金窗;24h 内必回评论(算法权重) |
| ① | X/Twitter | 主帖发布 2h 内发 thread 导流;@ 无特指,靠内容自传 |
| ① | HN | position paper 走普通提交(非 Show HN,有可跑产品才 Show);标题零营销腔,首评放技术细节+evidence 链 |
| ① | Lobsters | 架构长文提交;强调可复现($3.50)+判分卫生学;社区小而技术浓度高,适合深度讨论 |
| ① | Bluesky / Mastodon | X thread 同步发(开源/自托管圈在 bsky 活跃);标签 #LocalLLM #MCP #AgentMemory |
| ① | r/MachineLearning | ⚠️ 谨慎:仅 paper2 arXiv ID 出来后以论文讨论发(遵守版规,不导流 repo 首句);Reddit 主阵地仍是 r/LocalLLaMA |
| ① | Newsletter 投稿(TLDR AI / AlphaSignal / Interconnects 等) | 短 pitch 邮件:一句问题+一句架构+repo 链接+可复现点;第①层反响好后再投(有数据背书) |
| ① | MCP 社区(Discord / glama / PulseMCP / mcp.so) | 目录提交见 §12#6;社区频道发集成公告(带 tools/list 一屏截图) |
| ① | dev.to / 个人博客 | position paper 长文底座;HN 引用此链接 |
| ② 中文圈 | 知乎 | 架构文中文版(问答形式挂"AI agent 记忆如何做"类问题)+专栏 |
| ② | 微信公众号/掘金/V2EX | 技术文;V2EX 强调本地部署+开源可复现 |
| ③ 学术 | arXiv cs.CL | paper2;ID 出来后回填三处物料 |
| ④ 市场需求 | 落地页+SEO+Product Hunt | PH 留到 hosted 正式定价时(open beta 阶段先不烧) |
| ⑤ 大众 | 公众号故事/视频号 | 起源故事(禅心 AI/佛陀 agent→自研)+量子纠缠叙事,最后放 |

## 3. 时间表(发布期四周)

### 第 0 周(9/5-9/7,周末)· 准备
- [ ] 落地页 hero 数字确认/刷新(75.4/81.6 双口径)
- [ ] HN 提交文案+首评草稿写好
- [ ] 评论区应答模板备好(§6)
- [ ] paper2 用户提交 arXiv(可选先行,不阻塞)

### 第 1 周(9/8-9/12)· 第①层主发布
- **9/8 周二 21:00-24:00 北京**:r/LocalLLaMA 主帖 + 2h 后 X thread
- 9/9-9/10:评论区值守(24h 内回复率 100%);记录数据(§5)
- **9/10 周四**:position paper 上个人博客+dev.to;反响好则同日/9/11 提交 HN(与 Reddit 错峰 48h,避免同周轰炸观感)
- 9/12(N5④ due 前):第一波数据复盘
- paper2 arXiv ID 出来后:回填 launch post/position paper/落地页三处

### 第 2 周(9/15-9/19)· 第②层中文圈
- 知乎架构文中文版发布;公众号技术文;V2EX
- 中文圈评论同样 24h 响应;素材原则:不搬运英文帖,重写(中文技术社区反感翻译腔)

### 第 3 周(9/22-9/26)· ③收尾+④启动
- paper2 传播(如有学术圈反馈,引回英文社区二次讨论)
- 落地页 SEO 关键词(agent memory / local-first memory / LongMemEval)
- A 路径计量+支付开工(商业方案 §3A)

### 第 4 周(9/29-9/30)· 月度复盘
- 全渠道数据汇总;决定 10 月节奏(第二帖+对打评测+中文圈第二批)

## 4. D-day runbook(9/8 发布日)

1. 20:30 北京:最后检查——`git status` clean+pushed;signup/MCP 探针重跑一遍(四绿才发);落地页 200;**chunxiaoxx 账号已登录 Reddit/X**
2. 21:00:r/LocalLLaMA 发主帖(账号:chunxiaoxx;标题照物料,勿改数字;**带 60-90s 终端录屏**)
3. 21:05:**立即抢首评(草稿见 §13)**——主动说破 mem0 自报 94.4% vs 我方 75.4% 的口径问题,不给任何人留"抓漏洞"的先手
4. 23:00:X thread 发布(7 条,末条带 repo+signup)
5. 23:00-24:00:守 Reddit 评论区,数字类问题直接引 evidence 文件路径
6. 9/9 早:数据快照(star/评论/signup/MCP 调用),记入本文件 §5 表
7. 🔴 红线:不买量不刷票不用小号;被质疑只对事实不对人;答不上来的承认"open question"

## 5. 度量(24h / 72h / 7d 三个检查点)

| 指标 | 来源 | 24h 合格线(主观锚) |
|---|---|---|
| Reddit upvote/评论 | 帖子页 | 评论中有 ≥3 个技术性讨论(非嘲讽)即算破圈 |
| GitHub star | repo insights | 24h ≥20 / 7d ≥100 为理想;个位数也正常,不看单点看斜率 |
| signup 注册数 | 服务器 DB(signup 表) | 7d ≥10 真实注册(非 probe) |
| MCP 调用 | 服务端日志 | 有非探针的外部 token 调用=真采用 |
| HN 点数/评论 | 提交页 | front page 与否不强求,评论区质量优先 |
| arXiv 引用动作 | Google Scholar alert | 长期指标,不设短期门 |

## 6. 评论区应答模板(备查)

- **"判官是自己请的,分数不可信"**:引 position paper caliber notes+PROTOCOL.md;承认 judge 差异存在,强调双口径+同题同判据对打+71.1% 是官方自测不需我方判官
- **"为什么不用 AGPL/为什么不是纯开源"**:Modified MIT 一句话(2-year sunset 是 FSL 的事,我们是托管规模门槛 100 付费用户);自部署永久免费是核心承诺
- **"mem0 数字你们自己测的?"**:是,同题同判据,reproduction 脚本开源,欢迎复跑($3.50)
- **"mem0 自报 94.4% 你们 75.4%,还是输了"**:口径不同不可比——他们的 harness/判官/subject/数据版都可能不同,这正是本领域 meta-problem(我们自己判官还挂过 5 次);真正硬的对打是同题同判据的检索层:P@1 0.890 vs 0.774,脚本开源欢迎重跑;若有人把 mem0 最新版跑进我们的 harness(或反之),发出来,这种数据才推动领域
- **竞品员工到场(mem0/Zep 团队活跃于同社区)**:只谈自家数字与口径,零商业攻击;标准邀请句:"your latest version is welcome in our harness — scripts are in the repo"
- **"多租户/安全谁验证的"**:四探针脚本在 repo,任何人可对生产端点重跑
- **"一个人写的?"**:是,130 天 771 commits,其中 603 由 agent 舰队提交——这本身就是产品的证明(dogfood)
- **面对明显嘲讽**:不接火;只补事实一条,不再跟

## 7. 风险与应对

| 风险 | 概率 | 应对 |
|---|---|---|
| 冷启动无人看(Reddit/HN 沉底) | 中 | 不刷量;72h 后复盘标题/时间;第二周经 dev.to/blog 带 SEO 长尾;材料可复用不浪费 |
| 跑分被较真质疑 | 中 | 所有数字 evidence 链在仓;口径披露是差异化卖点,把质疑引向 PROTOCOL.md |
| license 被喷"伪开源" | 中 | §6 标准答案;开源纯度辩护交给第三方(四探针/复现成本) |
| 竞品恶意对比/碰瓷 | 低 | 不点名回应竞品营销;只守自家数字真实性 |
| hosted 被刷注册/滥用 | 中 | 已有 scoped token+隔离;发现滥用可按 token 撤销;必要时注册加邮箱验证 |
| 发布后 bug 爆发 | 低 | 四探针绿灯才发;热点修复走 patch commit,坏消息主动披露(信任资产) |

## 8. 拍板记录(2026-09-04 用户)

- ✅ 主发布日 **9/8 周二 21:00 北京** 确认
- ✅ 发布账号:**chunxiaoxx**(GitHub 同名)
- ✅ 中文圈:用户个人账号(具体主体发布前定)
- ✅ paper2:**提前提交**,准备充分为准(材料已定稿,等用户 arXiv 账号操作)
- ✅ 生产降压:8097 API 层 workers 1→2 已执行(见 §9 复验)
- 🆕 材料全家桶:见 §10(演讲 PPT/demo 动态演示/一页纸)
- 🆕 智源(BAAI)联动:见 §11,用户主导沟通,我方备联动材料

## 9. 附录:承载力压测记录(2026-09-04 · scripts/load_probe.py)

生产端点渐进压测(并发 1→2→5→10→20,读=recall/写=ingest_obs 分波,止损线=错误率>20% 或 p95>10s,**未触发,全阶段完成**,错误率全程 ≤1%):

| 并发 | 读 p50/p95/max | 读 rps | 写 p50/p95 | 写 rps |
|---|---|---|---|---|
| 1 | 0.10 / 1.23 / 1.81s | 3.1 | 0.32 / 0.57s | 3.4 |
| 5 | 1.12 / 2.19 / 30.1s | 3.3 | 0.23 / 1.56s | 7.3 |
| 10 | 2.49 / 4.74 / 5.82s | 4.8 | 0.26 / 1.11s | 17.1 |
| 20 | 2.57 / 7.88 / 30.0s(超时) | 5.4 | 0.25 / 1.27s | 28.6 |

**判读**:①单用户/小并发(1-5)p50 ≤1.1s,体验良好;②**读吞吐天花板 ≈5 rps(全服务共享)**——并发加 20 倍吞吐只涨 1.7 倍;③写路径扩展性佳;④韧性 OK,无 5xx 雪崩。**注意:压测 probe 用户为空记忆空间(下限近似),真实大库检索单请求更重。**

### 9.1 多 worker 变更与复验(同日)

拓扑实探:compass.nautilus.social → 8097(`compass-mcp-http.service`,mcp_http_server:app)→ 嵌入走 9877 daemon(BGE-m3 CPU,**串行推理=真瓶颈**)。变更:8097 workers 1→**2**(systemd ExecStart,其余不动;嵌入 daemon 不动避免代码改动)。复验:三进程共享监听确认 → **四探针四绿** → 压测对比:

| 20 并发 | 变更前 | 变更后 |
|---|---|---|
| 读 max | 30.0s(超时) | **10.99s(零超时)** |
| 读成功率 | 99.8% | **100%** |
| 读吞吐 | 5.4 rps | 4.4 rps(持平——瓶颈在嵌入 daemon,符合预判) |

**结论**:API 层扩容换来"慢而不死→稳而有尾",发布日够用;真提读吞吐需嵌入 daemon 并行化(改代码,发布后立项)。发帖仍注明 open beta。

## 10. 材料全家桶(用户 9/4 拍板:全部需要,含上台分享)

按受众×场合的矩阵,制作顺序按发布节奏排:

| 材料 | 受众/场合 | 框架(本轮) | 成品 |
|---|---|---|---|
| **演讲 PPT · 30 分钟版** | 技术大会/Meetup | §10.1 | 待大纲确认后制作 |
| 演讲 PPT · 15/5 分钟版 | 论坛/路演(由 30 分钟版裁剪) | 同上 | 同上 |
| **demo 动态演示** | 演讲现场+录屏兜底 | §10.2 | 待脚本确认后录制 |
| 一页纸(英文 one-pager) | 线下/邮件触达政企 | §10.3 | 待做 |
| 帖子矩阵 | 见 §1(已就绪 3 件) | — | ✅ |
| 中文圈图文 | 第②层 | 9/15 周启动 | — |

### 10.1 演讲 PPT 三幕结构(30 分钟)

1. **第一幕 · 问题(5min)**:你的 agent 每天忘记你 90% 说过的话→现场演示 ChatGPT 记忆覆写(官方论文人肉研究截图)→"写入时压缩=对未来的盲目下注"
2. **第二幕 · 架构(10min)**:三不变量(未来查询不可知/原文唯一可重索引/成本曲线反了)→六层图(ARCHITECTURE.md 直改)→反直觉点:写入零 LLM,智能全在读取
3. **第三幕 · 证据(10min)**:四战场成绩单(检索对打/LOCOMO 客场/LME-V2/e2e 75.4 双口径)→判分卫生学故事(抓自己判官 5 次,自嘲式讲=最圈粉段)→负结果清单(预注册文化)
4. **收尾(5min)**:dogfood 故事(130 天 771 commits,603 由 agent 舰队提交)→"One developer. No cloud required."→signup 二维码

### 10.2 demo 动态演示方案(现场 live + 录屏兜底)

三场景递进,每个 ≤90 秒,全程本地终端(最有说服力的就是终端):
- **D1 跨会话记忆**:三个会话里分别说三件事→第四个会话问跨会话问题→答对(对照:清掉记忆后同样问题答不出)
- **D2 多 agent 记忆胶囊**:agent A 解题 reward 1.0→写胶囊→agent B 直接继承(B 从 FAIL→PASS 的实录复刻)
- **D3 安全四探针**:现场跑 probes.py 打生产端点,四绿大屏(隔离/撤销肉眼可见)
- 录屏兜底:发布会前一周录制 1080p 三段;现场网络/环境故障即切录屏
- 技术准备:demo 专用干净 profile+预置会话数据脚本+恢复脚本(现场可重置)

### 10.3 一页纸(英文,政企向)

正面:问题一句+架构图+四行成绩+安全矩阵(四探针/隔离/merkle);背面:三档接入(本地三条命令/hosted signup/私有化联系)+Modified MIT 说明。素材全在 README/ARCHITECTURE,排版后交用户过目。

## 11. 智源(BAAI)联动(用户主导沟通,9/4 提出)

**事实底座**:compass 嵌入层用 BGE-m3(BAAI 开源)——本地部署零嵌入成本、零数据出域,是"本地免费无限"商业叙事的技术基石;评测线 LME-V2/LME-S 检索对打的 embedder 也是 BGE-m3(跨厂商公平对比同样用它)。

**联动价值(我方视角)**:①BAAI 生态页/case study 收录=权威背书;②联合内容(中文圈第②层现成题材:"BGE-m3 驱动的本地 agent 记忆层");③后续模型(BGE 系迭代)早期合作。**对方视角**:真实生产 case+可复现跑分数据+具身智能组织场景(对方也在布局)。

**我方准备物**:一页联动介绍(见 `bge_liaison_onepager_20260904.md`),数字口径与发布物料完全一致;沟通节奏放第①层发布后(拿着发布数据去谈更有分量),中文圈联动可作第②层联合内容。

## 12. 发布前冲刺清单(2026-09-04 再思考后修订 · 用户全部采纳,PPT 并行)

优先级判定:**9/8 成败取决于帖子质量与首日体验,不取决于材料储备量**。

| # | 事项 | 优先级 | 状态 |
|---|---|---|---|
| 1 | 60-90s 终端录屏(D1 跨会话记忆),嵌 Reddit 帖 | 🔴 发布前必做 | 脚本见 [demo_recording_script.md](demo_recording_script.md),录制待用户 |
| 2 | 首评草稿(94.4 vs 75.4 口径说破) | 🔴 发布前必做 | ✅ 见 §13 |
| 3 | chunxiaoxx Reddit karma 预热(本周起技术性评论) | 🟡 本周 | 待用户(每天 2-3 条,发帖前有历史即可) |
| 4 | 新人全流程实测+摩擦修复 | 🟡 | ✅ 已实测(§13.1);邮箱验证已实现(commit 4fefc97),等 SMTP 凭证后 restart 生效;🆕 9/5 双洞修复:① `/mcp`(无尾斜杠)301→:8443 死路径(nginx 已改直 proxy);② **自助 token 读写全断+跨租户读**(9/4 workers 2 重启后生效的 scope 门禁把无 project 参数的调用判 `read:''` 403——且 9/4 实测的"200"实为 forbidden 包在 body 里的假绿;首修放行后又暴露执行侧落 daemon 默认内部用户空间 cycle-N-auto 的跨租户读,终修=缺省 project 显式注入持有者 uid,读写落自己空间,公网复验 own-space+四探针 FOUR-GREEN);🟡 遗留:tools/list 17 个含 10 个平台内部工具(governance_*/submit_platform_task 等)暴露给外部用户,收敛白名单建议提前到发布前拍板 |
| 5 | paper2 提交 checklist 交用户 | 🟡 | ✅ 见 §13.2 |
| 6 | MCP 目录提交(PulseMCP/Smithery/mcp.so/glama) | 🟢 发布周 | ✅ 材料已核对修正(server.json 56.6%→75.4 定案口径+版本 3.1.1+packages 指 PyPI 真实 3.0.1+废弃 1/15 cost 删;npm 清单同步;anchors 防吹牛锚包 v1.3 重校准);⚠️ 发布周 TODO:PyPI 发 3.1.1(现 PyPI 3.0.1 描述停在 EvoMap 旧文案,需用户 PyPI 凭证)·目录提交动作需用户账号 |
| 7 | 智源接触(一页纸已备) | 🟢 本周发出,不催结果 | ✅ 材料 |
| 8 | PPT 页级大纲(Marp)→ 成品 | 🟡 并行(用户有演讲计划) | ✅ 大纲+成品双格式已渲染([pptx](pitch_deck_20260904.pptx) / [html](pitch_deck_20260904.html),12 页·讲者注内嵌);内容改动后重出:`npx @marp-team/marp-cli pitch_deck_outline_20260904.md -o pitch_deck_20260904.pptx` |
| 9 | 一页纸(英文政企) | ⏸ 降级:有真实触达场景再做 | — |

## 12.1 tools/list 收敛方案(已备,拍板即执行 · 2026-09-05)

改动只落 `mcp_http_server.py`(hosted 公网入口),本地 stdio/daemon 不受影响:

```python
# hosted 公网工具面:仅用户工具对外暴露(内部平台工具不进公网清单)
PUBLIC_TOOLS = {"ingest_obs", "recall", "session_search", "thread_recall",
                "profile", "drift_check", "drift_history", "feedback_log"}

# _list_tools 循环内加一行:
        if s["name"] not in PUBLIC_TOOLS and "admin" not in _current_scopes.get():
            continue

# _call_tool 的 deny 检查旁加同款(防知名字直调):
    if name not in PUBLIC_TOOLS and "admin" not in _current_scopes.get():
        return [... forbidden ...]
```

- 兼容性:ops/内部 token(tokens.json,admin scope)可见全部 17 个,内部调度零影响;自助/公开 token 只见 8 个用户工具
- 效果:外部 tools/list 17→8;governance_×5/submit_platform_task/proof_of_impact/add_worker/long_task/ingest_platform_task_result 退出公网面
- 部署:scp+restart,probes.py 复跑 + tools/list 计数断言
- 待用户拍板后执行(对外可见行为变更)

## 13. 首评草稿(Reddit first comment · 发帖后立即发)

> **OP here — before anyone asks: yes, mem0 self-reports 94.4% e2e on LongMemEval-S, and we report 75.4%. Those numbers are not comparable, and here's why.**
>
> Our 75.4% comes from our own harness: original Oct-2024 release, glm-5.3-flash judge, full 500 questions, dual accounting (81.6% excluding 71 judge-outage questions, disclosed in the post). mem0's 94.4% comes from their harness — different judge, different subject model, possibly different data version. Cross-harness numbers don't compare in this field; that's literally the meta-problem we keep hitting (we caught our own judge failing 5 times — one outage silently recorded 14.2% of questions as wrong answers).
>
> The comparison we *can* stand behind is the retrieval head-to-head: identical questions, identical criteria, BGE-m3 on both sides, our reproduction of mem0 2.0.19 — P@1 0.890 vs 0.774. Scripts and evidence in the repo, ~$3.50 to re-run. If someone runs mem0's latest through our harness (or ours through theirs) and posts the numbers — that's the kind of argument that moves this field forward.
>
> Happy to answer anything on the routing design; that's the fun part.

### 13.1 新人全流程实测(2026-09-04 · 生产端点)

全新邮箱 signup→login(JWT)→控制台发 token→首次写入→首次 recall→tools/list,全程 200,**注册到首查 <15s**:

| 步骤 | 耗时 | 结果 |
|---|---|---|
| signup | ~1-2s | 200 |
| login → JWT | ~1s | 200 |
| create token(cmp_live_ 前缀) | ~0.4s | 200 |
| 首次写入 ingest_obs | 1.7s | 200 |
| 首次 recall(冷路径) | 4.5s | 200(后续回到亚秒) |
| tools/list | 1.3s | 10 个工具 |

**实测发现三件待办**:①**无邮箱验证**——假邮箱可直接注册,发帖后可能被批量薅;建议发布前加简单邮箱验证或 rate limit(小改动,需拍板);②**tools/list 暴露平台内部工具**(submit_platform_task/long_task 等 nautilus 平台调度工具)——外部新用户会困惑+扩大攻击面,建议 hosted 面收敛工具白名单(发布后);③首次 recall 冷路径 4.5s——可接受,备注即可。

### 13.2 paper2 提交 checklist(用户操作)

1. arXiv 账号登录(paper1 同账号 2605.09863,endorsement 已有)
2. 元数据:cs.CL 主分类;license 照 paper1(arXiv 默认非独占);作者 Chunxiao Wang 单作者
3. 上传 tex 主文件(PDF 已编译验证 0 错 0 undefined)
4. 提交前自检三项(摘要字数/零 includegraphics/零 input)——已绿(71a78f1)
5. 提交后:把 arXiv ID 回填三处(launch post/position paper/落地页)

## 14. HN 提交文案(9/10-9/11 用,与 Reddit 错峰 48h)

> 提交物:repo 直链(有可跑产品+全套证据在 repo,比 position paper 更硬);position paper 作评论区补充链接。
> 账号:chunxiaoxx。提交时间:美东上午 9-11 点(北京 21-24 点),周中。

### 14.1 标题(HN 风格:零营销腔、标题即内容,二选一)

- **推荐**:`Nautilus-compass: Local-first agent memory – write path makes zero LLM calls`
- 备选(判官角度,论文味):`We caught our own LLM judge silently failing five times (agent memory evals)`

### 14.2 首评(OP follow-up,~180 词英文)

> One of the authors here (solo dev — 130 days, 771 commits, most of them by my own agent fleet, which is itself the best demo).
>
> The design bet: write-time compression is a blind wager on the future — nobody knows at write time what will be asked later. So the write path stores observations verbatim with zero LLM calls (local BGE-m3 embeddings, nothing leaves the machine), and all intelligence lives at read time: query-type routing, BM25+dense fusion, date anchoring, summary-card assembly. On LongMemEval-S that routing lifts e2e accuracy from 42.6% to 75.4% (81.6% excluding 71 judge-outage questions — disclosed, not hidden).
>
> The head-to-head you can actually check: same 500 questions, same criteria, same embedder, our reproduction of mem0 — P@1 0.890 vs 0.774. Reproduction scripts are in the repo, ~$3.50 of GPU time.
>
> The part I'm most proud of is the hygiene work: we caught our own judge failing five times (a gateway outage silently recorded 14.2% of questions as wrong answers). Paper on that is on arXiv — judging failures are this field's meta-problem.
>
> License is Modified MIT (Kimi-style): trademark protection + a cap on hosted paying users; self-hosting stays free forever. Happy to answer anything.

### 14.3 HN 纪律(与 Reddit 差异)

- 不发 thread 不拉票;24h 内值守,答技术上头 3-5 条即止,不做营销回复
- "Show HN" 不用(产品已发布+有用户=普通提交;若 moderator 建议转 Show 再转)
- 被质疑 license/自测数字:引 §6 模板;HN 对"self-reported benchmark"敏感,先亮 reproduction $3.50 和开源 harness,再亮分数
