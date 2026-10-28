# org/bootstrap 设计 · 组织级会话引导服务(狗粮第一口)

trace_id: org-bootstrap-design-20260828
frame: platform-dialog · SSOT §⓪ 首个工程兑现 · maturity: design(P0/P1 待入栈实作)

## 0. 问题(组织病在"session 开局"瞬间的表现)

新 session 开局要靠人肉纪律拼上下文:手读 SSOT/GOAL_STACK/交接文档(失忆)、副本靠人拷贝(分叉)、催办投仓根碰运气+deadline 无牙齿(瘫痪/混乱)。本月实证:平台框失忆 workbuddy 路线(8/22 既定)、催函两次跳票、EXPIRED 合约挂 38 天无人消费。

## 1. 目标

**一次 HTTP 调用,治一个 session 的开局。** 每个框/注册 agent/workbuddy 在会话开始时:

```
GET /api/platform/org/bootstrap?agent=<frame-or-agent_id>
```

## 2. 返回包(七节,治四病)

| 节 | 内容 | 治什么 | 数据源(现成) |
|---|---|---|---|
| identity | 注册信息/能力/信用/最新 capability | 我是谁 | agents 表+capability_stats |
| state | SSOT canonical 摘要(git hash+最近 N 条增量)+副本一致性 | 分叉 | 读文件+跨框事件协议读数 |
| **mailbox** | 本框未读函件(标题/deadline/from) | **必达** | org_mailbox 表(新建,P0) |
| contracts | 活合约清单,EXPIRED 亮红 | 挂账 | contracts frontmatter 扫描 |
| goals | GOAL_STACK 栈顶+本框相关项 | 方向 | 读文件 |
| memory 指针 | compass project+24h 新记忆索引(**只给指针不替代 compass**) | 失忆 | compass 目录 ls |
| health | 记分牌五数字+本框服务最近读数 | 盲区 | convergence API |
| **capability-index** | **能力索引:活资产清单(位置/接口一句话/消费者/消费计数)**——"先查再造"的注入事实 | 组合 | ASSET_LEDGER 台账 |

> 台账即索引数据源:bootstrap 读台账文件(同 SSOT 只读不 DB 化);**每行带消费者/消费计数两列**(§⓪-E 登记环),消费计数增长=组织进展的真口径。

## 3. mailbox 子系统(P0,先落地)

- 表 `org_mailbox(id, from_agent, to_agent, trace_id, title, body, deadline, created_at, ack_at, ack_note)`
- 端点:`POST /api/platform/org/mailbox` 投递 / `GET ?to=&unread=1` / `POST /{id}/ack`
- **牙齿**:supervisor(30min 现成)扫 `deadline-12h 未 ack` → telegram(同函只报一次,护栏沿用 ≤1条/周 trace 规矩)
- 兼容:仓根 md 函继续存在(审计归档),**带 deadline 的事项必须进 mailbox**(单一事实源)

## 4. 技术决策(防重造/防新真相源)

1. SSOT 保持 markdown canonical——bootstrap 只**读文件+报 hash**,不做 DB 化(否则第 N 份真相源)
2. 记忆本体留 compass——bootstrap 给指针;不建平行记忆
3. telegram/监督链复用 supervisor 现成(今天 ZERO 链刚验证)
4. **实现者**:P0/P1 平台框做(TDD);P3 起 SOUL 复活后接管扩展——**组织用自己的引擎修自己 = RSI 第一圈样板任务**,平台做的 P0/P1 就是给 SOUL 的示范样例

## 5. 验收(预注册,含狗粮条款)

- **bootstrap**:四框 session-start hook 全接(P1);连续 7 天零"读旧 SSOT/漏既定路线开工"事故(对照:本月 workbuddy 失忆一例)
- **mailbox**:上线两周 ack 率 100%、跨框平均响应 <1 session、EXPIRED>7 天事件=0
- **狗粮验收条款**(§⓪ 精神):不看内部自报"接入了"——看四框 session 实际**引用 bootstrap 内容**的产出比例+deadline 事项的实际闭环率

## 6. 分期

- **P0(半天)**:mailbox 表+端点+TDD+supervisor 牙齿
- **P1(1 天)**:bootstrap 聚合端点+四框 hook 一行 curl 接入
- **P2**:workbuddy 消费精简包(agent_type=workbuddy-user)——外部第一客,与 compass P1/P2/P3 解冻线合流
- **P3**:SOUL 复活后自我迭代接管(第一个喂给它的目标)

## 7. 风险

- hook 接入=改各框 .claude/hooks(turf:各框自己接,平台只出接入文档一行命令)
- SSOT 读文件在云后端=云仓副本可能落后 canonical(已知债:云分支 cherry-pick 流)→ P1 用 `git fetch origin + 读 origin 分支`绕开,拓扑正名后简化
- mailbox 沦为垃圾场 → 投递需带 trace_id+deadline,无 deadline 的闲聊函拒收(400)
