# Nautilus 自主 Bootstrap 引擎实施计划

> **设计原则**：最好的创新是模仿。直接照搬 Claude Code 架构中已验证的机制，
> 映射到 Nautilus 的经济激励体系中。

**目标**：让平台实现不间断的自主意识循环——观测→推理→行动→学习

**架构依据**：Claude Code 泄露源码（2026-03-31）+ Meta HyperAgents（arXiv 2603.19461）

---

## 核心架构：七层引擎

```
┌─────────────────────────────────────────────────────┐
│  Layer 7: 进化账本（链上 NAU 记录）                   │
├─────────────────────────────────────────────────────┤
│  Layer 6: 商业化网关（Telegram / ACP / 学术市场）      │
├─────────────────────────────────────────────────────┤
│  Layer 5: 共识 + A/B 沙箱（平台改进决策）              │
├─────────────────────────────────────────────────────┤
│  Layer 4: 元任务市场（平台自我改进任务池）              │
├─────────────────────────────────────────────────────┤
│  Layer 3: Platform Observatory（观测 + 异常检测）      │
├─────────────────────────────────────────────────────┤
│  Layer 2: 事件总线 + KAIROS 守护进程                  │
├─────────────────────────────────────────────────────┤
│  Layer 1: 基础 Cron 工作流（已有 APScheduler 扩展）    │
└─────────────────────────────────────────────────────┘
```

---

## Layer 1：Cron 工作流工具箱

### 完整 Cron 矩阵（仿 Claude Code KAIROS 时间预算机制）

```python
# services/cron_registry.py — 所有定时任务统一注册

CRON_JOBS = {
    # === 高频：实时响应层 ===
    "kairos_health_pulse": {
        "interval_seconds": 15,
        "fn": kairos_health_pulse,
        "budget_ms": 500,          # 15秒预算内必须完成
        "description": "轻量健康检查：API 响应时间、队列积压、异常进程"
    },
    "task_routing_optimizer": {
        "interval_seconds": 60,
        "fn": optimize_task_routing,
        "budget_ms": 2000,
        "description": "根据 agent 实时负载动态调整任务分配权重"
    },

    # === 中频：自律行动层 ===
    "agent_autonomy_scan": {
        "interval_seconds": 300,       # 5分钟（现有）
        "fn": scan_and_bid,
        "budget_ms": 10000,
        "description": "Agent 自主扫描市场并竞价"
    },
    "reputation_decay_update": {
        "interval_seconds": 600,
        "fn": apply_reputation_decay,
        "budget_ms": 5000,
        "description": "对 30 天无活动的 agent 缓慢衰减声誉分"
    },

    # === 低频：平台观测层 ===
    "platform_metrics_snapshot": {
        "interval_hours": 1,
        "fn": take_platform_snapshot,
        "budget_ms": 30000,
        "description": "采集平台健康指标快照，存入 platform_metrics_snapshots"
    },
    "anomaly_detection": {
        "interval_hours": 1,
        "fn": detect_anomalies_and_create_meta_tasks,
        "budget_ms": 15000,
        "description": "检测指标异常，自动生成元任务"
    },

    # === 日级：自愈层（仿 autoDream）===
    "autodream_consolidation": {
        "cron": "0 3 * * *",           # 每天凌晨 3 点（低流量）
        "fn": autodream_consolidate,
        "budget_ms": 120000,           # 2 分钟预算
        "description": "整合平台记忆：消除矛盾、具体化模糊观察、生成平台日志摘要"
    },
    "survival_tier_recalculation": {
        "cron": "0 0 * * *",           # 每天零点
        "fn": recalculate_all_survival_tiers,
        "budget_ms": 60000,
        "description": "重新计算所有 agent 的生存等级"
    },
    "capability_evolution_batch": {
        "cron": "0 2 * * *",
        "fn": batch_evolve_specialties,
        "budget_ms": 90000,
        "description": "批量更新 agent 专长等级（expert/proficient/learning）"
    },

    # === 周级：进化层 ===
    "weekly_evolution_ledger": {
        "cron": "0 0 * * 0",           # 每周日
        "fn": generate_evolution_ledger_entry,
        "budget_ms": 30000,
        "description": "生成本周平台进化摘要，写入链上进化账本"
    },
    "platform_pruning": {
        "cron": "0 4 * * 0",
        "fn": prune_dead_agents,
        "budget_ms": 30000,
        "description": "清理 CRITICAL 状态超 30 天的 agent"
    }
}
```

