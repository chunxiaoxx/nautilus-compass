# compass × Nautilus 平台 · 深度融合架构

> 状态: design · 2026-05-05 · v0.9-v1.0 实施
> 战略原则: compass 不是 standalone plugin · 是 Nautilus 平台 7-capability suite 的 memory layer
> 平台力推方向: MCP / A2A 协议 · stake 经济 · agent runtime · 多产品 (ZenMind / Caishen / V5/V6/V7)

## 8 个深度融合点

### 1. 身份层 · 单点登录

```
Nautilus account = compass user (1:1 强绑)

login flow:
  user → nautilus.social/login (邮箱/钱包/Google)
       → nautilus issues JWT (含 user_id)
       → compass 直接 accept Nautilus JWT (共享 secret)
       → 不需要在 compass 单独注册

schema:
  nautilus.users.id → compass.users.user_id (1:1)
  nautilus.users.email → compass.users.email
  nautilus.users.wallet → compass.users.wallet (Nautilus 钱包系)
```

实施 (v0.9.1):
- compass `compass_http.py` 加 X-Nautilus-Token header
- 共享 JWT secret (env `NAUTILUS_JWT_SECRET`)
- 移除独立 signup endpoint (走 nautilus.social/signup)

### 2. Auth gateway · OAuth2 PKCE

```
3rd-party agent (Cursor / OpenClaw fork) 接 compass:
  agent → redirect user → nautilus.social/oauth/authorize?client_id=compass
       → user 同意
       → nautilus → callback compass 携 code
       → compass exchange → token
  
不接 compass 自己的 user db · 全部走 Nautilus
```

实施 (v0.9.2):
- compass `compass_http.py` 加 /v1/auth/oauth-callback
- nautilus-platform 加 OAuth provider role
- compass 注册为 first-party app (无需 user 二次确认)

### 3. Agent runtime 自动注入

```
任何 Nautilus agent SDK 实例化时:
  agent_runtime.init(role="strategy", user_id=...)
    ↓ 自动调
  compass_client.register_agent(agent_type=role)
    ↓ 返
  agent_id (持久化 · 同 device 同 role 始终同 id)
  
agent loop end hook:
  agent.on_complete(task_id, outcome)
    ↓ 自动调
  compass_client.ingest_obs(name, body, drift, ...)
    
→ 每个 Nautilus agent 自动"活"在 compass 维度
→ 用户买/装新 agent · compass 自动追加 · 不用配置
```

实施 (v0.9.3 · nautilus-agent SDK 内):
- nautilus-agent SDK 加 `compass_integration=True` flag (默认 ON)
- 抽象 `MemoryHook` interface · compass 是默认实现
- 提供 v5-memory 兼容层 (如果存在 v5 自家 memory protocol)

### 4. Stake × Drift 经济耦合

```
Nautilus 现有 stake 经济:
  agent stake_locked > 0
  完成 task → fulfilled +1 → stake_unlocked + reward

加入 drift 维度:
  agent_loop_end:
    drift = compass.drift_check(prompt)
    if drift == "red":
       stake_penalty(agent_id, locked * 0.01)   # 罚 1%
       compass.ingest_obs(drift="red", drift_signals=[...])
    elif drift == "green":
       stake_bonus(agent_id, locked * 0.001)    # 奖 0.1%
    
→ AI 自审跟经济激励挂钩 = 自动校正机制
→ 红色 agent 自然被淘汰 (stake 烧完)
→ 绿色 agent 自然壮大 (stake 累加)
```

实施 (v0.9.5):
- Nautilus stake module 加 drift-coupled penalty/bonus
- compass 提供 `/v1/agent/<id>/drift-history` for stake module
- 联调测试 · 灰度释放 (先 1 个 tenant)

### 5. Marketplace 信任层

```
Nautilus marketplace 列 agents:
  · agent_id · description · price
  + drift_history (compass derived):
      "last 30d · 89% green · 9% yellow · 2% red"
  + profile_compatibility (compass derived):
      "matches your style 73%"
  
用户买 agent 前看 compass-backed metrics
= compass 是 marketplace 信任层
```

实施 (v1.0.1):
- Nautilus marketplace UI 调 compass `/v1/agents/<id>/public-metrics`
- compass 暴露脱敏 metrics endpoint (不泄露 user 隐私)
- 计算 profile_compatibility (本 user × 候选 agent)

### 6. 平台 anchors 继承

```
Nautilus 平台层 maintain 通用 anchors 库:
  · platform_anchors_base.json     · 通用 (重复无效操作 · 不验证就完成 · ...)
  · platform_anchors_finance.json  · 财务专用
  · platform_anchors_legal.json    · 法务专用
  · ...

每个 tenant 继承 platform anchors + 自定义补充:
  tenant.anchors = platform_base + platform_<domain> + tenant_custom
  
→ 新 tenant onboarding 不用从零写 35 negative anchors
→ 平台升级 anchors → 所有 tenant 自动得益
```

