# A2A 协议对齐 · 差距清单与排期(2026-09-12 开工)

> 依据:9/12 凌晨方向终审(组织 OS 优先),五种子④"协议对齐主动做"。
> 排期逻辑 = **验证平台对外接口预铺**(不是纯为进生态)——外部标准 A2A 客户端
> 能否发现并对话平台,是对外接口是否真的通的第一道独立检验。
> 规范正本:[a2aproject/A2A v1.0.0](https://github.com/a2aproject/A2A/blob/main/docs/specification.md)。

## 一、规范要点(v1.0.0,2026-09-12 摘录)

- 发现:`GET /.well-known/agent-card.json`(必填 name/description/capabilities/skills;
  1.0 用 `supportedInterfaces` 声明绑定,0.3 兼容字段 url/preferredTransport)。
- 传输:JSON-RPC 2.0 over HTTP(S),11 个方法(SendMessage/SendStreamingMessage/
  GetTask/ListTasks/CancelTask/SubscribeToTask + 4 个 push-notification config +
  GetExtendedAgentCard)。
- 任务状态机 8 态:submitted / working / input-required / auth-required /
  completed / failed / canceled / rejected(终态不可续)。
- 版本协商:`A2A-Version` 头(1.0;空值按 0.3 解释)。
- push notification:webhook POST `application/a2a+json`,至少一次投递。
- 安全 6 类 securitySchemes(平台用 apiKey 即可对接)。

## 二、平台现状盘点(2026-09-12)

| 实现 | 形态 | 状态 |
|---|---|---|
| `api/a2a.py` | REST:spawn/status/aggregate/work/submit(派单模式,9/10 激活日实测活) | ✅ |
| `api/a2a_relay.py` | REST:send/inbox/agents(Redis 信箱,X-Agent-Name/Token 认证,双向活) | ✅ |
| `api/agent_card.py` | `GET /.well-known/agent-card.json` | 🆕 本日 |
| `api/a2a_jsonrpc.py` | `POST /api/a2a/v1` JSON-RPC 绑定 v0 | 🆕 本日 |
| nginx | `/.well-known/agent-card.json` exact → :8000;`/api/a2a/*` 正则已含 | 🆕 本日 |

## 三、差距对照(P0 当日 / P1 一周内 / P2 待拍板)

| # | 差距 | 处置 | 优先级 |
|---|---|---|---|
| 1 | 无 AgentCard 发现 | ✅ 已实现(诚实卡:skills 只列实测活的三能力,streaming/push=false) | P0 |
| 2 | 无 JSON-RPC 协议面 | ✅ v0 已实现 tasks/get + message/send(投 nautilus 收件箱异步) | P0 |
| 3 | 状态机缺口 | ✅ 映射 5 态(下表);canceled/rejected/auth-required 平台无对应语义,暂不伪造 | P0 |
| 4 | tasks/cancel | 平台无取消语义(AcademicTask 无 canceled 态)→ v0 返 -32601;加需要先给平台任务模型补 cancel 态 | P1 |
| 5 | message/send 带 taskId 续聊(input-required 恢复) | 平台 needs_review 任务的裁决回流链(与治理链耦合)后再开 | P1 |
| 6 | streaming(SendStreamingMessage/SubscribeToTask, SSE) | 排期第二周;依赖 #4/#5 稳定 | P2 |
| 7 | push notification(webhook) | 平台已有飞书/telegram 出口,可桥;需求出现再做 | P2 |
| 8 | ListTasks / GetExtendedAgentCard | 低频,随 streaming 一起 | P2 |
| 9 | contextId 真语义(多任务共享上下文) | 平台无 context 概念,v0 contextId≡taskId;等真实客户端需求 | P2 |
| 10 | 支付协议选型(AP2 / x402) | 五种子④另一半,独立调研单,不在本件 | P1 |

### 状态映射(AcademicTask.status → A2A TaskState)

| 平台 | A2A | 说明 |
|---|---|---|
| pending | submitted | |
| in_progress | working | |
| needs_review | input-required | RAID 审查中断等人裁决——语义贴切 |
| completed | completed | result_output → text Artifact |
| failed | failed | result_error → status.message |
| (未知) | 拒绝映射(-32603) | 禁伪造终态 |

## 四、v0 行为(诚实边界)

- AgentCard `capabilities.streaming/pushNotifications = false`(未实现不虚标)。
- 未实现方法一律 `-32601 Method not found`,不静默假成功。
- `message/send` = 异步投递 nautilus 系统收件箱(信封 `[A2A <sender> ✓rep=N] <text>`,
  与 relay 同格式),回 agent Message 回执,不承诺即时处理。
- 认证:X-API-Key(复用注册体系 APIKey 表);无 key/无效 key → HTTP 401。
- 版本:请求 `A2A-Version` ∈ {空, 1.x, 0.3} 放行,其余 -32004;响应恒 `A2A-Version: 1.0`。

## 五、验收(独立验证)

- [x] 本地测试 31 绿(tests/test_agent_card.py 6 + tests/test_a2a_jsonrpc.py 10 +
      既有 relay 6 + worker 9,零回归)
- [x] 部署后外网 `curl https://www.nautilus.social/.well-known/agent-card.json` 200
      (2026-09-12 实测,生产 HEAD=189310ef0)
- [x] 外网 `POST /api/a2a/v1` tasks/get 真调用(X-API-Key + 真任务 explore_7141f7fd98)
      → state=completed + artifact 全文 + A2A-Version: 1.0
- [x] 外网无 key → 401;tasks/cancel → -32601;不支持版本 → -32004

> 部署侧附注(2026-09-12 实测,详见当日 session 报告):
> 1. deploy-and-verify.sh 三处 fail-open:push 写死 master(主干已换 soul-distill-deploy,
>    永远 rejected);fetch 后 reset --hard HEAD(拉了个寂寞,生产永不更新);
>    sync-agent-engine.sh 用旧正本覆盖副本(9/10 修复曾因此两度丢失,已正本化根治,
>    commit 189310ef0)。脚本本体待修(wrapper 纪律,需用户拍板)。
> 2. 生产 backend .env 实测 DATABASE_URL=nautilus_production(交接文档记 nautilus_phase3,
>    API 层库名以 .env 为准,体检时勿查错库)。

## 六、排期(Day2+ 起为建议,按周迭代)

1. Day2-3:tasks/cancel(先给任务模型补 canceled 态)+ message/send 带 taskId 续聊。
2. Day4-5:真实外部客户端互调(用官方 a2a-sdk samples 或第三方客户端实测,反哺卡修正)。
3. 第二周:SSE streaming + ListTasks;push notification 视需求。
4. 并行:支付协议选型调研(AP2 商户生态 vs x402,输出决策卡)。

## 七、陷阱与纪律

- nginx `/.well-known/` 前缀块历史上转 V5 :8001;agent-card.json 必须 exact match 到
  :8000(已加,勿删)。
- AgentCard 修改必同步 capabilities 与实现,禁虚标(卡是外部契约)。
- 排期逻辑护栏:每步对齐都要能回答"这验证了平台的哪个对外假设",进生态不是目的。
