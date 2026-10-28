# 数数科技（ThinkingData → ThinkingAI）调研报告

> 调研时间：2026-04-19
> 输出对象：Nautilus 平台创始人
> 核心结论：**同赛道，同底模（MiniMax），刚刚战略转型到 AI Agent 平台——从参考对象变成了直接竞争对手**

---

## 一、公司背景

数数科技（正式名称：数数信息科技（上海）有限公司）成立于 **2015 年 6 月**，总部上海长宁区，由四位软件工程师联合创立。核心团队画像：创始人吕承通曾任腾讯互娱，负责游戏后台与数据技术；CTO 毕业于中科大，曾在盛大游戏负责数据挖掘。在上海、北京、广州、深圳、成都、东京、首尔、新加坡设有办公室（具体员工数公开资料未找到，按办公室规模与 C 轮后游戏 SaaS 行业惯例估测 300–500 人）。

**融资节奏（非常扎实）**：

| 轮次 | 时间 | 金额 | 领投/主要投资方 |
|---|---|---|---|
| 天使 | 2015-10 | 百万级 | — |
| A | 2017-01 | 千万级人民币 | 丰厚资本、安赐资本 |
| A+ | 2019-12 | 2500 万人民币 | 金沙江创投、联通新沃 |
| B | 2021-03 | 1 亿人民币 | 蓝湖资本（领）、金沙江、线性 |
| C | 2021-11 | **3.76 亿人民币** | 金沙江、蓝湖、线性、红杉中国 |
| C+ | 2022-08 | 1 亿人民币 | GGV 纪源资本 |

C+ 之后再无公开新融资记录，总融资累计约 **5.85 亿人民币**。最新估值公开资料未披露。

## 二、产品矩阵

**ThinkingAnalytics (TA) / ThinkingEngine (TE)** 是主力产品：从 2018 年 TA 1.0 起迭代到 2026 年 **TE 4.0+**，定位"游戏大数据智能引擎"，打通数据分析 + 精细化运营闭环。核心能力包括：事件采集、用户画像/标签、漏斗/留存/归因、A/B 测试、人群圈选、全场景触达、自助式 BI 可视化、社区舆情分析。技术架构升级到 Iceberg 湖仓 + Kudu 流式，强调私有化部署 30 分钟完成。

子产品线：**Hermes**（精细化运营平台，注意：和你的 Hermes V4 同名但无关）、**Gaia**（数据治理平台）。海外品牌独立运营在 thinkingdata.io。

**2026 Q2 重大战略转型 — ThinkingData → ThinkingAI**：
- **2026-04-16** 硅谷 Computer History Museum 宣布与 **MiniMax 战略合作**（MiniMax 2026 年 1 月在港交所 IPO，市值 $400 亿+），MiniMax 多模态基础模型作为"Agentic Engine 私有化部署的模型底座"；
- **2026-04-22** 上海漕河泾上海发布会揭晓更多能力；
- 发布新产品 **Agentic Engine**：定位"企业级 Agentic 平台"，使命 "Enable every company to have its own AI Agent team"。具体 Agent 类型：Analytics Agent / Engagement Agent / A/B Test Agent / Custom Agent，号称"100+ Skills"内置、支持 **MCP 协议**、原生支持自然语言对话、自托管部署（本地推理、GDPR/CCPA 合规）；
- 联合创始人 Chris Han 的定调金句："Insight alone is no longer enough — execution is now the bottleneck."

## 三、客户 & 行业深度

官方口径："1500+ 企业客户"、"8000+ 应用"、"4000+ 款游戏"。公开披露的标杆客户包括：**SEGA、KRAFTON（《绝地求生》母公司）、Century Games、Habby（《弓箭传说》）、FunPlus（《State of Survival》）、IGG、37 Games、莉莉丝旗下工作室、中手游、昆仑游戏、英雄互娱**；内嵌游戏案例：《江南百景图》《最强蜗牛》《不休的乌拉拉》《闪耀暖暖》《古剑奇谭》等。

**关于米哈游**：公开资料未出现在数数科技的客户 logo 墙（米哈游很可能自建数据平台，待核验）。

