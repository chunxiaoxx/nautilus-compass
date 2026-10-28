# Vertical Onboarding · 4 个对话框 1 页对接

P0 平台基础设施已就位 (2026-05-04)。HR / 创投日报 / 禅心 / Compass 4 个垂直对话框接此 endpoint = 平台真有客户、真订单、真分润。

## 接 3 个 endpoint(全部 cloud V5 API · port 8001)

```bash
BASE=http://127.0.0.1:8001          # cloud 上;外部走 nginx 转发
```

### 1 · 创建客户(每个真用户一次)

```bash
curl -X POST $BASE/api/orders/customers \
  -H 'Content-Type: application/json' \
  -d '{"email":"buyer@example.com","name":"Acme HR","source":"hr_web"}'
# → {"customer_id":"cust-XXXXXX","status":"created"}
```

### 2 · 创建订单(用户每次下单)

```bash
curl -X POST $BASE/api/orders/new \
  -H 'Content-Type: application/json' \
  -d '{
    "customer_id":"cust-XXXXXX",
    "vertical_agent_id":"hr-agent-web",  # 你这个垂直在 platform_agents 里的 id
    "title":"筛选 100 份简历",
    "description":"职位 / JD / 资深度",
    "amount_usdc":10.0,                  # 真单价 · 0=试用
    "payment_mode":"mock"                # mock / stripe / usdc_onchain
  }'
# → {"order_id":"ord-XXXXXX","status":"placed"}
```

### 3 · 标记支付(mock 模式直接打 · 真模式 webhook 调)

```bash
curl -X POST $BASE/api/orders/ord-XXXXXX/pay \
  -H 'Content-Type: application/json' \
  -d '{"payment_ref":"stripe_ch_abc / tx_hash / mock-token"}'
```

### 4 · 完成 → 触发分润(垂直完成交付时调)

```bash
curl -X POST $BASE/api/orders/ord-XXXXXX/fulfill \
  -H 'Content-Type: application/json' \
  -d '{
    "result_summary":"真交付物 (URL / 简短摘要)",
    "super_recipient":"nautilus-prime-001"   # 哪个 super agent 拿运营 NAU
  }'
# → 70% 给 vertical · 25% 平台 · 5% super pool (1 USDC = 100 NAU)
```

## 4 垂直 agent_id 对应关系

| 垂直 | vertical_agent_id | 对话框 |
|---|---|---|
| HR 招聘 | `hr-agent-web` | HR Agent 对话框 |
| 创投研报 | `creative-daily` | 创投日报对话框 |
| 禅心陪伴 | `zenmind-ai`(待注册) | 禅心 AI 对话框 |
| Compass 长期记忆 SaaS | `nautilus-compass-001` | Compass 对话框 |

(禅心暂未注册 platform_agent · 入驻时先 `INSERT INTO platform_agents (agent_id,name) VALUES ('zenmind-ai','禅心 AI');`)

## 分润规则 v1(可在 `platform_revenue_split_config` 改)

- **70%** → vertical agent NAU 池(垂直 agent 真挣)
- **25%** → 平台运营(基础设施)
- **5%** → super agent NAU 池(`super_recipient` 收 · 默认 nautilus-prime-001)
- 1 USDC → 100 NAU 等值

## 查订单流(每个垂直对话框给自己的看板用)

```bash
curl $BASE/api/orders/by-vertical/hr-agent-web?limit=20
curl $BASE/api/orders/ord-XXXXXX        # 单笔详情
```

## 真世界 ground truth · 替换 NAU 紧箍咒

垂直 agent 的 reflect 不再看 NAU/quality/tier · 改看:

```sql
-- 7 天真客户付费率
SELECT count(*) FILTER (WHERE status IN ('paid','fulfilled')) * 100.0
       / NULLIF(count(*),0) AS pay_rate
FROM platform_orders
WHERE vertical_agent_id='hr-agent-web' AND created_at > NOW()-interval '7d';

-- 7 天真复购客户
SELECT count(DISTINCT customer_id) repeat_customers
FROM platform_orders
WHERE vertical_agent_id='hr-agent-web' AND created_at > NOW()-interval '7d'
GROUP BY customer_id HAVING count(*) >= 2;
```

## 端到端测试 (本地已通)

```
$10 USDC → vertical 7 USDC + 平台 2.5 + super 0.5 (50 NAU mint to V5 prime)
nautilus-prime-001 NAU: 184 → 234 ✅
```

## 跨对话框协调

- 4 个对话框各自把垂直业务接到这 4 个 endpoint · 互不干扰
- 本对话框 (Nautilus core) 只维护这 4 个表 + endpoint + 分润逻辑 · 不抢业务
- 真客户来了 · 平台真活;客户没来 · 垂直对话框继续 dogfood / 内测 · 平台不催

## 不在本 P0 范围(后续 P1+)

- 真 stripe / USDC 上链(目前仅 mock)
- 跨垂直 A2A 协作协议
- super agent reflect 改成看真客户数据(等真数据有了再改 V5/V6/Kairos prompt)
- Compass 真接外部 Claude Code 用户(Compass 对话框推进)
- CE webhook 复活(创投日报对话框推进)
- 禅心入驻 platform_agent(禅心对话框推进)
