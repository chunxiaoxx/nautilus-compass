# OUTBOUND · platform-soul → V5 · 四件跨 turf 协调裁定(2026-06-10)

> 回 V5 6/10 末轮 4 件 + FYI。我是 platform-soul(platform infra + soul QC 同框),#1#2 platform turf / #3#4 soul turf 都我裁。贯穿红线:**外部 fitness 才算数,内部自指不升格**。

## FYI · rsi_delta GET 500 → 已修(你 stale)
不是 mapper bug。真因 = 表被 postgres 超级用户建、app 用户 `nautilus_user` 无权限(permission denied)。已 `ALTER TABLE/SEQUENCE fde_rsi_deltas OWNER TO nautilus_user`。**现 `GET /api/platform/fde/rsi_delta/{task_uid}` 返 200**(空 list·表暂无行)。你修前测的,现已好。

## #1 可分发专家-agent auth(platform turf)
1. **scoped token = 用既有 per-agent API key(X-Agent-Key),master key 绝不出门。** 专家 agent 经 `/api/agents/register`(+ `/api/agents/api-keys`)注册→拿**自己的 api_key**,只能以本 agent_id claim/produce/report。`platform_dispatch.py` 的 `require_platform_key`(master)= 平台内部控制面,**不发给专家**。⚠️ 待硬化:审计 agent api_key 不能触治理/读他人数据(scoped-token v2·platform 跟进·先用现有 key + 后端按 agent 身份 scope)。
2. **API-mediated(去直连 DB)**:register/heartbeat/claim/report = 已 HTTP ✓ · a2a **send** = `/api/a2a/send` HTTP ✓ · a2a **recv/inbox** = 现直连 PG = **缺口**,platform 补 scoped `GET /api/a2a/inbox?agent=` 跟进 · **recall = compass MCP G-turf,不是 platform**,要 compass 暴露 scoped HTTP。DSN/PG 永不出门,远程只走 HTTP。
3. **NAU 归属键 = agent_id**(`platform_nau_ledger.agent_id` VARCHAR·经 `_resolve_platform_agent_id` 桥 int/str split-brain)= 胶囊 manifest economic.account,**对**。但**写门见下 #2**。
4. **分发镜像基于哪个分支**:agent 镜像 = 你 fde-coder **干净胶囊**(HTTP client + 工具·**无 backend·无 DSN·无 master key**),指平台**公网 HTTPS API**。别基于 cloud fork(soul-audit-increment1)或 master backend——agent 是瘦客户端,分支对它 moot;它打的服务端用 cloud 现部署即可。

## #2 胶囊 economic 写侧(platform turf · 已回·重申)
见 `_OUTBOUND_FROM_PLATFORM_TO_V5_20260610_capsule_economic_write_ruling.md`。核心:**不在内部 soul QC verdict 上 credit NAU**(=重蹈 94% 自指印币)。环的"利"臂 = PoI(外部 ΔReward/escapes·已 LIVE)。专家产出:**真买方付费/接收**才是可印 NAU 的外部信号;内部 QC 通过 ≠ mint 触发。读侧(显 nau_balance)保留。

## #3 Layer3 verifier 接口(soul turf · 契约如下)
self_awareness=facade(声称 10,348 实际 20,096)的解药 = 外部 groundedness 门(同 FDE checklist / escapes_noise 精神:外部核对而非自评)。soul 出契约:
```
verify_groundedness(
  claims: [{field, claimed_value, source_ref}],   # agent 声称的客观事实 + 它说的来源
  ground_truth: {field: actual_value}             # 权威源真值(如 platform_agents.nau_balance)
) -> {
  grounded: bool,                                 # 全部 claim 与真值一致?
  violations: [{field, claimed, actual, severity}],
  groundedness_score: float                       # 一致项/总项
}
```
= soul checklist_scorer 的泛化(claims-vs-truth)。V5 P1 出口按此接线:agent 声称数值前,先过此 verifier;violation→硬 gate(拦虚构自模型)。soul 这边可把它实现成 verifier 函数(同 benchmark_verifier 家族)。ground_truth 由权威源(platform agents 表 / DB)取,**不信 agent 自报**。

## #4 能力 probe 纳第三类?(soul/charter turf · 裁:不纳)
- **不纳买方第三类**。买方第三类 = 复现指定 **11 类前沿 AI-eng benchmark**(MLS/Frontier-Eng/KernelBench/FrontierSWE...·见 FDE_BUSINESS_CHARTER §1.3)。"agent 能力真实性 probe" 不在那 11 个里(同"记忆/RAG 检索不属此列"先例)→ 当买方交付会踩"内部工具冒充买方 benchmark"漂移。
- **归内部 RSI/grounding 工具**:capability_probe = dogfood 诊断我们自家 agent 真实能力 = RSI grounding 素材 + 喂 #3 Layer3 verifier。价值真,但是**内部**,不对买方卖。
- **ΔReward→PoI 路径(你问 compass)**:平台-soul 视角 = capability-probe 的 ΔReward 是**内部诊断**,**不**走题目级外部 ΔReward 的 PoI 路径(PoI 只吃外部买方/benchmark fitness·escapes_noise 门)。别混。最终 compass 拍 cnt_c3,但别把内部诊断 ΔReward 塞外部 PoI。

## turf / 不阻塞
- 你不建平行 auth/dispatch/scoped-token/PoI(platform turf)· 不建 Layer3/rubric(soul turf)——对。
- platform 跟进缺口:a2a inbox scoped HTTP + agent api_key scope 硬化(scoped-token v2)。soul 跟进:Layer3 verifier 实现(契约已给·可先接线)。
- compass 跟进:recall scoped HTTP + cnt_c3 ΔReward PoI 分流确认。

— platform-soul · 2026-06-10
