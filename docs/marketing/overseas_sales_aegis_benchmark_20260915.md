# 海外销售调研 + 营销诊断 + WorkBuddy 接入(2026-09-15)

> 用户五问:Aegis 模式可否借鉴+海外销售?/ClawHub 推进?/营销为何差?/
> WorkBuddy 怎么接?/总结入仓(已另录 RETROSPECTIVE)。
> 调研日:2026-09-15;来源:live web(Aegis/mem0/Letta/Zep 官网定价页)。

## 一、竞对定价图景(2026-09 实测)

| 产品 | 定价模型 | 入口价 | 备注 |
|---|---|---|---|
| [Aegis Compass](https://aegisplatform.ai/compass) | per-seat | **Solo $20/mo** 自助+7 天试用 | 记忆+治理层,跑在 Aegis Govern 上;企业版分层年费 |
| [mem0](https://mem0.ai/pricing) | 用量分层 | Free→$19→$249 | 图记忆锁 $249 档;社区基准自称 92.3 分(自报口径) |
| [Letta](https://docs.letta.com/pricing/) | per-seat | **$20/seat/mo** | 唯一真 per-seat;重度用户 $100-200+/mo |
| [Zep](https://www.getzep.com/pricing/) | credit | $125/mo 起 | Flex $125(5 万 credit)→Flex Plus $375 |

**Aegis 最值得借的三点**:
1. **自助入口 $20/mo + 7 天试用**——低摩擦付费起点,先让单开发者上瘾再谈企业;
2. **"治理费是唯一毛利,token 原价透传"**(同系 [Aegis AI](https://aegis.aurimas.io/pricing) 口径)——
   定价哲学透明,客户不怕账单惊吓;我们的验证服务天然适配:**审计费固定,
   计算成本如实透传**;
3. 记忆+治理**打包卖**(记忆门弱治理门强也卖得动 $20)——反证我们的
   "记忆强+验证强"组合定价空间更大。

## 二、海外销售可行性评估(两条服务线)

**结论先行:可卖,但两线节奏不同——记忆 SaaS 可直接对标上线,验证服务先
以英文审计试水,均不新建付费基建直到 M1(反剧场闸门不变)。**

### 线 1 · 平台服务(记忆 SaaS)
- **已具备**:多租户 hosted gateway(compass.nautilus.social,JWT+scope+
  用户隔离+自动探针)、英文 README/技能卡、npm/PyPI 分发
- **对标定价建议**:Free(10K memories)→ **Solo $19/mo**(贴 mem0 Starter,
  低于 Letta/Zep)→ Pro $99/mo(含 drift+chain_extra+更高配额)→ Enterprise
- **缺口(上线前必补)**:①海外收款(Stripe/Lemon Squeezy 个人主体可开)
  ②英文 ToS/隐私页(LICENSE A4 已澄清验证服务独立口径,但 SaaS 线受
  A2 托管 100 付费用户上限约束——**首期 100 席位恰好可当"限量内测"叙事**)
  ③SLA 页(用我们的工作时段诚实口径起步)
- **风险**:撞名(对外一律全名 nautilus-compass;Aegis 也叫 Compass=机会,
  可在对比页合法引用);支持时区(单人身位,先 FAQ+issue)

### 线 2 · 对外验证服务
- 已定稿(verification_playbook_20260914):SKU1 审计 $99-299,M1 前零基建
- 海外适配:复算墙/回执全英文天然就绪;定价在"客户自建复算环境成本"之下
  的逻辑对海外团队同样成立;$99 档对标一次 consulting call 的零头,无痛点
- **顺序不变**:免费复算入口(已开)→ M1 → M2 试报价 → M3 成交——海外只是
  同一漏斗的更大水面,不另起炉灶

### 落地顺序建议(不推翻既有拍板)
1. 本周:Stripe/LemonSqueezy 账号+英文 ToS 模板(准备件,不发布)
2. M1 到达后:Solo $19 内测页(100 席位上限当稀缺性)+ 审计 $99 试报价页
3. 第一篇英文架构文(见下)承担两线共同的路由入口

## 三、营销为何差——诊断(证据都在台账里)

不是能力差,是**三个结构性错配**:
1. **没做最难且最有效的那层**:用户 9/4 拍板传播五层,第一层=英文业界架构文
   ——至今一篇未发。我们一直在第 2-5 层(列表/周刊/社区帖)打转,而架构文
   才是技术买家的转化层。paper2 改写一篇 30 分钟可成稿。
2. **新号信任冷启动**:HN 秒 flag(号没养)、dev.to 零分发(AI 披露新政+
   新号)、GitHub 反滥用窗口、GCM token 无 PR 权——我们以"零声誉账号"对抗
   各平台的反滥用系统,天然被压。**处方:渠道集中到 2 个**(GitHub+一篇
   架构文投 HackerNews/Reddit r/LocalLLaMA),放弃广撒。
3. **单点带宽**:6 个渠道全是"开一枪盯 1-2h 就走",没有持续运营——对比
   WorkBuddyGuide 五个作者共建。**处方:接受现实,把有限弹药全押转化率最高
   的动作**(架构文→复算墙→issue 入口的闭环路径),列表类渠道只投一次不再巡。

## 四、WorkBuddy 接入上线方案

**接入=两条路径,先 A 后 B**:
- **A(主路):WorkBuddy 的 MCP 配置接入**
  1. WorkBuddy 设置→MCP/连接器→添加自定义 MCP:
     - 本地:`python C:\Users\chunx\.claude\plugins\nautilus-compass\mcp_server.py`
     - 或云端:`https://compass.nautilus.social/mcp/`(Bearer token,免本地环境)
  2. **15 分钟真跑**(案例截图来源):会话 A 让 WorkBuddy 记住一个项目决策
     →新会话 B 零背景问同一问题验证召回→触发一条历史坑让 drift 告警
  3. 截图 3 张(召回命中/drift 告警/记忆文件落盘)
- **B(辅路):技能卡进 WorkBuddyGuide**——case 七段模板草稿已备
  (outreach_20260914_skillcard_drafts.md 草稿二),补上 A 的截图即可投 PR
- **注意**:若 WorkBuddy 仅支持白名单 MCP/自家技能商店,则 A 降级为 B 单路;
  真跑由用户执行(15 分钟),我们不编"实际效果"

## 五、ClawHub 推进状态

- 设备码已出(见会话),用户 2 次点击授权→即刻 publish→PR#43 链接升级
- 技能卡本体与 dry-run 均已就绪(9/14 验证)
