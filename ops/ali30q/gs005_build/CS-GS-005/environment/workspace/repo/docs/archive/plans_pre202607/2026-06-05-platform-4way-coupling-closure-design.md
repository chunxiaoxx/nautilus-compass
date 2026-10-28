# 平台 4-way 耦合闭环接线 · 设计(2026-06-05 · platform-soul dialog)

> 用户(2026-06-05):"把 平台+compass+soul+agent 真正耦合闭环接线,平台要承担这部分工作 · 可自愈可感知"。
> 对位 compass 同日的 `dual_flywheel_wiring` goal(compass own 检索/记忆/PoI)。本设计 = **平台侧 own 跨系统耦合 substrate**。
> 配套:`...closure.md`(TDD 计划)· `GOAL_2026-06-05_platform_4way_coupling_wiring.md`(/goal 起手包)。

## 0. 北极星 / 不变约束
- 平台 agent-first 生态(anchor #1);FDE+RSI 双轮按外部信号解锁(anchor #2 6/5 修订:对的客户=字节=双轮引擎,非 defer)。
- **反 D / ship≠价值 / 反 spray(anchor #3)**:接线钉在**唯一活回路 = FDE verdict 流**(data_001 已闭环),不接休眠能力、不发散。
- **gate 守住**:内部 NAU 自印经济(L4 `daemon.py:159-229`、`api/evolution.py`)+ fitness_delta gating = benchmark 弧证伪的自指陷阱,**非"与我们相关",仍 held**。其余承载 FDE/耦合信号的 = 接。

## 1. 总判定(audit grounded)
平台不缺能力,缺**接线 + 可感知 + 自愈**。审计(2 路 subagent + memory)结论:
- 真断裂可修:`daemon.py:685` P1 治理 KeyError(每 2h 崩烧 cycle)+ 双 ship 竞态(soul_executor 10min vs daemon P1 2h 抢 accepted,无 peek-claim)+ **soul 活动零读端点**(痛点根因:engine_cycle_outcomes 全写无读)+ LLM call 无 timeout。
- 可感知断裂:企业微信推送真实现(`api/wechat_bot.py:41` qyapi 真 token+send),但唯一定时推"痛点列表"非活动摘要,失败 `except:pass` 静默吞(`mind.py:263`/`platform_brain.py:427`)。
- 耦合现状:FDE verdict 走**共享文件**(`_v5_data001_real_verdict.json`)非平台 DB;跨对话框协调走 git 文件非平台 a2a_relay。组织 agent 优势"断裂"= 没走平台 substrate。
- 现成可复用(不新建):`engine/outcome_emit.py`(outcomes 写)· `api/a2a_relay.py`(send_message/poll_inbox/list_agents agent 消息中继)· `engine/a2a_review.py`(跨 agent 评审)· `api/tenants.py`+compass_sub 读权限。

## 2. 架构:平台 = 4-way 耦合 substrate(hub)
活 FDE 回路横跨 4 系统,今天跑在共享文件 + 不可见 DB 写上。闭环 = 路由进平台 substrate,持久化+可观测+自愈。
```
v5 copilot 产物 ─┐
                 ├→ [W1 平台 verdict-bus] → compass PoI(读)
soul QC verdict ─┘        │
                          ├→ [W2 平台 activity digest] → 企业微信 push 给用户(可感知)
agent/compass/soul ─A2A→ [W3 平台 a2a_relay send/poll · 复用 · 替文件传递]
                          └→ [W4 自愈: timeout+fallback + B1/B2 fix + 失败不静默吞]
```

## 3. 工作流(W1-W4 + GATE)
### W1 · verdict-bus(平台承担的耦合核心)
- 平台建 FDE verdict ingest 端点 + 表(复用 outcome_emit 模式;**新表 fde_verdicts**,不混 engine_cycle_outcomes 的内部 RSI 语义)。字段:task_uid/source(v5/soul)/checklist_uid/overall_pass/veto_failed/score/产物清单/created_at。
- v5 producer + soul checklist_scorer → POST verdict → 平台持久化 → compass 读(PoI 燃料,对接 compass T3)→ 进 W2 digest。
- **替代共享文件传 verdict**(`_v5_data001_real_verdict.json` → DB)。文件保留作 fallback/审计。
- gate:compass PoI live boost 仍 compass own(平台只供数据,不碰 compass 内部)。

### W2 · 可感知 digest + soul-activity 读端点
- 新只读端点 `GET /api/platform/soul/activity`:读 engine_cycle_outcomes + v_engine_progress + fde_verdicts + open soul draft PR 列表。纯 observability,**不碰 pending_nau_rewards/投票**(不触自指)。
- 新 `_daily_activity_digest()`(复用 `wechat_bot.py:351 _admin_platform_status`):组装"过去 N 小时:soul ship N cycle / FDE verdict M 条 / agent 进展 / open PR" → scheduler 注册 → 企业微信 push。内容=成绩+FDE 真进展,非痛点。
- 修 `except:pass` → `logger.warning`(失败不再静默)。
- 补 `api/platform_proposals.py:301 get_proposal` 返 resolution_note/resolved_by/resolved_at。

### W3 · A2A 耦合接线
- 跨对话框 FDE 协调消息(verdict ack / checklist ready / 批次状态)从 git 文件 → 走 `api/a2a_relay.py` send_message → poll_inbox。可观测(进 digest)+ 持久。
- scope 限 FDE 协调,不重建 A2A 协议。验证:soul→compass→v5 一条真协调消息经 relay 收发 + 出现在 activity 端点。

### W4 · 自愈
- B1 `daemon.py:685` P1 KeyError:P1 goal 补 description 适配(对齐 P2 `daemon.py:629`)。
- B2 双 ship 竞态:加 peek-and-claim(status accepted→claiming 原子 UPDATE)——与 B1 **同修**(单修 B1 暴露真双 ship)。
- LLM call timeout:LLMClient.chat / propose_fn 加 timeout(+retry)——backlog 兑现,防慢网挂死。
- 失败不静默:关键路径 except 记 warning。

### GATE(撞到停)
- G-held:内部 NAU 自印/fitness gating/gene 市场/bootstrap = 不碰。
- G-cloud:云端实测/DDL 需 SSH,无权限停报。
- G-turf:compass 内部 PoI/v5 copilot 内部 = 不碰,只接接口。
- G-DDL:生产 DDL / 公网 post → 停 + AskUserQuestion。

## 4. 数据流(闭环验证锚)
data_001 已闭环回放新路径:v5 产物 → soul QC verdict → **POST 平台 verdict-bus**(W1)→ compass 读做 PoI(对接 T3)+ **进企业微信 digest**(W2)→ 用户被动看到 → 跨框 ack 走 a2a_relay(W3)。全程平台持久+可观测+自愈(W4)。

## 5. 测试 / 验收(verification-before-completion)
- W1:mock verdict POST→DB→GET 回读 + compass_sub 能 SELECT 到。TDD red→green。
- W2:活动 digest 函数单测(给 fake DB 行→出成绩摘要非痛点)+ soul/activity 端点回读 engine_cycle_outcomes。**企业微信真发需运行时验证(G-cloud)**。
- W3:a2a_relay send→poll 往返单测 + 一条真 FDE 协调消息端到端。
- W4:B1 回归(P1 goal 不再 KeyError)+ B2 并发 claim 只一方得 + timeout 触发降级不破。
- 每步 TDD;改代码 using-git-worktrees 隔离;R4 git 检查;不 -A/push/force。

## 6. 边界 / 非目标(anti-spray)
- 不接休眠能力(gene 市场/bootstrap/L4)。
- 不重建 A2A 协议、不做 coze 式 agent onboarding 大改(列后续候选)。
- 不碰 compass/v5 内部实现,只接接口。
- 论坛质量门 = 机制设计问题,列后续,不在本 goal。
- KG 可视化 = 独立小工程,列后续。

## 7. 起手序
W4-B1/B2(先止血 daemon 崩)→ W1 verdict-bus(耦合核心)→ W2 可感知(痛点直解)→ W3 A2A(协调上 substrate)。按 `...closure.md` TDD task 执行。fresh session fire `/goal`。
