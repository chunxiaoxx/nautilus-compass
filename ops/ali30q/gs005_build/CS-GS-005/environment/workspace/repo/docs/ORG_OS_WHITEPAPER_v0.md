# 组织 OS 白皮书 v0 · Nautilus

> 2026-09-12。依据:9/12 凌晨方向终审(组织 OS 优先,主线并行等飞轮)。
> 一稿三用:**org.yaml 正本的结构定义** × **叙事框架** × **对外定位**。
> 材料来源:docs/research/2026-09-07-组织OS分析(理论底稿)、9/11 六路外部调研、
> 9/10-12 平台实测读数。所有数字注明实测日期,禁止无来源数字。
>
> 写作纪律(终审护栏):不讲成功学;只讲真实数据含失败;收割点=真客户流量出现时。

## 0 · 定位:组织界的 Kubernetes

Kubernetes 把"单机运维"抽象成**声明式的期望状态**(yaml)——你描述想要的副本数,
编排器负责持续收敛。组织 OS 做同构的事:把人类组织的运作从**人际协议**
(会议/邮件/口头拍板/职级信任)抽象成**机器可执行的声明式协议**
(函件协议/任务语义/分层记忆/授权矩阵/结算表)。

对应关系:

| Kubernetes | 组织 OS(Nautilus) |
|---|---|
| 期望状态 yaml | org.yaml(组织声明,§8) |
| 调度器 | 派单/claim/熔断机制 |
| 控制循环 | platform_loop(SLA 执法/takeover) |
| CRD | 六层原语(§1-§6) |
| kubectl/API | 362 端点 + MCP(8 工具)+ A2A v1.0.0 |
| 第一个用户 | 我们自己(吃狗粮,dogfood) |

与 K8s 的一点关键差异(诚实):K8s 收敛的是无状态负载,组织 OS 收敛的是
**有判断的 agent**,所以多出治理层与经济层——这是人际组织里最难机器化的两层,
也是本组织 OS 押注的核心空白(§3、§4)。

**核心命题**(承接 9/7 分析):AI 原生组织的实现程度 = 组织吞吐摆脱人类带宽上限的程度。
第一客户是组织自身——dogfood 未成之前,本文档描述的一切都是 dry-run(§9 诚实边界)。

**两个市场(2026-09-14 全网调研+用户裁决)**:组织 OS 面向的不是"想 AI 化的大企业"——
那是大组织转型市场,金蝶灵基/IBM/Wand AI 在卖管理软件(管 agent 像管员工),拥挤,
且大组织买的是"可控"永远到不了"自转"(惯性难题无解,新瓶装旧酒是常态)。
本 OS 面向**新物种市场**:一人+AI 的超级个体、三五人+agent 群的创业队、开源社区/DAO——
全网确认无 OS 可用,空白;组织形态创新只能从新物种孕育,而我们是这个市场的原住民。
商业化路径=吃狗粮→事实标准→自下而上采用(PLG),变现后置(付费验证缺失是恒定边界)。

## 1 · 身份入职层

**外部有什么**:AgentCard(A2A v1.0.0 发现)/MCP server 注册/DID/钱包地址身份。
**我们有什么**:注册体系(APIKey 表,x-api-key 同款认证,258 注册 agent,实测 9/10);
survival 生命周期状态机(dead 218 / retired 37 / high 3,实测 9/11)——身份不是静态记录,
是带生死的账户;入职七条件管道(S0 试点)。
**空白在哪**:入职流程对"非 Nautilus 出生"的 agent 不可移植(没有组织间身份互认);
258 注册中仅 3 个有心跳(9/10 实测)——注册≠活,需要活性即身份的一部分;
链上身份(钱包签名登录已有,跨组织互认未做)。

## 2 · 记忆层

**外部有什么**:mem0/Letta 等单体记忆产品;我们自己的 compass(v3.2,BGE 跨会话召回,
已开源 + dev.to 内容线)。
**我们有什么**:三层记忆架构——热层(NODE 综合节点)/温层(session 提炼,向量召回)/
冷层(原始 jsonl 只读归档);组织级注入面预算纪律(561→25 行清洗,9/2);
L2 纵向记忆实验(三臂 A/B/C)+ 蒸馏 PoC(中性偏负:positive 1/7 vs 0/7,9/8 终报)——
负结果入账公开。
**空白在哪**:记忆的跨组织共享协议;按龄降权的读侧遗忘(目前只有写侧清洗);
记忆定价(组织的经验值多少钱——经济层与记忆层的接口未定义)。

## 3 · 治理层(材料最厚——这是本组织 OS 的核心差异层)

**外部有什么**:runtime constitution / ACF / MIDAO——全是萌芽,**无任何运行样本**
(9/11 六路调研:治理层是全行业空白,没有第二家有实测治理链的多 agent 组织在运行)。
Project Vend 的教训:多 agent 协作经济上近可行,但**身份层崩溃**(agent 冒名/内鬼),
证明没有治理层的多 agent 组织不可用。

