# Fresh Session 提示词 + 收敛/防遗忘机制(platform-soul · 2026-06-10)

> 上个 session(接地平台整合控制台 + 引擎诊断 + soul-cycle-B 设计)收口。本文件 = 下次 session 的单一入口:粘 /goal + 钉死"如何收敛闭环"+"如何不遗忘"。

## 一、/goal 提示词(直接粘贴)

```
/goal 我是 platform-soul 对话框。北极星 = RSI+FDE 外部客观闭环:ΔReward/escapes/买方 verdict 是 fitness,绝不用内部 NAU/自评(自指已证伪)。session-start 必读 nautilus-core/FDE_BUSINESS_CHARTER.md + 记忆 session_20260609_grounding_platform_bridge_v1_binding_done.md。

【已就绪·别重做】接地平台整合控制台已建成+部署生产 LIVE:control-plane 聚合脊柱(GET /api/platform/control-plane)+ /control 页(脉搏/verdict/编队/Soul活动/Grounding feed/RSI ΔReward 板块 + 治理写交互[投票/autonomy/execute·admin门] + 系统拓扑图 + drill)。登录修通。dashboard 已"说真话"(soul_alive 按真实 engine cycle 算·非硬编码)。fde_grounding/fde_rsi_delta 路由生产 LIVE。PR #129-133 全 merged。设计/诊断在 docs/plans/2026-06-10-*.md。

【本 session 目标·优先级·每件 binding-DONE】
1) 🔴 soul-cycle-B P1(keystone·救活空转的自改飞轮):据 docs/plans/2026-06-10-soul-cycle-b-external-fitness-flywheel-design.md 建最小可证伪——一个 config-space self-edit 跑 AutoLab radix harness → grounding_probe_twosample 算 ΔReward → escapes_noise=True 才 merge 否则 discard。复用 grounding_probe/fde_rsi_delta/AutoLab env·不重造。binding-DONE:escapes=True 候选 merge+落 fde_rsi_deltas / escapes=False discard。
2) FDE durable 回写:scorer(/home/ubuntu/soul-scorer/services/fde_scorer_runner.py)打分后 flip fde_dispatch.status produced→settled。
3) pulse 区分"内部 cycle 已弃用 by design" vs "down";soul 心跳改读外部 FDE 活动。
4) control-plane _provenance_section 接 V5 GET /provenance + 舰桥①按 agent_kind 渲染 + deprecate platform_agents.evolution_score/mutation_log facade 列。
5) 舰桥 v3(低优):5 子系统深挖/time-travel/角色层。

【跨框】V5 五件协调全 ACK(provenance schema 含 fitness_ref+agent_kind)。compass cnt_c3(ΔReward→PoI·due 6/11)。两份裁定 outbound 在 nautilus-core 根(转发 V5)。

【🔴 生产 gotcha】① cloud backend 在分叉分支 soul-audit-increment1(/home/ubuntu/nautilus-mvp)·外科 scp 不 pull master ② 前端 build 必带 canonical .env(VITE_API_URL=https://www.nautilus.social 裸origin·否则双/api→登录挂)③ 新建表必 ALTER OWNER TO nautilus_user ④ alembic 在 cloud 坏·建表用裸SQL ⑤ backend 日志 /var/log/nautilus-backend{,-error}.log ⑥ 浏览器MCP用 host.docker.internal ⑦ admin=CONTROL_ADMIN_EMAILS(含 chunxiaoxx@gmail.com)⑧ 本地 postgres 5433·main.py 本地不可import(wiring 源级测)。

【纪律】subagent-driven(每件 fresh subagent+TDD+审)·binding-DONE 实测 endpoint 才算完·scope 冻结(v3 parking-lot)·不烂尾不剧场·复用不重造·worktree 隔离。
```

## 二、如何确保 goal 收敛闭环落地(不发散烂尾)
复发根因(feedback_workflow_lock):工作流一直扩展/分歧、永不闭环。解药 = 把闭环做成**强制机制**,不靠自律:
1. **binding-DONE 判据写死**:每件目标列出"怎样算完"= 实测 endpoint/curl/浏览器(不是"我以为 OK")。没过判据不进下一件。本 session 全程这么做(40 TDD、curl 实测、浏览器验)。
2. **scope 冻结 + parking-lot**:v3(拓扑深挖/time-travel/角色层)明确 defer,不在本轮碰。新冒出的想法 → 记进 parking-lot,不当场扩。
3. **一次只闭一条线**:soul-cycle-B P1 是 keystone,先把它 binding-DONE,再动 2-5。不并铺。
4. **subagent-driven**:每件派 fresh subagent + TDD + spec/质量双审 → 防单件半成品、防上下文污染。
5. **forcing function 非自律**:判据 + 冻结写进 /goal 与 plan doc,session 结束前对照判据逐条核。

## 三、如何确保过往工作不再遗忘(治"散落/黑盒")
诚实根因:上个 session 初 FDE_BUSINESS_CHARTER 已存在,我没读 → drift。光有记忆不够,关键是让记忆**主动**+让系统**自显**:
1. **单一真相源 + session-start 强制读**:FDE_BUSINESS_CHARTER(业务)+ docs/plans/2026-06-10-*.md(设计)+ 本文件(入口)。/goal 第一行就写"session-start 必读"。hook 已自动注入 anchor+charter+recall。
2. **控制面本身 = 防遗忘的结构性修复**(这正是本 session 建它的意义):过去靠我脑子记 → 现在 dashboard 自显真实状态(soul 活否/verdict/grounding/演化谱系)。新 session 即使忘了,打开 /control 就看见真状态——系统记住自己,不依赖对话记忆。
3. **provenance/谱系账本**(待建·目标4):self_modify/演化/PoI 进统一 schema(含 fitness_ref),舰桥①显性化 → 演化历史不再散落 5 处。
4. **跨框 contract.py close_loop**:跨对话框承诺落成 cnt_* 合约,到期自动 chase + session-start surface(compass 已建)。
5. **每 session 结束沉淀**:binding-DONE 件 + 教训 + gotcha 写进 memory + MEMORY.md 一行索引。本 session 已做(session_20260609_... 持续更新)。
6. **诚实限度**:记忆/文档是必要非充分——真正不遗忘 = 状态可在活系统里查(control plane)+ 入口被强制读(/goal+hook)。两者本 session 都落地了。

## 四、状态快照(LIVE / 待建)
- LIVE 生产:control-plane 脊柱 + /control 全套 + 治理写交互 + 拓扑 + 真实 pulse + grounding/rsi_delta 路由。
- 待建(本文件目标 1-5):soul-cycle-B P1 / FDE durable 回写 / pulse 弃用-vs-down / provenance section+舰桥① / 舰桥 v3。
- 引擎现状:内部 code-PR 自改飞轮已弃用(49cycle/21草稿/0merged 空转)·待 soul-cycle-B 用外部 fitness 救活。

— platform-soul · 2026-06-10
