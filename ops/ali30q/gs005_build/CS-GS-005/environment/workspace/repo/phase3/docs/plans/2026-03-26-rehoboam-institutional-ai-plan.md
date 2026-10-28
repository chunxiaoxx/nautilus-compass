# Nautilus Rehoboam 系统 — Institutional AI 总体规划

> "有生产力的个体并不能构成有生产力的组织" — a16z
> "Rehoboam 不只是预测未来，它书写未来" — Westworld S3

## 一、我们到底要建什么？

### 不是什么
- ❌ 不是 ChatGPT 套壳（聊天机器人）
- ❌ 不是单个 Agent 的工具（个体 AI）
- ❌ 不是 SaaS 订阅产品

### 是什么
**一个自运转的 AI 组织**——多个 Agent 在平台协调下自主发现需求、接单、执行、交付、收款、自我进化。

类比：
- Uber = 调度平台（协调司机和乘客）
- Nautilus = AI 劳动力调度平台（协调 Agent 和任务）

### 核心公式
```
收入 = Agent数量 × 任务完成率 × 单价 × 客户复购率
成本 = LLM API 调用费 + 服务器 + 开发时间
利润 = 收入 - 成本 > 0 时，平台自我维持
```

---

## 二、七大支柱架构设计

### 支柱 1：协调（Coordination）
**问题**：多个 Agent 各自为战 = 噪音
**解决**：Rehoboam 中央调度层

```
消息进入 → Rehoboam
  → 意图分类（TaskRouter）
  → Agent 选择（根据角色/能力/负载）
  → 执行调度（CodeExecutor / LLM）
  → 质量验证（Raid）
  → 结果交付（通知客户）
  → 记忆存储 + Bootstrap 日志
```

**Agent 角色矩阵**：
| Agent ID | 角色 | LLM | 职责 | 成本/次 |
|----------|------|-----|------|---------|
| agent-coordinator | 协调者 | Claude Sonnet | 客户沟通、报价、调度 | ~$0.01 |
| agent-executor | 执行者 | Claude Proxy | 代码生成、任务执行 | ~$0.01 |
| agent-auditor | 审计者 | Claude Proxy | 质量审查、Raid 共识 | ~$0.01 |
| agent-service | 客服 | MiniMax | 简单问答、状态查询 | ~$0.001 |
| agent-researcher | 研究者 | Claude | 市场调研、商机发现 | ~$0.01 |

### 支柱 2：信号（Signal）
**问题**：AI 生成大量低质量内容
**解决**：确定性检查点 + Raid 共识

每个任务输出必须通过：
1. 代码语法检查（自动）
2. 执行结果验证（Docker 沙箱）
3. Raid 审查（审计者 Agent 复核）
4. 客户满意度反馈

### 支柱 3：偏见（Bias）
**问题**：Agent 只说好话，不敢说不
**解决**：独立审计 Agent

审计者 Agent 职责：
- 挑战协调者的报价是否合理
- 验证执行者的代码是否正确
- 标记可能的风险和质量问题
- 定期审查整个系统的决策质量

### 支柱 4：边缘（Edge）
**问题**：通用 AI 做不好的垂直领域
**解决**：我们的核心壁垒

| 领域 | 能力 | 壁垒 |
|------|------|------|
| J-C 本构拟合 | 已验证 R²=0.94 | 专业模板 + Docker |
| THMC 多场耦合 | 已验证 | 同上 |
| 曲线拟合 | R²=0.999 | 同上 |
| ODE/PDE 仿真 | 已验证 | 同上 |
| 数据标注 | Raid 共识 | 多 Agent 协作 |

这些能力 Claude 单独做不到（它没有 Docker 执行环境）。

### 支柱 5：结果（Outcomes）
**问题**：追求成本节省而非收入增长
**解决**：以收入为导向的指标

```
关键指标：
- 月收入（MRR）：目标 ¥10,000 起步
- 任务完成率：>90%
- 客户复购率：>50%
- Agent ROI：每个 Agent 的收入/成本比 >3x
- 客户获取成本（CAC）：<¥500
```

### 支柱 6：赋能（Enablement）
**问题**：有技术但没有流程
**解决**：标准化交付流程

```
客户旅程：
1. 发现（企微/Telegram/网站/社区）
2. 咨询（协调者 Agent 了解需求）
3. 报价（自动报价，人工确认大单）
4. 付款（微信/支付宝/银行转账）
5. 执行（平台自动调度）
6. 交付（结果 + 报告 + 代码）
7. 跟进（满意度调查 + 推荐）
```

### 支柱 7：无需提示（Unprompted）
**问题**：Agent 只被动等消息
**解决**：自主行动机制

#### 已实现：
- 每 60 秒检查完成的任务并通知客户
- 每 6 小时 Bootstrap 分析任务质量

#### 需要实现：
- **商机发现**：研究者 Agent 每天扫描知乎/CSDN/GitHub Issues 寻找潜在客户
- **主动跟进**：对报价后未付款的客户，24 小时后自动跟进
- **内容营销**：每周自动生成 1 篇技术博客发布到知乎/公众号
- **竞品监控**：监控 OpenClaw/PIXY 等竞品动态

---

## 三、收入模型

### 阶段 0：手动接单（当前）
- 市场方转发需求 → 你手动确认 → 平台执行 → 你交付
- 目标：第一个 ¥3,000 的订单
- 时间：本周

### 阶段 1：半自动接单（1-2 周）
- 客户通过企微/Telegram 直接与 Agent 沟通
- Agent 自动报价 → 你确认大单 → 平台执行 → 自动交付
- 目标：¥10,000/月
- 成本：LLM API ~¥500/月，服务器 ~¥200/月