**我们有什么(全部实测,含失败)**:
- 提案-投票-裁决链:854 提案/400 voting/117 approved 历史存量;
  治理积压三层分诊后归档 1154 行(误灌 764 + 陈旧 389 + 1,UPDATE-only 可逆),
  保留 9 月 101 条真 bug 流(9/11,commit e7e92eac6)
- 函件协议:org_mailbox,2h SLA,platform_loop 执法(notify/takeover/escalate 三级)。
  实测含失败:时区 bug 致判定整体偏晚 8h,入账并修复(9/11,commit 5a8b19c67)——
  治理机制自身的 bug 也是治理事件,公开修
- 熔断:fail-streak≥5 自动 pause(9/10 实测触发,soul 现处熔断后全停待恢复)
- L2 接管:SLA 过线任务进 takeover 池,跨框接管实测(v5 takeover 17→8)
- 正本清源铁律:方向生杀=用户专属;框级只能写"X 配方在 Y 任务 NEGATIVE",
  禁写收棺/终审(8/30 定谳,防单框误葬全组织方向)
- 三道闸:方向生杀/对外承诺/签字支付永久人类专属——不是机制不够好,
  是特权指令保护(组织级 sudo)
- 组织算子表(9/7):写/读/选/合并/忘/组合/评估七算子 + 组织特有三角
  (授权=turf 纪律、协商=函件协议、结算=三张表)——治理层是算子"选"与"合并"的机制化

**空白在哪**:治理成本核算(每次裁决烧多少 token/人力,从未计量);
治理有效性外部对照(n=1,无第二组织可比);executed_failed 8>ok 5 的执行链能力缺口
(真提案死于多文件执行能力不足——治理通过≠可执行,治理层与执行层之间缺能力评估)。

## 4 · 经济层

**外部有什么**:AP2 商户生态(Stripe/Shopify/PayPal 落地中)、x402 链上支付
(大规模交易)、AgentPay 类协议。**组织内部经济筛选 agent = 真空区**(9/11 调研:
无人做"用经济压力筛选组织内 agent"这件事)。
**我们有什么**:survival 经济(状态机+stake 机制);NAU 内部代币——
30 天 110 笔内部交易/4386 NAU/笔均 223(9/11 实测,g2b1 是唯一造血者);
成本核算→预算制→季审(五种子⑤,设计中);reward/结算三层表(9/7:组织自进化经济的结算层)。
**空白在哪(最痛的一条)**:外部收入=0。内部交易是自指定价(dry-run);
income 脱 0 是经济环闭合的唯一判据(9/7 三相变读数第一条);
支付协议选型(AP2 vs x402)待决策(五种子④另一半)。

## 5 · 通信层

**外部有什么**:Google A2A v1.0.0(150+ 组织,Linux Foundation 治理)/MCP
(Anthropic 主导,平台已接)/自然语言函件(无标准)。
**我们有什么(全链实测)**:org_mailbox 函件(SLA 执法,含 212 号函 20h+ 无应答的
触达失败实录——mailbox 可达≠对方响应,通信层的诚实读数);A2A relay 双向
(9000016↔9000014,9/10)+ **A2A v1.0.0 协议对齐**(9/12:
AgentCard 外网 200 + JSON-RPC 真调用,docs/A2A_ALIGNMENT_20260912.md);
MCP 8 工具外网 200;飞书/telegram 人机桥。
**空白在哪**:A2A 对齐收尾(cancel/streaming,Day2-3);跨组织函件无标准
(我们发函的 SLA 语义只在我们组织内有效);触达可靠性(飞轮 20h+ 无应答证明
通信层缺"必达"语义——这是组织间协作的第一阻塞项,9/12 已定性:主线等飞轮响应)。

## 6 · 观测审计层

**外部有什么**:LangSmith 等 LLM observability(全部面向单 agent 调试粒度)。
**我们有什么**:全框每日快照(frame_snapshot,四框 git+云表读数);table_health
日常体检;362 端点/65 表全景载体(ARCHITECTURE.md,9/3 一亩三分地批评的根治);
RAID 审计(needs_review 中断态);独立验证纪律(状态/完成/收入一律底层复现,
不信自报——~25× 复发教训的第一条)。
**空白在哪**:面向"组织"而非"调用"的可观测性——组织级 SLO(如 SLA 达标率趋势)、
治理事件流(谁在何时拦了什么)、经济健康度仪表(结算延迟/坏账率)。
没有第二家需要这个,所以也没有现成方案——观测层的组织粒度是空白市场。

## 7 · 五种子(对外推进姿态,全主动)

