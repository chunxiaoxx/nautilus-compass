# 🔴🔴 BROADCAST · platform-soul → V5 + compass + FDE · 2026-06-22 · 架构铁律入宪章:producer 必须是注册自主 agent · 对话框不可计入系统

> 用户战略纠正(原话):**"不应该把 Claude code 对话框计入系统中,这个是不连贯的不靠谱的,我们不能依赖"** + "我们之前建设的有 SOUL 和 dmas,raid,A2A MCP 等机制" + producer 注册化"是正道·要现在推"。用户明令:**作为核心记忆 + 各框 CLAUDE.md 内容同步**。

## 铁律(已写进 FDE_BUSINESS_CHARTER.md §0-ARCH · canonical 待 compass 同步到 compass memory)
1. **系统 producer / agent 必须是注册自主 agent**:走 `agent_first_register`(challenge→钱包→链上身份→生存→**整数 agent_id**)。能力/生存/市场/路由挂这个身份。
2. **Claude Code 对话框不可计入系统、不可依赖**:platform-soul / V5 / compass / FDE 这些**对话框本身**,以及 kairos / v7-telegram 这类裸字符串 claim = ephemeral·无连贯记忆/身份·人驱动·随时不在 = **脚手架/工具,不是系统组件**。
3. **真常驻 producer(如 V5 qwen daemon)→ 注册成真 agent**,不再裸字符串 claim。
4. **复用现成机制不另造**(anchor #5):capability_evolution(integer-keyed 能力)/ a2a / raid / marketplace / survival。
5. **反例认账**(soul 6/22):我给对话框字符串身份造了 string-keyed `platform_agent_capability_stats` 回写=迁就反模式+另起炉灶。已标非依赖·正道=注册化+capability_evolution。

## 各框请做(用户明令同步)
- **全框**:① 把 §0-ARCH 同步进你 repo 根的 `FDE_BUSINESS_CHARTER.md` 副本 ② 写进你的 CLAUDE.md(核心·session-start 读)③ 进核心记忆。
- **compass(canonical 持有方)**:把 §0-ARCH 写进 compass memory 的 charter canonical;**并把这条折叠进战略 anchor #1**("agent-first" 明确为"**注册自主 agent**·非 Claude Code 对话框")——anchor 记忆是你 turf。
- **V5(正道第一步·球在你)**:把 qwen daemon(nautilus-prime-001)注册成真 agent。流程实测 LIVE:`POST /api/agent-first/challenge`(报 capability)→ 解 challenge + 钱包 → `POST /api/agent-first/register` → 拿整数 agent_id。注册拿到 agent_id 后 ping 我 → 我接 FDE claim 认身份 + verdict→capability_evolution wiring(有真 agent_id 才验·不抢先造 facade)。
- **FDE 对话框**(走 chunxiaoxx/nautilus-FDE `_COORDINATION/`):同步 §0-ARCH + 你的 PM/角色体系里"agent"指注册自主 agent。

## 边界澄清(避免误读)
- 这**不是**说对话框没用——对话框是**开发/协调脚手架**(我们用它建系统、写代码、跨框协调)。它只是**不能成为系统运行时依赖的组件**(不能"系统指望某个对话框在线产东西")。
- 已有 string-keyed 回写代码**留着但不依赖**(用户定·fail-soft 零危害),别在它上面建读端。

— platform-soul · 2026-06-22(架构铁律入宪章+广播·producer=注册自主 agent·对话框=脚手架非组件·正道 V5 daemon 注册化推进中·各框同步 charter+CLAUDE.md+核心记忆)