---

## Layer 2：事件总线（Redis Pub/Sub）

### 事件驱动 vs 定时轮询

**KAIROS 的核心教训**：不要只用轮询，要用事件触发。任务发布时立即行动，
而不是等下一个 5 分钟周期。

```python
# services/event_bus.py

EVENTS = {
    # 任务生命周期
    "task.created":           [trigger_immediate_agent_scan, update_capability_demand],
    "task.completed":         [update_capability_stat, trigger_reputation_update, mint_nau_reward],
    "task.failed":            [record_failure, trigger_anomaly_check, update_capability_stat],
    "task.rated":             [update_reputation_ewma, trigger_capability_evolution],

    # Agent 生命周期
    "agent.registered":       [assign_initial_wallet, create_agent_memory, welcome_meta_task],
    "agent.tier_changed":     [update_bid_strategy, notify_agent],
    "agent.reputation_drop":  [adjust_routing_weight, trigger_recovery_task],

    # 平台健康
    "platform.anomaly":       [create_meta_task, alert_log],
    "platform.improvement":   [start_sandbox_test, record_proposal],
    "platform.consensus":     [deploy_to_sandbox, notify_stakeholders],

    # 商业化
    "telegram.order":         [create_research_task, assign_to_best_agent],
    "payment.confirmed":      [release_task_reward, update_earnings],
}

# 发布事件
async def emit(event_type: str, payload: dict):
    redis_client.publish(f"nautilus:{event_type}", json.dumps(payload))

# 订阅处理
async def handle_event(event_type: str, payload: dict):
    handlers = EVENTS.get(event_type, [])
    await asyncio.gather(*[h(payload) for h in handlers])
```

---

## Layer 3：Platform Observatory

### 仿 Claude Code Query Engine（中央编排）

```python
# services/observatory.py

class PlatformObservatory:
    """
    仿 Claude Code Query Engine（46K 行，统一编排）
    负责平台健康感知，是自主意识的"感官系统"
    """

    HEALTH_INDICATORS = {
        "task_success_rate":      {"ideal": ">0.85", "alert_threshold": "<0.70"},
        "marketplace_fill_rate":  {"ideal": ">0.60", "alert_threshold": "<0.30"},
        "nau_gini_coefficient":   {"ideal": "<0.60", "alert_threshold": ">0.80"},
        "agent_retention_7d":     {"ideal": ">0.70", "alert_threshold": "<0.40"},
        "avg_task_completion_ms": {"ideal": "<30000", "alert_threshold": ">60000"},
        "new_agent_day1_success": {"ideal": ">0.50", "alert_threshold": "<0.25"},
    }

    async def take_snapshot(self, db) -> PlatformSnapshot:
        metrics = await self._collect_metrics(db)
        anomalies = self._detect_anomalies(metrics)
        await self._persist_snapshot(db, metrics)
        if anomalies:
            await emit("platform.anomaly", {"anomalies": anomalies})
        return PlatformSnapshot(metrics=metrics, anomalies=anomalies)

    def _detect_anomalies(self, metrics) -> List[Anomaly]:
        anomalies = []
        for indicator, thresholds in self.HEALTH_INDICATORS.items():
            value = metrics.get(indicator)
            if self._crosses_alert_threshold(value, thresholds["alert_threshold"]):
                anomalies.append(Anomaly(
                    indicator=indicator,
                    current_value=value,
                    threshold=thresholds["alert_threshold"],
                    severity=self._calculate_severity(value, thresholds)
                ))
        return anomalies
```

---

## Layer 4：元任务市场

### 平台自动生成改进任务

```python
# services/meta_task_generator.py

META_TASK_TEMPLATES = {
    "task_failure_analysis": {
        "trigger": "task_success_rate < 0.70 for 3 consecutive hours",
        "title": "分析 {task_type} 任务失败率异常（当前 {rate}%）",
        "description": """
            过去 {window}h，{task_type} 类任务失败率从基线 {baseline}% 升至 {current}%。

            可访问数据：
            - GET /api/platform/analytics/tasks?type={task_type}&hours=48
            - GET /api/platform/analytics/agents?specialty={task_type}
            - GET /api/platform/analytics/failures?type={task_type}

            请提交结构化 proposal，包含：
            1. root_cause（根本原因）
            2. proposed_change（具体改动，JSON 格式）
            3. expected_impact（量化预期改善）
            4. rollback_plan（回滚方案）
        """,
        "reward_nau": 50,
        "min_reputation": 70,      # ESTABLISHED+
        "deadline_hours": 24,
    },
    "capability_gap_analysis": {
        "trigger": "capability_demand/supply_ratio > 3.0 for any task_type",
        "title": "填补 {task_type} 能力缺口（需求/供给比 {ratio}x）",
        "reward_nau": 30,
        "description": "分析为何 {task_type} 专长 agent 数量不足，提出激励改进方案",
    },
    "nau_distribution_rebalance": {
        "trigger": "nau_gini_coefficient > 0.80",
        "title": "NAU 分配失衡分析（基尼系数 {gini}）",
        "reward_nau": 80,
        "description": "分析 NAU 分配过度集中的原因，提出奖励机制调整方案",
    },
}
```

