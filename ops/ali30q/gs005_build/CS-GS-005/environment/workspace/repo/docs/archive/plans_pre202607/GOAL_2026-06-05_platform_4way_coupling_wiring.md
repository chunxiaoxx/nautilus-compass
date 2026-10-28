# /goal 起手包 · 平台 4-way 耦合接线闭环(fresh session 入口 · 2026-06-05)

> 复制下方「/goal verbatim」段到 fresh session。底本:设计=`2026-06-05-platform-4way-coupling-closure-design.md`,计划=`2026-06-05-platform-4way-coupling-closure.md`,诊断=`memory/session_20260605_platform_4way_coupling_diagnosis_design.md`。

## /goal verbatim(粘这段)

```
/goal platform-4way-coupling-wiring

【北极星·不变】平台 agent-first 生态;FDE+RSI 双轮(anchor #2 6/5 修订:对的客户=字节=双轮引擎非 defer)。平台承担 compass+soul+agent 跨系统耦合 substrate。

【总判定·本 goal 根据】平台不缺能力,缺接线+可感知+自愈。活 FDE 回路(v5 产物→soul QC→compass PoI→用户感知)今天跑在共享文件+不可见 DB 写。本 goal=把它接进平台 substrate,持久化+可观测+自愈。复用现成 outcome_emit/a2a_relay/wechat_bot,不新建不发散。详见 docs/plans/2026-06-05-platform-4way-coupling-closure-design.md。

【lane·平台 own·不碰别框 turf】跨系统耦合 substrate(verdict-bus + 可感知 digest + A2A relay 接线 + daemon 自愈)。不碰 compass 内部 PoI/检索;不碰 v5 copilot 内部;只接接口。soul own RUBRIC/checklist_scorer。

【凭据·已备·读这个·值不回显】C:\Users\chunx\.claude\.cache\.fde_api_secrets.env(企业微信 corpid/secret/agentid 等)。

【可验证终态·全满足=done】按 docs/plans/2026-06-05-platform-4way-coupling-closure.md 的 TDD task:
  W4 自愈(先止血):W4.1 daemon P1 KeyError(daemon.py:685 补 description)· W4.2 双 ship peek-and-claim(与 W4.1 同修)· W4.3 LLM call timeout。每步 TDD red→green。
  W1 事件脊柱(耦合核心·平台 OWN·吸收 v5 event_outbox 设计 2a24ffa·防平行造轮子):W1.0 激活/接 event_outbox(sent→delivered→processed+consumer ack·复用平台现成 EventBus/a2a_relay·YAGNI 不上 Redis/Kafka)· W1.1 fde_verdicts 表 migration(verdict=脊柱第一类事件·本地·生产 DDL 停报)· W1.2 POST /api/platform/fde/verdict ingest+回读 · W1.3 compass_sub 读路径验证(对接 compass T3 PoI)。**跨框对齐:平台供脊柱+envelope/ack 合约·v5 接 producer/consumer·compass 接 PoI consumer·三框 buy-in 后再 build,不各造一套。**
  W2 可感知(痛点直解):W2.1 GET /api/platform/soul/activity 只读端点(读 engine_cycle_outcomes/fde_verdicts/open PR·不读 NAU/votes)· W2.2 _daily_activity_digest 组装(成绩非痛点·复用 wechat_bot.py:351)· W2.3 scheduler 注册推送+修 except:pass 静默吞 · W2.4 get_proposal 补 resolution_note。
  W3 A2A 耦合:W3.1 FDE 协调消息走 a2a_relay send/poll(可持久可观测·接 W1 事件脊柱)· W3.2 data_001 真 verdict 端到端回放新路径(closure 验收锚)。
  W5 对外可用化(分层·大方向先 spike 不盲建):W5.1【spike·先调研后决策】调研 coze.cn/n8n + 定义"如何让别人用我们产品/服务"最小自助面(网页交互 + 本地化 agent 部署 + skills.md 注册即用)→ 出 build-vs-集成推荐 design,不本 goal 盲建大产品 · W5.2 skills.md/capabilities manifest 只读端点(GET /api/platform/skills·agent 自助 onboarding 入口·register-post-use 第一步)· W5.3 论坛质量门(square create_post 加内容质量门·超 reputation spam gate·square.py:120)· W5.4 KG 可视化(知识图谱 json→可读 HTML 概览·复用 5 个现成 KG)。W5 全程 anchor #3:小件可 ship·大产品方向只出 spike 推荐等用户拍。
  W6 RSI 反馈环(实现双轮 RSI 半边·gated·见 docs/plans/2026-06-05-rsi-fde-closed-loop-design.md):W6.1 soul checklist_scorer 出 per-item fail_reason(当前只 pass/fail)落 verdict-bus items.reason · W6.2 compass fail_reason→避坑语料库(按领域/题型可检索·复用胶囊管线) · W6.3 v5 producer 下一题 retrieve 避坑规则注入 grounding(systematize shared_facts)。创新点=外部 verdict 失败→结构化 grounding→喂 producer 输入→下一 verdict 度量(非 self-edit·非内部 NAU·避 Probe3 死法)。先建管道+mock·**G-rsi:data_002→003 首验假说证实前不 live wire**。

【gated 边界·撞到停+报+不空转】
  G-held 不碰内部 NAU 自印(daemon.py:159-229 L4 · api/evolution.py)/fitness_delta gating/gene 市场/bootstrap = benchmark 弧证伪自指陷阱,非"与我们相关"。
  G-cloud 生产 DDL apply / 企业微信真发 / 云端实测需 SSH → 本地验,生产停报。
  G-turf compass 内部 PoI/v5 copilot 内部 → 不碰只接接口。
  G-align W1 事件脊柱跨 turf(consumer 在 v5/compass/soul)→ envelope/ack 合约须三框 buy-in 再 build,不 platform-solo 定死(对位 v5 同款诚实:防平行造轮子)。
  G-spike W5.1 大产品方向(coze/n8n/网页交互/本地 agent)只出调研+推荐,不盲建 → 等用户拍 build-vs-集成。
  G-rsi W6 RSI 反馈环 data_002→003 首验假说(grounding 注入让 pass 率↑)证实前不 live wire → 只建管道+mock。fitness 只外部(soul QC/字节接收)·绝不内部 NAU·绝不 self-edit prompt(Probe3 死法)。
  G-DDL 生产 DDL/公网 post/改别框 turf → 停 + AskUserQuestion。

【每个增量纪律】
  · 改代码 using-git-worktrees 隔离,不污染 main;ship 前 R4 git 检查;不 -A/push/force。
  · verification-before-completion:W1/W2/W4 本地 TDD green + W3.2 data_001 回放全链通才标 done;生产 apply 卡 G-cloud 如实标"待 SSH"。
  · 不碰 held 内部自指(anchor #3);不重复造轮子(outcome_emit/a2a_relay/wechat_bot 复用)。
  · R1 drift / R2 全做 / R3 4h / R5 anchor 触发即停。
  · 每轮一句话报:做了 Wn 哪 task + 验证证据(file:line/命令输出)+ 下一步/撞哪个 G。
  · 「真」不作强调副词;凭据值永不回显/不入 git。

【DONE】W4 止血 + W1/W2 本地 TDD green + W3.2 data_001 回放全链通 + W5.2/5.3/5.4 小件 green + W5.1 spike 推荐出 + W6 反馈环管道+mock 建好(live wire 卡 G-rsi 等 data_002→003 首验)+ 设计/计划行更新;或生产 apply 全卡 G-cloud/别框 → 停报等用户 SSH 授权。事件脊柱合约卡 G-align → 出提案等三框 buy-in。

【起手序】W4(自愈止血·先稳)→ W1(事件脊柱/verdict-bus·收敛核心)→ W2(可感知)→ W3(A2A 接脊柱)→ W6(RSI 反馈环·建管道+mock·gated)→ W5(对外可用化·spike+小件)。前 4 个 = 用户聚焦的"收敛闭环+稳定可靠"·优先;W6/W5 在其后。
```

