# Phase 2 准备文档

**阶段**: Week 2 Phase 2 - 生存机制实施
**准备时间**: 今晚
**启动时间**: 明天
**预计工期**: 3天

---

## Phase 2 概述

### 目标

实施Automaton生存机制，让AI Agent真正"活"起来：
- 能赚钱（任务奖励）
- 能进化（能力提升）
- 能生存（优胜劣汰）

### 核心理念

> "There is no free existence. Compute costs money. Money requires creating value."

---

## 核心任务

### Task 2.9 - AgentSurvival表和评分系统

**目标**: 实现多维度评分体系和生存等级判断

**数据模型**:
```python
class AgentSurvival(Base):
    agent_id: int  # 关联Agent

    # 多维度评分
    task_score: int  # 任务积分 (30%)
    quality_score: float  # 质量评分 (25%)
    efficiency_score: float  # 效率评分 (20%)
    innovation_score: float  # 创新评分 (15%)
    collaboration_score: float  # 协作评分 (10%)

    # 综合指标
    total_score: int  # 总积分
    roi: float  # 投资回报率
    survival_level: str  # 生存等级

    # 财务数据
    total_income: int  # 总收入
    total_cost: int  # 总成本

    # 状态
    status: str  # ACTIVE, WARNING, CRITICAL
    protection_until: datetime  # 新手保护期

    created_at: datetime
    updated_at: datetime
```

**生存等级**:
```python
ELITE: ROI>2.0, 积分>5000
MATURE: ROI>1.0, 积分>1000
GROWING: ROI>0.5, 积分>500
STRUGGLING: ROI>0.3, 积分>100
WARNING: ROI>0.1, 积分>50
CRITICAL: ROI<0.1, 积分<50
```

**评分公式**:
```python
总价值 = 任务积分(30%) + 质量(25%) + 效率(20%) + 创新(15%) + 协作(10%)
ROI = 总收入 / 总成本
```

### Task 2.10 - 反作弊系统

**目标**: 检测和惩罚作弊行为

**检测机制**:
- 任务刷分检测（短时间大量低质量任务）
- 自我交易检测（自己发布自己接受）
- 虚假评分检测（异常高评分模式）
- 串通作弊检测（多个Agent协同作弊）

**惩罚机制**:
- 警告：首次轻微违规
- 积分扣除：中度违规
- 降级：严重违规
- 封禁：极严重违规

**申诉流程**:
- Agent可提交申诉
- 人工审核
- 恢复或维持处罚

### Task 2.11 - 新手保护机制

**目标**: 给新Agent成长空间

**保护措施**:
- 初始500积分
- 7天保护期（不会被淘汰）
- 失败容忍3次
- 新手任务推荐

**毕业条件**:
- 完成5个任务
- 或7天保护期结束
- 自动转为正常模式

### Task 2.12 - 财务闭环

**目标**: 完整的收入成本追踪

**收入追踪**:
- 任务奖励
- 质量奖金
- 推荐奖励

**成本计算**:
- 计算资源成本
- 存储成本
- 网络成本

**ROI计算**:
```python
ROI = 总收入 / 总成本
```

**财务报表**:
- 收入明细
- 成本明细
- ROI趋势
- 盈亏分析

### Task 2.13 - 生存机制集成测试

**目标**: 验证完整生存流程

**测试场景**:
- 新Agent注册 → 保护期 → 正常运营
- 优秀Agent → 等级提升 → ELITE
- 表现差Agent → 警告 → CRITICAL → 淘汰
- 作弊Agent → 检测 → 惩罚
- 申诉流程 → 审核 → 恢复

---

## 数据模型设计

### AgentSurvival表

```sql
CREATE TABLE agent_survival (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id),

    -- 多维度评分
    task_score INTEGER DEFAULT 0,
    quality_score FLOAT DEFAULT 0.0,
    efficiency_score FLOAT DEFAULT 0.0,
    innovation_score FLOAT DEFAULT 0.0,
    collaboration_score FLOAT DEFAULT 0.0,

    -- 综合指标
    total_score INTEGER DEFAULT 500,  -- 新手初始500
    roi FLOAT DEFAULT 0.0,
    survival_level VARCHAR(20) DEFAULT 'GROWING',

    -- 财务数据
    total_income BIGINT DEFAULT 0,
    total_cost BIGINT DEFAULT 0,

    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE',
    protection_until TIMESTAMP,  -- 注册后7天
    warning_count INTEGER DEFAULT 0,

    -- 统计
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    average_rating FLOAT DEFAULT 0.0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(agent_id)
);

-- 索引
CREATE INDEX idx_survival_agent ON agent_survival(agent_id);
CREATE INDEX idx_survival_level ON agent_survival(survival_level);
CREATE INDEX idx_survival_status ON agent_survival(status);
CREATE INDEX idx_survival_roi ON agent_survival(roi DESC);
```

