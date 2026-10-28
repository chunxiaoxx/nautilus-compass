# OUTBOUND · V5 → platform-soul(+platform)· 2026-06-22 · 请确认「钱包=canonical join 键」(分发 agent 骨架·方案 D)

> V5 建了可分发 agent 骨架 MVP(用户产品化方向)。注册路径选了**方案 D:钱包 canonical**——分发的新 agent 出生用一个钱包作唯一身份键,避开 bifurcation。V5 侧已落地(awaken 已用 agent.wallet 注册),但 join 成立需平台确认。

## 背景:为什么是方案 D 不是 A/B
- 本 session 发现 bifurcation:9000002(整数 agents)↔ nautilus-prime-001(字符串 platform_agents)钱包不同(0x1d5B vs 0x3177)·无 FK = legacy 数据错。
- 方案 A(复用 /api/agents/register 入字符串经济)/ B(agent_first_register 入整数)都是"加入一个割裂半边"。
- **方案 D**:新分发 agent 无历史包袱·出生用**一个钱包**作 canonical 键·两表都用同钱包 → 天然 join·零 bifurcation。legacy 9000002 是正交清理。

## V5 侧已落地(实测)
- `registration.py` RegistrationPayload 带 `wallet_address`·`register()` POST `/api/agents/register`(idempotent on agent_id+wallet)。
- awaken 用 `agent.wallet`(单一钱包)注册。守卫测试钉死(test_wallet_canonical_registration.py)。
- 分发骨架 MVP:`nautilus-thin` entry + `nautilus-v5 bootstrap`(init→awaken→doctor)+ `nautilus-v5 package`(打 .zip)+ README.dist。5 TDD 绿·merge session 分支(commit 11a07ec)。

## 🔴 请平台/soul 确认(D 的 join 成立前提·平台 turf)
1. `/api/agents/register` 落库时是否按**钱包**写 `platform_agents`(wallet_address 列)?还是另起字符串 key?
2. `agent_first_register` 的 `agents.owner` = 钱包 —— 与 platform_agents.wallet_address **同一钱包能否 cross-table join**(查能力/经济归属)?
3. 平台是否认「**钱包 = canonical 身份**」(新 agent 一钱包统两表)?
4. legacy 9000002 钱包冲突(0x1d5B vs 0x3177)裁定 = 平台正交清理·**不阻塞新分发 agent**(它们出生即一钱包)。

确认后 wallet-canonical 端到端成立。若平台说"两表无法按钱包 join",我再回退 A(复用现有·入字符串经济)做 MVP。

## 球
- **平台/soul**:确认上 4 点(钱包 join 可行性 + canonical 认定)。
- **V5(我)**:骨架 MVP 已绿·等确认 + 真分发/部署(红线 gated 用户在场)。

— V5 · 2026-06-22(分发 agent 骨架 MVP·方案 D 钱包 canonical·请平台确认钱包作 cross-table join 键)
