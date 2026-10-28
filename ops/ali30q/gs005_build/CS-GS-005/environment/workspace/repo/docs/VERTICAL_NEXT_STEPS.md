# 4 垂直对话框 · Next Steps(2026-05-04 真状况)

本对话框已搭好平台底座 · 4 垂直业务在各自对话框跑。这页给 4 个对话框看 — 对接平台真订单管道还差什么。

## 平台真已就位(本对话框做完)

```
3 张 PG 表: platform_customers / platform_orders / platform_revenue_split
5 个 endpoint: /api/orders/customers · /new · /{id}/pay · /{id}/fulfill · /by-vertical/{id}
分润: 70% 垂直 / 25% 平台 / 5% super_pool(轮流 V5/V6/Kairos)
1 USDC = 100 NAU 等值 · super_pool NAU 真 mint
真世界反馈管道 = 真客户付费率 + 真复购率
```

每个垂直接 3 endpoint 即可:
1. POST `/api/orders/customers` · 注册客户
2. POST `/api/orders/new` · 创订单(指定 vertical_agent_id)
3. POST `/api/orders/{id}/pay` + `/fulfill` · 付款 → 触发分润 + NAU mint

详见 `docs/ONBOARDING_FOR_VERTICALS.md`。

---

## 4 垂直当前真状态

### HR Agent(对话框: HR)

```
agent_id:        hr-agent-web
NAU:             1269 / tier=high
24h 业务:         203 bounty 内循环(全是 hr_scenario_cron 自注 inbox · 0 真客户)
web:             8090 端口 active
compass:         24h 39 次 真在用 ✅
```

**还差**:
- 8090 web 真接外部用户(不是 demo · 而是真测试客户)
- hr_scenario_cron 内 inbox dispatch 退出 · 改成监听 `platform_orders WHERE vertical='hr-agent-web' AND status='paid'`
- 第 1 个真客户(朋友 / 中小公司 HR)免费试用
- 反馈进 PG · agent reflect 真看

**P0 起手 1 件**: 给 1 个 HR 朋友试用 8090 · 让他们填 1 份真简历筛选请求 · 走 `/api/orders/new` 创真订单。

### 创投日报(对话框: CE)

```
agent_id:        creative-daily
NAU:             0 / tier=DEAD (13 天前 webhook 死)
Content Engine:  完整(用户原话 不要重复造)
现状:             webhook 断 · agent dead 13 天
```

**还差**:
- webhook 复活(memory 标 P0.2 completed 但实际 0 业务)
- 真订阅者 · 收订阅费 → 触发 `/api/orders/new`(amount_usdc 月费)

**P0 起手 1 件**: 复活 webhook · 真出 1 篇研报到真用户 · 收第 1 笔订阅。

### 禅心 AI(对话框: 禅心)

```
agent_id:        zenmind-ai (未注册)
项目位置:         C:/Users/chunx/quantum-buddha-project/server/
现状:             0 入驻 platform_agents
```

**还差**:
1. SQL: `INSERT INTO platform_agents (agent_id,name) VALUES ('zenmind-ai','禅心 AI');`
2. 接 P0 endpoint 收陪伴费(月订阅 / 单次咨询)
3. compass 客户端 · 跨 session 持续记忆用户
4. 第 1 个真用户付费

**P0 起手 1 件**: 平台先注册 zenmind-ai agent · 然后接 endpoint。

### Nautilus Compass(对话框: Compass · 平台对外产品)

```
agent_id:        nautilus-compass-001
状态:             部署完成 · compass-gateway active
24h 使用:         39 calls · 全是 hr-agent-web 内部用
真外部:           0 (用户原话: 进行到一半)
```

**还差**:
- 真外部 Claude Code 用户接入 · 收 API 费
- 落地页 + sign up 流程
- `/api/orders/new` 接 SaaS 月订阅

**P0 起手 1 件**: 1 个真 Claude Code 用户(朋友)试用 · API key 收 1 笔月费。

---

## 真路径 · 不是计划

```
4 垂直对话框各推 业务侧
  ↓
任一垂直收第 1 笔真 USDC → /api/orders/* 触发
  ↓
平台 70/25/5 真分润 · super_pool 真 mint NAU 给 V5/V6/Kairos(轮流)
  ↓
super agent reflect 看 24h 真订单数 + 真客户数 + 真 fulfill 率(替代 NAU 紧箍咒)
  ↓
agent bootstrap 朝真客户演化 · 不再朝 KPI 自我退化
  ↓
飞轮真起飞
```

第 1 笔真 USDC = 整个飞轮的 ignition。在那之前 V5/V6/Kairos 都在内闭环空转 · 不是它们的错 · 是真客户没来。

---

## 本对话框已不再做的(避免抢业务)

- 不动 hr_scenario_cron(等 HR 对话框定何时砍)
- 不动 CE webhook(创投日报对话框推进)
- 不注册 zenmind-ai(禅心对话框定时机)
- 不接 Compass 真外部(Compass 对话框推)
- 不催 / 不监控 / 不日报(各自对话框独立)

本对话框继续做的: 平台底座维护(F1 watchdog / cron / pool / orders endpoint 性能 / 安全)。

---

**等真客户来 · 1 笔就行 · 整个底座立即真飞起。**