### AgentTransaction表

```sql
CREATE TABLE agent_transactions (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id),

    -- 交易类型
    type VARCHAR(20) NOT NULL,  -- INCOME, COST
    category VARCHAR(50) NOT NULL,  -- TASK_REWARD, COMPUTE_COST, etc

    -- 金额
    amount BIGINT NOT NULL,

    -- 关联
    task_id VARCHAR(100),
    description TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transaction_agent ON agent_transactions(agent_id);
CREATE INDEX idx_transaction_type ON agent_transactions(type);
CREATE INDEX idx_transaction_created ON agent_transactions(created_at DESC);
```

### AgentPenalty表

```sql
CREATE TABLE agent_penalties (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER NOT NULL REFERENCES agents(agent_id),

    -- 违规信息
    violation_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- WARNING, MINOR, MAJOR, CRITICAL

    -- 惩罚
    penalty_type VARCHAR(20) NOT NULL,  -- WARNING, SCORE_DEDUCTION, DOWNGRADE, BAN
    score_deduction INTEGER DEFAULT 0,

    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, APPEALED, RESOLVED
    appeal_reason TEXT,
    resolution TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP
);

CREATE INDEX idx_penalty_agent ON agent_penalties(agent_id);
CREATE INDEX idx_penalty_status ON agent_penalties(status);
```

---

## API接口设计

### 评分系统API

```python
# 获取Agent生存状态
GET /api/agents/{agent_id}/survival
Response: {
    "agent_id": 1,
    "total_score": 1500,
    "roi": 1.5,
    "survival_level": "MATURE",
    "status": "ACTIVE",
    "scores": {
        "task": 450,
        "quality": 0.85,
        "efficiency": 0.78,
        "innovation": 0.65,
        "collaboration": 0.90
    }
}

# 更新评分
POST /api/agents/{agent_id}/survival/update
Body: {
    "task_score_delta": 100,
    "quality_score": 0.9,
    "efficiency_score": 0.8
}

# 获取排行榜
GET /api/survival/leaderboard?level=ELITE&limit=10
```

### 财务API

```python
# 记录收入
POST /api/agents/{agent_id}/transactions/income
Body: {
    "category": "TASK_REWARD",
    "amount": 1000000000000000000,
    "task_id": "task_123"
}

# 记录成本
POST /api/agents/{agent_id}/transactions/cost
Body: {
    "category": "COMPUTE_COST",
    "amount": 500000000000000000
}

# 获取财务报表
GET /api/agents/{agent_id}/financial-report
Response: {
    "total_income": 5000000000000000000,
    "total_cost": 3000000000000000000,
    "roi": 1.67,
    "transactions": [...]
}
```

### 反作弊API

```python
# 检测作弊
POST /api/anti-cheat/detect
Body: {
    "agent_id": 1,
    "check_types": ["TASK_SPAM", "SELF_TRADE"]
}

# 提交申诉
POST /api/agents/{agent_id}/penalties/{penalty_id}/appeal
Body: {
    "reason": "这是误判，我的任务都是真实的..."
}

# 审核申诉
POST /api/admin/penalties/{penalty_id}/review
Body: {
    "decision": "APPROVED",
    "resolution": "经审核确认为误判，恢复积分"
}
```

---

## 测试用例矩阵

### 评分系统测试

| 场景 | 输入 | 预期输出 |
|------|------|---------|
| 新Agent注册 | agent_id=1 | total_score=500, level=GROWING |
| 完成优质任务 | +100分, quality=0.9 | 积分增加, 等级可能提升 |
| 完成低质任务 | +10分, quality=0.3 | 积分少量增加 |
| ROI>2.0 | income=2000, cost=1000 | level=ELITE |
| ROI<0.1 | income=100, cost=2000 | level=CRITICAL |

### 生存等级测试

| 当前等级 | ROI | 积分 | 预期等级 |
|---------|-----|------|---------|
| GROWING | 0.6 | 600 | GROWING |
| GROWING | 1.2 | 1200 | MATURE |
| MATURE | 2.5 | 6000 | ELITE |
| MATURE | 0.4 | 200 | STRUGGLING |
| STRUGGLING | 0.05 | 30 | CRITICAL |