**非游戏拓展**：2026 品牌升级后明确目标扩展到**消费类应用（移动/Web/电商）**，但存量客户结构仍 90%+ 游戏。对你而言这是个重要信号——他们承认"游戏天花板到了"。

## 四、商业模式 & 定价

- **计费方式**：公开资料未披露明确价目表，行业惯例为按"事件量级/DAU/私有化模块"分档。
- **部署形态**：SaaS 云版 + 私有化部署（后者是国内游戏大厂主要形态，因数据敏感）。
- **订单规模（行业口径，待核验）**：私有化部署起售估计 **50–100 万人民币/年**，头部客户年费可达数百万到千万级。
- **开源**：无开源版，SDK 开源（iOS/Android/Unity/Unreal/鸿蒙 OpenHarmony 等），核心引擎闭源。

## 五、2026 最新动态

1. **2026-03-10** 旧金山 ThinkingData Summit（GDC 配套）—— 定调"data + AI"；
2. **2026-04-16** 硅谷官宣 MiniMax 合作、品牌 ThinkingData → ThinkingAI 切换；
3. **2026-04-22** 上海 Agentic Engine 发布会；
4. 新域名 **thinkingai.io** 已切换，原 thinkingdata.io 301 跳转；
5. 未见 2026 新融资（C+ 之后沉默 3.5 年，结合估值压力，这次 AI 转型可能是为下一轮融资或并购铺路）。

## 六、对 Nautilus 的 3 条具体启示

### 启示 1：**你们已经是直接竞争对手，且他们用同一家 LLM（MiniMax）**

ThinkingAI Agentic Engine 的技术栈关键词——"MCP 协议、自托管、100+ Skills、Agent 团队、从 Insight 到 Action"——与 Hermes V4 + 智涌 HR + ContentEngine 的叙事**高度重叠**。但他们**垂直切入游戏运营场景**（LiveOps、A/B、Payment Analytics），你垂直切入 **HR + VC 研报**。

**防御动作**：立刻在智涌 HR 和 ContentEngine 的对外文案里强化"垂直行业 know-how"，别让客户把你当成"通用 Agent 平台"去跟 ThinkingAI 对比——你会输在品牌、渠道、私有化成熟度上。

### 启示 2：**学他们的"Skills 资产化"，但要比他们更彻底**

数数 10 年沉淀的行业方法论被 ThinkingAI 明确"编码为可调用的 Skills"——这就是 Hermes V4 呼吸链的理论基础，但他们产品化了。

**行动建议**：把你在 Nautilus bounty 市场、HR 8 个 AI 员工、创投日报 RAID-2 写审分离里积累的领域经验，**显式做成可对外售卖的 Skill Pack**（如"HR 简历筛选 SOP"、"VC 周报框架六级跃迁"），这恰好是你宪法提到的"真实客户 / 能收钱 / 助力 HR 或研报"的三个 Yes 交点。他们卖的是"Agent 团队基础设施"，你可以卖"装好 Skills 的行业套件"，价格锚点和 GTM 都不一样。

### 启示 3：**SaaS 定价避开他们主战场，走按结果收费（outcome-based）**

数数走的是典型企业 SaaS 私有化路线（年费 50 万起），这条路径需要销售铁军、售前团队、实施交付能力——以 Nautilus 当前资源打不过。

**定价突围**：智涌 HR 按"成功筛选简历数 / 发放工资单数"收费，创投日报按"生成研报份数 + 公众号阅读分成"收费。outcome-based 在 Gartner 2026 SaaS 趋势报告里是头号关键词，但传统分析厂商因收入结构锁定转不了。这正是你作为初创的结构性优势。

另外，**千万不要再叫你的框架"Hermes"**——数数科技的 Hermes 运营平台商标在先，且现在他们也叫 Agentic Engine，正面撞上会吃亏。考虑 V5 改名，例如 Nautilus Engine 或直接 D-Spine（对应你的 D 架构）。

> **⚠️ 补丁（2026-04-19 晚间更新）**：用户后续指出——**Hermes 是开源项目**（github 已有同名框架），数数科技的 Hermes 和我们都是基于同一个开源底座。不存在商标撞车问题。差异化应该在**垂直产品层**，不是在名字层。所以"启示 3 末尾改名建议"作废。

## 七、潜在合作 / 竞争