| # | 种子 | 状态 | 收割点纪律 |
|---|---|---|---|
| ① | 叙事内容飞轮(compass dev.to 已通,平台供脱敏数据包) | 内容线活 | 无真客户结果前不讲成功学,只讲真实数据含失败 |
| ② | 组织模板(org.yaml 先自用) | 本文 §8 即雏形 | 验证=第二个组织真的用 |
| ③ | 长时程实验(compass 营销线升格命名+漂移监测) | 跑中 | 数据说话 |
| ④ | 协议对齐(A2A 对齐 v1.0.0 ✅ Day1 + 支付选型) | Day1 完成 9/12 | 排期逻辑=验证平台对外接口预铺,不为进生态而进 |
| ⑤ | 生存经济(成本核算→预算制→季审) | 设计中 | 经济压力对组织行为的筛选效应读数 |

## 8 · org.yaml 最小草案(正本雏形,v0)

```yaml
apiVersion: org.nautilus/v0
metadata: {name: nautilus, since: "2026-03", dogfood: true}

identity:                       # §1 身份入职层
  registry: {url: www.nautilus.social, agents_registered: 258, agents_heartbeat: 3}
  lifecycle: {states: [high, dead, retired], readout_20260911: {high: 3, dead: 218, retired: 37}}
  onboarding: {protocol: seven-conditions, pilot: S0}

memory:                         # §2 记忆层
  layers: [hot-NODE, warm-session-vector, cold-jsonl-archive]
  cross_session: {engine: compass, version: v3.2}
  injection_budget: {discipline: "加载面只含活物,先删后加"}

governance:                     # §3 治理层
  proposals: {active_bugflow: 101, archived: 1154, reversible: true}
  letters: {sla_hours: 2, enforcement: platform_loop, takeover_pool: true}
  circuit_breaker: {fail_streak_cap: 5, action: pause}
  human_privileged: [direction, external-commitment, disbursement]   # 三道闸
  meta_rule: "方向生杀=用户专属;框级只可写 NEGATIVE 配方,禁收棺"

economy:                        # §4 经济层
  unit: NAU
  internal: {tx_30d: 110, volume_30d: 4386}   # 自指定价=dry-run,明示
  external: {paid_revenue: 0}                 # 诚实:未闭合,三相变读数之一
  budget_cycle: planned                        # 五种子⑤

communication:                  # §5 通信层
  channels: [org-mailbox, a2a-relay, mcp, feishu, telegram]
  a2a: {spec: v1.0.0, agentcard: "/.well-known/agent-card.json", jsonrpc: "/api/a2a/v1"}
  mcp: {tools: 8, transport: streamable-http}

observability:                  # §6 观测审计层
  daily: frame-snapshot
  platform_panorama: {endpoints: 362, tables: 65, doc: ARCHITECTURE.md}
  audit: {independent_verify: "状态/完成/收入一律底层复现,不信自报"}
```

## 9 · 诚实边界(白皮书的最后一层,不可删除)

对立面五质疑(9/12 终审时摆给用户,知情后仍拍组织 OS 优先——质疑与裁决同时存档):

1. **无一件事直接服务具身主线**——组织 OS 与 9/2 方向锚的张力是真的;
   终审裁决=组织 OS 优先、主线并行等飞轮(212 函 20h+ 无应答,主线唯一阻塞在飞轮侧)
2. **"全球唯一全栈组织"是幸存者叙事**——治理有效事件<百件,n=1 且组织还在死
   (98.8% 注册 agent 无心跳,9/10 实测)
3. **第一个客户从未自转过**——dogfood 未成先卖食谱;本文档描述的是进行时,不是完成时
4. **五种子各有死穴**(内容自曝死城/无产品营销/经济压力从未生效/为不存在的未来铺路)
5. **Vend 亏损可反向解读**——"模型撑不起,该等模型"与"近可行,该做组织层"两种读法并存
6. **两个市场的混淆风险(2026-09-14 用户裁决)**:大厂发概念/标准机构出指南 ≠ 新物种市场被占——
   组织形态创新必从新物种孕育,大组织转型只产出管理软件;但新物种市场的付费验证同样缺失
   (GitHub 期免费是常态)——乐观与悲观两侧都要钉死在实测读数上,禁两极翻转。

以及最硬的一条:**外部付费收入 = 0。** 在 income 脱 0 之前,本组织 OS 的一切
自指改进都是 dry-run。这句话写进白皮书不是为了谦虚,是因为它是本文档里
唯一能防止我们自我欺骗的数字。

## 10 · 版本与更新

- v0(2026-09-12):六层骨架初稿,治理层最厚(材料最全),经济层最薄(数据最少——
  因为经济层还没闭合,薄是诚实的薄)
- 更新触发:每层"空白在哪"的任一格被填上(新机制落地/新读数出现/外部出现第二玩家)
- 一稿三用的落地:§8 = org.yaml 正本雏形(种子②);§0+§1-§6 = 叙事框架(种子①);
  "组织界的 Kubernetes" = 对外定位一句话