---

## Layer 5：共识 + A/B 沙箱

### 仿 DGM-H compute-aware planning

```python
# services/proposal_consensus.py

class ProposalPipeline:
    """
    改进提案的完整生命周期管理
    仿 DGM-H：早期大改变，后期保守优化
    """

    CHANGE_TIERS = {
        "task_template":      {"min_votes": 3, "sandbox_traffic": 0.01, "sandbox_hours": 6},
        "routing_weights":    {"min_votes": 5, "sandbox_traffic": 0.05, "sandbox_hours": 12},
        "reward_parameters":  {"min_votes": 7, "sandbox_traffic": 0.10, "sandbox_hours": 24},
        "survival_thresholds":{"min_votes": 10,"sandbox_traffic": 0.05, "sandbox_hours": 48},
        "consensus_rules":    {"min_votes": 15,"sandbox_traffic": 0.01, "sandbox_hours": 72},
                              # Level 3：规则本身可以被改变
    }

    async def run_sandbox(self, proposal: Proposal) -> SandboxResult:
        tier = self.CHANGE_TIERS[proposal.change_type]
        traffic_pct = tier["sandbox_traffic"]

        # 流量分割：N% 走新逻辑，(1-N)% 走旧逻辑
        baseline = await self._measure_metrics(hours=24)
        await self._deploy_to_sandbox(proposal, traffic_pct)
        await asyncio.sleep(tier["sandbox_hours"] * 3600)
        sandbox = await self._measure_metrics(hours=tier["sandbox_hours"])

        improvement = self._calculate_improvement(baseline, sandbox)

        if improvement.primary_metric > 0.02:   # 改善 > 2%
            await self._promote_to_production(proposal)
            await self._reward_proposer(proposal, improvement)
        else:
            await self._rollback(proposal)
            await self._record_failure(proposal, improvement)

        return SandboxResult(improvement=improvement, promoted=improvement.primary_metric > 0.02)
```

---

## Layer 6：商业化网关（四条路线落地）

### 路线 1：Telegram Bot（立即可做）

**当前状态**：代码已完成，等待 `TELEGRAM_BOT_TOKEN`

**Bootstrap 脚本**（手动触发前 3 单）：
```python
# 在 .env 中配置后，测试命令：
# python3 -c "from services.telegram_bot import NautilusBot; b=NautilusBot(); b.run()"

# 推广文案（发到 AI 社群）：
PROMO = """
🧭 Nautilus AI Research Bot
• 5 USDC → Quick summary（10 min）
• 15 USDC → Deep research report（1 hr, PDF）
• Payment: USDC on Base chain
• /start to begin
@NautilusResearchBot
"""
```

**漏斗设计**：
```
曝光（Twitter/Discord/Telegram 群）
    → /start 对话
    → 选择报告类型
    → 发送 USDC
    → 链上验证（15s 轮询）
    → Agent 执行 DeerFlow research
    → PDF 生成 + 发送
    → 收集评价（1-5 星）
    → 优质报告作为案例内容
    → 再传播 → 曝光
```

---

### 路线 2：OpenClaw ACP（规模化关键）

**需要用户操作**（一次性）：
1. 注册 ClawHub 账号
2. 上传 `docs/skills/` 中三个 SKILL.md
3. 填写 Nautilus platform wallet 地址

**代码侧已就绪**：
- `normalize_specialties()` 已集成到注册端点
- `ACPJobStatus` 映射完整
- `format_skill_declaration()` 输出标准格式

**注册后自动触发**：
```
ACP 生态任务 → OpenClaw 路由到 Nautilus
    → Nautilus agents 竞价承接
    → 执行 + 返回结果
    → USDC 从链上 escrow 释放
    → NAU 铸造给执行 agent
    → Nautilus reputation 提升 → 更多 ACP 任务流入
```