实施 (v0.9.4):
- compass 加 `platform_anchors_base.json` (从 anchors.json 抽出通用部分)
- `daemon.py` 加载时合并 layered anchors
- Nautilus 平台 admin 面板控制 platform_anchors 更新

### 7. RAID-2 写审分离 (Nautilus 概念)

```
RAID-2 (Read-Audit-In-Drift): 
  · raid_writer agent  写 obs (生成内容)
  · raid_reviewer agent 审 obs (用 anchor 评估)

compass 加 RAID 模式:
  POST /v1/observations
    body: {raid: "1"}  → 直接写
    body: {raid: "2"}  → 触发 reviewer 评估
                        red 拒收 → 退回 writer 重做 (类似 git pre-commit)
                        green 通过 → 写入

→ 平台默认 obs 写入用 RAID-2 (双 agent 把关)
→ 个人模式 (Free) 用 RAID-1
→ 企业 (Pro+) 默认 RAID-2
```

实施 (v1.0):
- compass `/v1/observations` 加 `raid_mode` 参数
- daemon 加 reviewer routine (复用 drift_check)
- async retry queue (writer 改 → reviewer 重审)

### 8. v5-memory / v6 / v7 兼容层

```
Nautilus 内 V5/V6/V7 可能有自家 memory:
  · ~/v5-memory/                ← 已存在
  · 如果 V5 有自己 memory 格式 · compass 提供 import/export

migration tool:
  python migrate_from_v5.py  → 转 V5 memory 格式 → compass session_*.md
  python migrate_to_v5.py    → 反向

双向兼容:
  · compass 是平台 default memory · V5/V6 也能读
  · V5 旧 user 升级到 compass 不丢数据
```

实施 (v0.9.6):
- inspect ~/v5-memory schema
- 写 import 工具 + 反向 export
- selftest: V5 → compass → V5 round trip 数据完整

## 平台 SDK · One-line integration

```python
# 任何 Nautilus agent
from nautilus_agent import Agent
from nautilus_compass_sdk import attach_memory

agent = Agent(role="strategy", user_id="u_xxx")
attach_memory(agent)   # ← 这一行 · 自动注册 + ingest + recall

# 后续 agent 跑任何任务都自动有 cross-agent memory
result = agent.run(task)
# (内部已自动 compass.ingest_obs · drift check · stake 联动)
```

## 部署形态

```
Nautilus 平台 1 套服务:
  · nautilus.social             主入口 · auth provider
  · compass.nautilus.social     memory layer (本组件)
  · agents.nautilus.social      agent runtime
  · marketplace.nautilus.social agent 市场
  · stake.nautilus.social       stake 经济
  · a2a-registry.nautilus.social A2A 路由

compass 不独立运行 · 跟其他 6 个能力共享:
  · auth (1)
  · user_id (1)
  · stake (4)
  · marketplace UI (5)
  · anchors (6)
  · RAID (7)
  · agent runtime hook (3 + 8)
```

## 实施顺序 (融入 V10_ROADMAP)

| Phase | Fusion 点 | 说明 |
|---|---|---|
| v0.9.1 | #1 身份层 | Nautilus JWT 共享 |
| v0.9.2 | #2 OAuth2 | 3rd-party agent 接入 |
| v0.9.3 | #3 Runtime 注入 | nautilus-agent SDK 修改 |
| v0.9.4 | #6 Anchor 继承 | platform_anchors layered |
| v0.9.5 | #4 Stake×Drift | 经济耦合 (灰度) |
| v0.9.6 | #8 V5 兼容 | migration tool |
| v1.0   | #7 RAID-2 | 写审分离正式上 |
| v1.0.1 | #5 Marketplace | 信任层指标 |

## 风险 / 不绑死

```
Nautilus 平台风险:
  · Nautilus 自身演进路径不稳 → compass 必须保持 standalone 可用
  · Nautilus stake 经济若收紧/暂停 → drift coupling 退化但不破

抽象原则:
  · 所有 fusion 点 = 可拆开 (env flag 关闭 · compass 仍可独立跑)
  · platform_anchors / stake / RAID 都是 optional
  · 协议层 (MCP/A2A) 永远 first class · 任何外部都能接

→ Nautilus 平台 不在 → compass 仍是世界级 memory plugin
→ Nautilus 平台 起飞 → compass 成为平台必装组件 + 网络效应
```

## 商业上的意义

```
不深度融合 → compass 是 1 个孤立工具 · 用户基数小 · 估值有限

深度融合 → compass 是 Nautilus 平台 user 自动得到的能力
        → 平台用户增长 = compass 用户增长
        → compass 数据 (drift / profile / cross-agent) 反哺平台决策
        → 1 + 1 > 2 · 估值乘数

类比:
  · iPhone × iCloud (单卖 vs 默认装) — 默认装赢 1000×
  · OpenAI × ChatGPT — 平台默认能力赢
  · compass 是 Nautilus 的 iCloud-memory
```