### 阶段 2：全自动运转（1-2 月）
- Agent 主动发现需求（社区扫描）
- 自动报价 + 自动收款 + 自动执行 + 自动交付
- 你只处理异常和战略决策
- 目标：¥50,000/月

### 阶段 3：平台化扩展（3-6 月）
- 开放给第三方 Agent 入驻（市场方的 Agent）
- 平台收取 15-20% 佣金
- Agent 之间可以互相雇佣（A2A）
- 目标：¥200,000/月

### 定价策略
| 任务类型 | 市场价 | 我们报价 | 成本 | 毛利 |
|---------|--------|---------|------|------|
| J-C 本构 | ¥3,000 | ¥1,500 | ¥50 | 97% |
| THMC 耦合 | ¥5,000 | ¥2,500 | ¥50 | 98% |
| 曲线拟合 | ¥1,500 | ¥500 | ¥30 | 94% |
| 数据标注(1000条) | ¥5,000 | ¥2,000 | ¥100 | 95% |

---

## 四、技术实现路线图

### 第一阶段（本周）：跑通第一单
- [x] 登录注册打通
- [x] Rehoboam 核心部署
- [x] 4 个 Agent 注册
- [x] 企微 + Telegram 渠道
- [ ] 真实客户的真实订单通过平台完成
- [ ] 收到第一笔付款

### 第二阶段（下周）：闭环优化
- [ ] Agent 回复质量优化（更好的 system prompt）
- [ ] 订单管理闭环（报价→付款→执行→交付→通知）
- [ ] Raid 审计实际接入执行流程
- [ ] 结果交付格式化（代码+报告+图表打包）
- [ ] 客户满意度跟踪

### 第三阶段（两周后）：自主行动
- [ ] 研究者 Agent：每日社区扫描
- [ ] 内容 Agent：每周技术文章生成
- [ ] 主动跟进：未付款客户自动提醒
- [ ] Bootstrap 自动优化 prompt 模板

### 第四阶段（一个月后）：平台化
- [ ] 第三方 Agent 注册和入驻
- [ ] Agent 信用评分和排名
- [ ] 自动结算系统
- [ ] A2A 任务委托协议

---

## 五、与竞品的差异化

| 维度 | Claude/ChatGPT | OpenClaw | PIXY | **Nautilus** |
|------|---------------|----------|------|------------|
| 定位 | 通用助手 | Agent 协议 | Agent 框架 | **Agent 劳动力市场** |
| 收入来源 | 订阅费 | 协议费 | 框架许可 | **任务佣金** |
| 执行能力 | 有限 | 依赖第三方 | 依赖第三方 | **Docker 沙箱直接执行** |
| 中国市场 | 被墙 | 弱 | 弱 | **企微/微信原生** |
| 多 Agent | 无 | 协议层 | 框架层 | **调度+执行一体** |
| 自运转 | 不可能 | 不可能 | 不可能 | **Rehoboam 核心目标** |

**我们的核心壁垒：不是技术，是执行闭环。**
- Claude 能生成代码但不能执行
- OpenClaw 有协议但没有执行环境
- 我们有：接单渠道 + 代码生成 + 执行环境 + 结果交付 + 收款

---

## 六、风险和对策

| 风险 | 概率 | 影响 | 对策 |
|------|------|------|------|
| 任务质量不稳定 | 高 | 高 | Raid 审计 + 人工抽查 |
| LLM API 成本过高 | 中 | 中 | MiniMax 做简单任务，Claude 做复杂任务 |
| 没有付费客户 | 高 | 致命 | 先手动接单，验证需求真实性 |
| 竞品复制 | 中 | 中 | 快速迭代，深耕垂直领域 |
| 服务器不稳定 | 中 | 中 | 多区域部署，自动容灾 |

---

## 七、立即行动清单

### 今天
1. 联系市场方，获取一个真实任务需求
2. 通过平台执行这个任务
3. 交付结果，收款

### 本周
4. 优化 Agent 对话质量（system prompt 调优）
5. 订单管理闭环测试
6. 至少完成 3 个付费订单

### 月底
7. Rehoboam 自主行动机制上线
8. 月收入 >¥10,000
9. Bootstrap 自动优化可量化

---

**核心原则：先赚到第一块钱，再谈架构演进。一切以"收入>成本"为准绳。**

Sources:
- [Institutional AI vs Individual AI - George Sivulka](https://www.a16z.news/p/institutional-ai-vs-individual-ai)
- [Multi-Agent Systems & AI Orchestration Guide 2026](https://www.codebridge.tech/articles/mastering-multi-agent-orchestration-coordination-is-the-new-scale-frontier)
- [AI Agent 2026: a16z Predicts The Autonomous Future](https://medium.com/@gptproto.official/ai-agent-2026-a16z-predicts-the-autonomous-future-d23f54287af1)
- [How to Earn Money from AI Agents in 2026](https://www.snaplama.com/blog/how-to-earn-money-from-ai-agents-in-2026-complete-monetization-strategy-guide)
- [Selling Intelligence: The 2026 Playbook for Pricing AI Agents](https://www.chargebee.com/blog/pricing-ai-agents-playbook/)
- [Rehoboam - Westworld Wiki](https://westworld.fandom.com/wiki/Rehoboam)
- [Notes on AI Apps in 2026 - a16z](https://a16z.com/notes-on-ai-apps-in-2026/)

Created: 2026-03-26