## 关键 file:line 锚点(执行用)
- daemon P1 KeyError:`phase3/agent-engine/soul/daemon.py:685`(ship 取 goal["description"])· P2 适配范例 `daemon.py:629-630` · codegen-friendly task 封装 `daemon.py:559-564`
- 双 ship:`soul_executor.py`(10min timer)vs `daemon.py` P1(2h)抢 `status='accepted'` · `goal_stack.py:34-40` 记录
- verdict-bus 复用:`engine/outcome_emit.py:30-80`(写模式)· 新表 fde_verdicts 别混 engine_cycle_outcomes
- 可感知:`api/wechat_bot.py:41`(qyapi)`:351`(_admin_platform_status 复用)· 静默吞 `mind.py:263`/`platform_brain.py:427` · scheduler `scheduler.py:44` · get_proposal `api/platform_proposals.py:301-313`
- A2A relay:`api/a2a_relay.py`(send_message:57/poll_inbox:102/list_agents:134)· `engine/a2a_review.py`
- 跨系统:compass_sub 读 engine_cycle_outcomes(memory)· `api/tenants.py`

## 与 compass goal 的分工
- compass `dual_flywheel_wiring`:检索/记忆生产接线 + FDE verdict→PoI adapter(读端)+ 专家复核回路。
- 本 goal(平台):提供 verdict-bus(供 compass 读)+ 可感知 digest + A2A substrate + daemon 自愈。**两 goal 在 verdict-bus 接口对接**(平台供数据·compass 做 PoI)。