**竞争面（主）**：
- 他们如果把 Agentic Engine 横向拓展到**消费应用 / 电商 / SaaS**（官方路线图已明示），会和智涌 HR 侧面相撞——因为 HR SaaS 本质是"员工行为+薪酬数据"，和他们的用户行为分析技术栈完全通用；
- 两家都用 MiniMax 做底模，模型层没有差异化，只能在**数据、Skills、行业深度**层拉开。

**合作面（窄但值得试）**：
- **MCP 互通**：他们明确支持 MCP，你的 HR MCP server 技术上可以作为 Agentic Engine 的外挂 Skill Pack。**建议动作**：4 月 22 日上海发布会后，主动邮件 Chris Han，提议智涌 HR MCP 作为 Agentic Engine 的 HR 垂直扩展，换曝光或收入分成；
- **渠道合作**：他们的 1500 家游戏客户里有大量中型游戏公司的 HR 和市场岗位是痛点，可以谈 reseller；
- **人才 / 信息情报**：他们的销售团队懂游戏公司决策链，可以挖 1-2 个高级 BD。

**防御点**：
- 确保智涌 HR 和创投日报的**标杆客户 logo** 尽快上墙，品牌信任是他们最大的壁垒；
- 不要和他们比 Dashboard 完整度，要比 **Agent 自主执行闭环的深度**（你的"快车道 / 痛苦机制 / CHAIN.jsonl"是差异化资产）；
- **警惕他们的 PR 节奏**：ThinkingAI 的品牌重塑预算很足，Nautilus 年内至少要做一次对标发布会（用"第一个跑通 bounty 市场 + 真实付费客户"的叙事压住）。

---

## 参考链接

1. ThinkingAI 官网（新品牌）: https://thinkingai.io/
2. ThinkingData 中文站: https://www.thinkingdata.cn/
3. ThinkingData 海外站（已 301）: https://thinkingdata.io/
4. ThinkingAI × MiniMax 战略合作中文 PR: https://www.prnasia.com/story/529470-1.shtml
5. ThinkingAI × MiniMax 英文 PR: https://www.prnewswire.com/news-releases/thinkingai-partners-with-minimax-to-launch-agentic-engine-marking-shift-from-analytics-to-autonomous-business-operations-302744708.html
6. Mobidictum 产业媒体报道: https://mobidictum.com/thinkingai-minimax-agentic-engine/
7. GamesBeat ThinkingData Summit 2026 报道: https://gamesbeat.com/thinkingdata-summit-2026-explores-the-reality-of-data-driven-growth/
8. 36 氪创投平台融资数据: https://pitchhub.36kr.com/project/1678464992408580
9. 数数科技融资/历史 B 轮披露: https://www.thinkingdata.cn/thinking/news/1914.html
10. 数数科技公司动态（大事记）: https://www.thinkingdata.cn/thinking/news/4630.html
11. TE 4.0 发布公告: https://www.thinkingdata.cn/thinking/blog/features/6024.html
12. ThinkingEngine 新一代引擎发布: https://www.thinkingdata.cn/thinking/blog/features/6074.html
13. 私有化部署产品页: https://thinkingdata.cn/privatization.html
14. 数数科技 CSDN 技术博客（与 1500+ 企业共创）: https://blog.csdn.net/ThinkingData/article/details/156080356
15. 数数信息科技（上海）工商信息: https://m.qcc.com/firm/8c21e6bb56267b94d68db43077ee1bc8.html
16. CapWhale 合作新闻中文版: http://www.capwhale.com/newsfile/details/20260417/48a20482c8b642f4ac5ca3f43d786ce1.shtml

---

**核心判断（一句话）**：数数科技刚刚（2026-04-16）完成从"游戏数据分析 SaaS"到"企业 Agent 平台"的战略转身，和 Nautilus 赛道正面相撞、底模撞车（都用 MiniMax），但他们的垂直仍在游戏。**窗口期最多 6–12 个月**：Nautilus 需要用"HR + VC 垂直 + outcome-based 定价 + MCP 互通"三板斧迅速建立差异化品牌认知，否则会在 ThinkingAI 横向扩张时被当成"通用 Agent 平台里的小玩家"吃掉。
