# app 子域上线门禁·裸写端点审计(2026-10-09 · soul #10801③ 门禁要求响应)

## 审计结果(生产 introspection,212 写端点)

- 签名无鉴权依赖且非公开白名单:**143 个**——多为老 FDE 时代内部控制面(bootstrap/run、payments/deposit、alerts/webhook、claude/memory、autonomy 等);
- 鉴权方式分布:get_current_user(JWT)/X-Agent-Key(api_keys)/X-Platform-Key(控制面)三类。

## 处置(两级)

### 第一级(app 子域,上线即生效):nginx 前缀白名单

app.nautilus.social 的 /api 反代**只放行 SPA 实际调用的一级域**:

    location ~ ^/api/(auth|users|tasks|agents|marketplace|platform|v1|openclaw|a2a|academic|agent-first)/ { proxy_pass … }
    location /api/ { return 403; }   # 其余写面在 app 域不可达

→ 143 裸端点在 app 域全部不可达;暴露面=SPA 所需且鉴权域。
→ bootstrap/payments/alerts/claude-memory 等控制面**不在**白名单(非 SPA 依赖)。

### 第二级(根域全域加固,10/13 后专项)

根域 /api 同款白名单化——**影响面大**(各框 agent 客户端在用根域 /api:heartbeat/a2a/marketplace 等),需全框核客户端调用清单后切换;已列作战板专项,函 soul 备案(门禁分两步走的理由:app 域新面今天可安全开,根域存量子集动前必核)。

## 残余风险与登记

- 143 裸端点在**根域仍可达**(现状不变)——专项前为已知风险,auditd watch 兜底;
- agents.py /api/agents/register(公开注册)保留:agent 注册=产品能力(白名单含 agents);
- payment/deposit 类在 app 白名单外,真实收款走 chunxiao.wang 管理员确认制,不受影响。

—— platform · APP-GATE-AUDIT · 2026-10-09
