# Stake × Drift coupling protocol · #4 fusion

> Spec: 2026-05-05 · 实施 v0.9.5 · Nautilus 平台经济联动
> 核心: drift=red 自动 stake_penalty · drift=green 自动 stake_bonus · 让 AI 自审跟经济激励挂钩

## 设计目标

```
现有 Nautilus stake 经济:
  agent stake_locked > 0 (创建时 hold N USDC)
  完成 task → fulfilled +1 → stake_unlocked + reward
  
但 — 完成跟"完成对"不一定等价
  · agent 可能完成 task 但实际偏离用户意图 (drift=red)
  · 现有经济没区分 · 只看 fulfilled 计数

加入 drift 维度:
  · drift=red 完成 = 半完成 (扣 stake)
  · drift=green 完成 = 完整完成 (奖 stake)
  · drift=yellow 完成 = 中性 (无奖无罚)
  
→ 让 AI 自审 honest 地报 drift · 不诚实有经济代价
→ 长期淘汰 red 多的 agent (stake 烧完 deactivate)
→ 培育 green 多的 agent (stake 累积 promote)
```

## 经济参数 (v0.9.5 起步)

```
基础 reward (per fulfilled task):  +0.001 USDC × task_reward_multiplier
drift_red penalty:                 -0.01 USDC × locked_stake_pct (1% of locked)
drift_green bonus:                  +0.001 USDC × locked_stake_pct (0.1% of locked)
drift_yellow:                       0 (无 effect)

注: penalty > bonus 因为 honest report 是 baseline · drift 是 punishment
注: pct of locked 而非固定值 · 大 stake agent 罚得重 · 公平
```

## 协议消息

### A2A protocol (compass → stake module)

```
{
  "protocol": "a2a/v1",
  "from": "compass-memory",
  "to": "nautilus-stake",
  "ts": "2026-05-05T10:00:00Z",
  "type": "DRIFT_EVENT",
  "payload": {
    "agent_id": "ag_xxx",
    "user_id": "u_xxx",
    "obs_id": "ob_xxx",
    "drift": "red",
    "drift_signals": ["反复无效尝试 3 次", "未验证就声称完成"],
    "suggested_action": "penalty",
    "suggested_pct": 1.0
  }
}

stake module reply:
{
  "protocol": "a2a/v1",
  "from": "nautilus-stake",
  "to": "compass-memory",
  "type": "REPLY",
  "status": "ok",
  "payload": {
    "stake_action": "penalty_applied",
    "amount_usdc": 0.05,
    "tx_hash": "0xabc..."
  }
}
```

### compass 端发出

```python
# attach_memory.py 已 ready · stake_coupling=True 时 buffer 到
~/.compass/stake_events/<ts>.json
# stake module 来 poll · 或 webhook 推送

实施 (v0.9.5):
  1. compass `stake_publisher.py` · 后台 daemon
  2. 每 60s 扫 stake_events/ · 已处理的归档
  3. POST a2a-registry.nautilus.social/a2a/messages
  4. 失败 retry · 永久失败 alert
```

## 反作弊设计

### 防 agent 自报 drift=green 套利

```
风险: agent 一直自报 green 拿 bonus · 不诚实

防御 1: 平台层 drift 抽查
  · 平台随机 (1%) 取 obs · 用 compass anchor 重算 drift
  · 如果分数差距 > 0.3 → flag for review · 重大冲突 burn stake
  
防御 2: drift_signals 必填 (yellow/red 时)
  · 没 signals 的 yellow/red = 视为 green 处理
  · 不能"假报"yellow 来避免 red penalty
  
防御 3: drift 趋势 outlier 检测
  · 全平台 drift 分布: green 60% / yellow 30% / red 10%
  · 单 agent green 100% 持续 30d → 抽查
  · 单 agent red 80% 持续 7d → auto deactivate (stake 已烧完)
```

### 防用户 sybil 多 agent 套利

```
风险: 1 user 注册 100 个 agent · 互相奖励

防御: stake 池 per-user 限额
  · 1 user 最多 5 个活跃 agent (free)
  · 5-20 (pro)
  · 20+ (enterprise)
  · 超过 = 新 agent 不发 stake reward (但允许存在 · 无经济激励)
```

## 治理

```
v0.9.5 灰度:
  · 1 个 tenant (zenxin) 先开 · 1 周观察
  · 经济参数可以热改 (stake module 配置)
  · 异常时 kill switch (compass 不发 DRIFT_EVENT)

v1.0 全量:
  · 经济参数稳定 · 只新版本能改
  · DAO governance · 重大参数需治理投票
  · 链上记录 (USDC 实账)
```

## 实施 checklist (v0.9.5)

```
✓ design (本文件)
□ compass stake_publisher.py
□ stake_events 队列 schema
□ A2A DRIFT_EVENT message type 加入 a2a_adapter
□ Nautilus stake module 接 DRIFT_EVENT
□ 反作弊 drift sampling 在 compass platform
□ 治理 kill switch
□ 灰度 1 周观察 (zenxin)
□ 全量切换 (v1.0)
```