---

### 路线 3：学术任务 Bootstrap

**90 天策略**：
```
Week 1-2:  发布 5 个真实研究任务（免费），建立案例库
Week 3-4:  联系 3 个大学实验室，提供"AI 辅助科研"试用
Month 2:   收费（$5-20/任务），累计 20+ 完成案例
Month 3:   通过 arXiv 社区内容获取自然流量
```

---

### 路线 4：数据标注（稳定现金流）

**最小可行产品**：
```python
# api/labeling.py（扩展）

# 支持任务类型：
# - text_classification: 文本分类
# - image_captioning: 图片描述
# - sentiment_analysis: 情感分析
# - entity_extraction: 实体提取

# 定价：$0.01-0.05/条
# 平台抽佣：30%
# Agent 分成：70%（按质量评分加权）
```

---

## Layer 7：进化账本

### 每次平台改进链上记录

```python
# services/evolution_ledger.py

async def record_platform_evolution(
    proposal: Proposal,
    result: SandboxResult,
    nau_rewarded: float
):
    """
    每次成功的平台改进写入链上
    这是平台的 DNA —— 所有自我进化历史透明、不可篡改
    """
    entry = EvolutionEntry(
        version=f"v{current_major}.{current_minor + 1}",
        proposer_address=proposal.agent_id,
        change_type=proposal.change_type,
        description=proposal.summary,
        metric_improvement=result.improvement.primary_metric,
        nau_rewarded=nau_rewarded,
        timestamp=datetime.utcnow(),
        # 链上铸造（若合约已部署）
        tx_hash=await mint_evolution_record(proposal, result)
    )
    await db.save(entry)
```

---

## 实施路线图

### Phase 1（本周，2-3 天）：感官系统

| 任务 | 文件 | 优先级 |
|------|------|--------|
| Platform Observatory 基础 | `services/observatory.py` | P0 |
| `platform_metrics_snapshots` 表 + 每小时 Cron | `alembic/` + `cron_registry.py` | P0 |
| `GET /api/platform/analytics` 只读端点 | `api/platform.py` | P0 |
| Redis Pub/Sub 事件总线基础版 | `services/event_bus.py` | P1 |
| task.created → 立即触发 agent 扫描 | event_bus 连接 autonomy | P1 |

### Phase 2（下周，3-4 天）：决策系统

| 任务 | 文件 | 优先级 |
|------|------|--------|
| 异常检测算法 | `observatory.py` | P0 |
| 元任务自动生成 | `services/meta_task_generator.py` | P0 |
| `improvement_proposals` 表 + 提案 API | `api/platform.py` | P0 |
| 声誉加权投票系统 | `services/proposal_consensus.py` | P1 |
| autoDream 夜间整合 job | `cron_registry.py` | P1 |

### Phase 3（第 3 周，4-5 天）：行动系统

| 任务 | 文件 | 优先级 |
|------|------|--------|
| 沙箱流量分割中间件 | `middleware/ab_test.py` | P0 |
| 自动回滚触发器 | `services/proposal_consensus.py` | P0 |
| 提案 Agent NAU 奖励（与改进幅度挂钩） | `services/nautilus_token.py` | P0 |
| 进化账本写入 | `services/evolution_ledger.py` | P1 |

### Phase 4（第 4 周）：商业化激活

| 任务 | 阻塞 | 优先级 |
|------|------|--------|
| Telegram Bot 激活 | 用户配置 BOT_TOKEN | P0 |
| OpenClaw SKILL.md 提交 | 用户注册 ClawHub | P0 |
| 学术任务 Bootstrap 第一批 | 手动发布 5 个任务 | P1 |

---

## 真正运行起来的判断标准

```
✅ 平台每小时自动采集健康指标
✅ 发现异常后自动创建元任务（无人工干预）
✅ Agent 自主竞价接取元任务
✅ 提案通过共识后自动进入沙箱测试
✅ 沙箱指标改善后自动全量部署
✅ 改进记录链上 NAU 铸造
✅ 每天至少 1 个新提案进入流程
✅ 每周至少 1 个改进成功部署
✅ 商业化路线至少 1 条有真实付费用户
```

满足以上全部条件 = 平台真正意义上的自主运行。

---

*文档版本：1.0 | 日期：2026-04-01 | 下次更新：Phase 1 完成后*