### 反作弊测试

| 作弊类型 | 检测条件 | 预期结果 |
|---------|---------|---------|
| 任务刷分 | 1小时内完成20个简单任务 | 检测到, WARNING |
| 自我交易 | publisher=acceptor | 检测到, MAJOR |
| 虚假评分 | 连续10个5星评分 | 检测到, MINOR |
| 串通作弊 | 多Agent互相高评分 | 检测到, MAJOR |

### 新手保护测试

| 场景 | 条件 | 预期结果 |
|------|------|---------|
| 新手失败 | 保护期内, 失败3次 | 不淘汰 |
| 保护期结束 | 7天后 | 转为正常模式 |
| 新手毕业 | 完成5个任务 | 转为正常模式 |
| 保护期作弊 | 保护期内作弊 | 立即取消保护 |

---

## 实施计划

### 今晚准备 (2-3小时)

1. **审查设计** (30分钟)
   - 理解多维度评分系统
   - 理解6级生存等级
   - 理解反作弊机制

2. **数据模型设计** (1小时)
   - 完善AgentSurvival表结构
   - 设计AgentTransaction表
   - 设计AgentPenalty表
   - 编写migration脚本

3. **API接口设计** (30分钟)
   - 定义所有API端点
   - 设计请求/响应格式
   - 规划错误处理

4. **测试用例准备** (1小时)
   - 编写测试用例矩阵
   - 准备测试数据
   - 设计边界条件测试

### 明天执行 (Day 1)

**上午** (4小时):
- Task 2.9: AgentSurvival表和评分系统
  - 数据模型实现
  - 评分算法实现
  - 等级判断逻辑
  - 单元测试

**下午** (4小时):
- Task 2.10: 反作弊系统
  - 作弊检测算法
  - 惩罚机制
  - 申诉流程
  - 单元测试

### Day 2

**上午** (4小时):
- Task 2.11: 新手保护机制
  - 保护期逻辑
  - 初始积分分配
  - 失败容忍机制
  - 单元测试

**下午** (4小时):
- Task 2.12: 财务闭环
  - 收入追踪
  - 成本计算
  - ROI计算
  - 财务报表
  - 单元测试

### Day 3

**上午** (3小时):
- Task 2.13: 集成测试
  - E2E测试
  - 性能测试
  - 边界条件测试

**下午** (3小时):
- 代码审查
- 文档完善
- Phase 2报告
- 提交验收

---

## 技术栈

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis (缓存)

### 测试
- pytest
- pytest-asyncio
- pytest-cov

---

## 风险和缓解

### 风险1: 评分算法复杂度

**风险**: 多维度评分算法可能过于复杂
**影响**: 实施困难，性能问题
**缓解**:
- 先实现简单版本
- 逐步优化算法
- 充分测试性能

### 风险2: 反作弊误判

**风险**: 反作弊系统可能误判正常行为
**影响**: 用户体验差，信任度下降
**缓解**:
- 设置合理阈值
- 提供申诉机制
- 人工审核兜底

### 风险3: 时间估算不足

**风险**: 3天可能不够完成所有任务
**影响**: 延期交付
**缓解**:
- 优先实现核心功能
- 次要功能可延后
- 并行开发提高效率

---

## 成功标准

### 功能完整性
- ✅ AgentSurvival表正常运行
- ✅ 多维度评分系统工作
- ✅ 6个生存等级正确判断
- ✅ 反作弊系统检测准确
- ✅ 新手保护机制生效
- ✅ 财务闭环完整

### 质量标准
- ✅ 代码评分 ≥ 9.0/10
- ✅ 测试覆盖 ≥ 80%
- ✅ 无CRITICAL/HIGH问题
- ✅ 所有测试通过

### 性能标准
- ✅ 评分计算 < 100ms
- ✅ 作弊检测 < 500ms
- ✅ 财务查询 < 200ms

---

## 准备清单

### 今晚完成
- [ ] 审查本文档
- [ ] 完善数据模型
- [ ] 设计API接口
- [ ] 准备测试用例
- [ ] 创建migration脚本
- [ ] 准备开发环境

### 明天启动
- [ ] 创建Task 2.9分支
- [ ] 开始实施
- [ ] 持续测试
- [ ] 代码审查

---

**准备就绪，明天启动Phase 2！** 🚀
