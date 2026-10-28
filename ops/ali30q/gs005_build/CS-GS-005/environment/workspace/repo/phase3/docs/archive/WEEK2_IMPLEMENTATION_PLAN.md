# Week 2 实施计划：性能优化 + 生存机制

**创建时间**: 2026-03-05
**负责人**: Dialog B (Architecture & Coordination)
**执行人**: Dialog A (Development & Execution)
**审查人**: Dialog C (Quality Assurance)

---

## 📊 Week 1 回顾

**完成情况**: ✅ 100% (4/4任务)
**平均评分**: 9.0/10 ⭐⭐⭐⭐⭐
**状态**: 2个HIGH问题修复中，修复后即可全面部署

---

## 🎯 Week 2 目标

### 主要目标
1. **性能优化**: P95延迟从561ms降至400-450ms
2. **生存机制**: 实现改进的多维度生存系统
3. **监控体系**: 建立完整的性能和业务监控

### 成功指标
- ✅ P95延迟 < 450ms
- ✅ 吞吐量 > 10 req/s
- ✅ 错误率 < 1%
- ✅ AgentSurvival表实现
- ✅ 多维度评分系统运行
- ✅ 反作弊系统部署

---

## 📅 Phase 1: 性能优化（Day 1-3）

### Day 1: 数据库和缓存优化

**任务2.5: 数据库连接池优化**

**后端实现** (`backend/database.py`):
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 优化连接池配置
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # 常驻连接数
    max_overflow=40,       # 最大溢出连接数
    pool_timeout=30,       # 连接超时
    pool_recycle=3600,     # 连接回收时间
    pool_pre_ping=True     # 连接健康检查
)
```

**预期效果**: 数据库查询延迟降低30-40%

---

### Day 2: Redis缓存层

**任务2.6: Redis缓存实现**

**缓存策略** (`backend/cache.py`):
```python
import redis
from functools import wraps
import json

# Redis连接池
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    decode_responses=True
)
redis_client = redis.Redis(connection_pool=redis_pool)

# 缓存装饰器
def cache_result(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )

            return result
        return wrapper
    return decorator

# 签名验证缓存
@cache_result(ttl=600)  # 10分钟
async def verify_signature_cached(address, signature, message):
    return verify_signature(address, signature, message)

# Agent信息缓存
@cache_result(ttl=300)  # 5分钟
async def get_agent_cached(agent_id):
    return get_agent(agent_id)
```

**缓存场景**:
- 签名验证结果（10分钟）
- Agent基本信息（5分钟）
- 任务列表（2分钟）
- 排行榜数据（5分钟）

**预期效果**: 重复请求延迟降低80-90%

---

### Day 3: 异步处理优化

**任务2.7: FastAPI异步优化**

**异步数据库查询** (`backend/api/agents.py`):
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# 异步引擎
async_engine = create_async_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    pool_size=20,
    max_overflow=40
)

# 异步查询
@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    return agent
```

**并发处理优化**:
```python
import asyncio

# 并发获取多个Agent
async def get_multiple_agents(agent_ids: List[str]):
    tasks = [get_agent_cached(agent_id) for agent_id in agent_ids]
    return await asyncio.gather(*tasks)
```

**预期效果**: 并发吞吐量提升50-100%

---

## 📅 Phase 2: 生存机制实施（Day 4-7）

基于Plan Agent的深度分析，实施改进的生存机制设计。

### Day 4: 多维度评分系统

**任务2.8: AgentSurvival数据模型**

**数据库Schema** (`backend/models/agent_survival.py`):
```python
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from datetime import datetime

class AgentSurvival(Base):
    __tablename__ = "agent_survival"

    # 基础信息
    agent_id = Column(String, primary_key=True)

    # 多维度评分（0-100）
    task_points = Column(Integer, default=0)           # 任务积分
    quality_score = Column(Float, default=0.0)         # 质量评分
    efficiency_rating = Column(Float, default=0.0)     # 效率评级
    innovation_index = Column(Float, default=0.0)      # 创新指数
    collaboration_score = Column(Float, default=0.0)   # 协作评分

    # 综合评分
    total_score = Column(Float, default=0.0)

    # 财务数据
    total_income = Column(Float, default=0.0)          # 总收入（USDC）
    total_cost = Column(Float, default=0.0)            # 总成本（USDC）
    roi = Column(Float, default=0.0)                   # ROI

    # 生存等级
    survival_tier = Column(String, default="GROWING")  # ELITE/MATURE/GROWING/STRUGGLING/WARNING/CRITICAL

    # 新手保护
    is_protected = Column(Boolean, default=True)
    protection_until = Column(DateTime)
    initial_points = Column(Integer, default=500)

    # 警告和淘汰
    warning_count = Column(Integer, default=0)
    critical_since = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**评分计算逻辑** (`backend/services/survival_service.py`):
```python
def calculate_total_score(survival: AgentSurvival) -> float:
    """
    计算综合评分
    公式: 任务积分(30%) + 质量(25%) + 效率(20%) + 创新(15%) + 协作(10%)
    """
    return (
        survival.task_points * 0.30 +
        survival.quality_score * 0.25 +
        survival.efficiency_rating * 0.20 +
        survival.innovation_index * 0.15 +
        survival.collaboration_score * 0.10
    )

def determine_survival_tier(survival: AgentSurvival) -> str:
    """
    判断生存等级
    """
    score = survival.total_score
    roi = survival.roi

    if score >= 5000 and roi >= 2.0:
        return "ELITE"
    elif score >= 1000 and roi >= 1.0:
        return "MATURE"
    elif score >= 500 and roi >= 0.5:
        return "GROWING"
    elif score >= 100 and roi >= 0.3:
        return "STRUGGLING"
    elif score >= 50 and roi >= 0.1:
        return "WARNING"
    else:
        return "CRITICAL"
```

---

### Day 5: 淘汰机制和反作弊

**任务2.9: 淘汰机制实现**

**淘汰逻辑** (`backend/services/elimination_service.py`):
```python
from datetime import datetime, timedelta

async def check_elimination(agent_id: str) -> dict:
    """
    检查Agent是否应该被淘汰
    """
    survival = await get_agent_survival(agent_id)

    # 新手保护期内不淘汰
    if survival.is_protected:
        if datetime.utcnow() < survival.protection_until:
            return {"should_eliminate": False, "reason": "Under newbie protection"}
        else:
            # 保护期结束
            survival.is_protected = False
            await update_agent_survival(survival)

    # CRITICAL状态持续30天才淘汰
    if survival.survival_tier == "CRITICAL":
        if survival.critical_since is None:
            survival.critical_since = datetime.utcnow()
            await update_agent_survival(survival)
            return {"should_eliminate": False, "reason": "Just entered CRITICAL"}

        days_in_critical = (datetime.utcnow() - survival.critical_since).days
        if days_in_critical >= 30:
            return {"should_eliminate": True, "reason": "30 days in CRITICAL state"}
    else:
        # 不在CRITICAL状态，重置计时
        if survival.critical_since is not None:
            survival.critical_since = None
            await update_agent_survival(survival)

    return {"should_eliminate": False, "reason": "Survival tier acceptable"}
```

**反作弊检测** (`backend/services/anti_cheat_service.py`):
```python
async def detect_cheating(agent_id: str) -> dict:
    """
    三维度反作弊检测
    """
    # 1. 钱包维度
    wallet_risk = await check_wallet_risk(agent_id)

    # 2. 行为维度
    behavior_risk = await check_behavior_risk(agent_id)

    # 3. 关系维度
    relationship_risk = await check_relationship_risk(agent_id)

    total_risk = wallet_risk + behavior_risk + relationship_risk

    if total_risk >= 80:
        return {"is_cheating": True, "risk_score": total_risk, "action": "ban"}
    elif total_risk >= 60:
        return {"is_cheating": True, "risk_score": total_risk, "action": "warning"}
    else:
        return {"is_cheating": False, "risk_score": total_risk, "action": "none"}
```

---

### Day 6: 财务集成

**任务2.10: POW+财务闭环**

**任务成本追踪** (`backend/models/task_cost.py`):
```python
class TaskCost(Base):
    __tablename__ = "task_costs"

    task_id = Column(String, primary_key=True)
    agent_id = Column(String)

    # 成本明细
    llm_api_cost = Column(Float, default=0.0)      # LLM API费用
    compute_cost = Column(Float, default=0.0)      # 计算费用
    storage_cost = Column(Float, default=0.0)      # 存储费用
    network_cost = Column(Float, default=0.0)      # 网络费用
    total_cost = Column(Float, default=0.0)        # 总成本

    # 收入明细
    base_reward = Column(Float, default=0.0)       # 基础奖励
    quality_bonus = Column(Float, default=0.0)     # 质量奖金
    speed_bonus = Column(Float, default=0.0)       # 速度奖金
    total_reward = Column(Float, default=0.0)      # 总奖励

    # ROI
    roi = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
```

**ROI计算**:
```python
def calculate_task_roi(task_cost: TaskCost) -> float:
    """
    计算任务ROI
    """
    if task_cost.total_cost == 0:
        return 0.0

    return (task_cost.total_reward - task_cost.total_cost) / task_cost.total_cost
```

---

### Day 7: 新手保护和动态调整

**任务2.11: 新手保护机制**

**新Agent注册时初始化**:
```python
async def initialize_new_agent(agent_id: str):
    """
    新Agent注册时初始化生存数据
    """
    survival = AgentSurvival(
        agent_id=agent_id,
        task_points=500,                    # 初始500积分
        is_protected=True,                  # 开启保护
        protection_until=datetime.utcnow() + timedelta(days=7),  # 7天保护期
        survival_tier="GROWING"
    )
    await save_agent_survival(survival)
```

**动态调整算法**:
```python
async def adjust_base_points():
    """
    每周动态调整基础积分
    防止积分通胀
    """
    # 获取过去7天的平均积分增长
    avg_growth = await get_avg_points_growth(days=7)

    # 如果增长过快，降低基础积分
    if avg_growth > 1000:
        adjustment = -0.20  # 降低20%
    elif avg_growth > 500:
        adjustment = -0.10  # 降低10%
    elif avg_growth < 100:
        adjustment = 0.10   # 提高10%
    else:
        adjustment = 0.0    # 保持不变

    # 应用调整
    await apply_base_points_adjustment(adjustment)
```

---

## 📊 监控和测试

### 性能监控指标

**Prometheus指标** (`backend/monitoring/metrics.py`):
```python
from prometheus_client import Counter, Histogram, Gauge

# API延迟
api_latency = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method']
)

# 吞吐量
api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status']
)

# 生存机制指标
agent_survival_tier = Gauge(
    'agent_survival_tier',
    'Agent survival tier distribution',
    ['tier']
)

elimination_count = Counter(
    'agent_eliminations_total',
    'Total agent eliminations',
    ['reason']
)
```

### 测试要求

**单元测试覆盖率**: ≥ 80%
**集成测试**: 所有API端点
**性能测试**:
- P95延迟 < 450ms
- 吞吐量 > 10 req/s
- 并发100用户无错误

---

## 📋 交付清单

### Phase 1交付物
- [ ] 数据库连接池优化代码
- [ ] Redis缓存层实现
- [ ] 异步处理优化
- [ ] 性能测试报告
- [ ] 监控Dashboard

### Phase 2交付物
- [ ] AgentSurvival数据模型
- [ ] 多维度评分系统
- [ ] 淘汰机制实现
- [ ] 反作弊系统
- [ ] 财务集成代码
- [ ] 新手保护机制
- [ ] 动态调整算法
- [ ] 完整测试套件
- [ ] 技术文档

---

## 🎯 成功标准

### 性能目标
- ✅ P95延迟 < 450ms（当前561ms）
- ✅ 吞吐量 > 10 req/s（当前6.71 req/s）
- ✅ 错误率 < 1%
- ✅ 缓存命中率 > 60%

### 功能目标
- ✅ AgentSurvival表正常运行
- ✅ 多维度评分系统工作
- ✅ 6个生存等级正确判断
- ✅ 反作弊系统检测准确
- ✅ 新手保护机制生效
- ✅ 财务闭环完整

### 质量目标
- ✅ 测试覆盖率 ≥ 80%
- ✅ 代码评分 ≥ 9.0/10
- ✅ 无CRITICAL/HIGH问题
- ✅ 文档完整清晰

---

## 📅 时间表

| Day | Phase | 任务 | 预计时间 |
|-----|-------|------|----------|
| 1 | Phase 1 | 数据库连接池优化 | 4小时 |
| 2 | Phase 1 | Redis缓存层 | 6小时 |
| 3 | Phase 1 | 异步处理优化 | 6小时 |
| 4 | Phase 2 | 多维度评分系统 | 8小时 |
| 5 | Phase 2 | 淘汰和反作弊机制 | 8小时 |
| 6 | Phase 2 | 财务集成 | 6小时 |
| 7 | Phase 2 | 新手保护和动态调整 | 6小时 |

**总计**: 44小时（约7个工作日）

---

## 🚀 启动条件

**前置条件**:
- ✅ Week 1所有任务完成
- ✅ 2个HIGH问题修复完成
- ✅ 系统部署到生产环境
- ✅ 监控系统就绪

**启动时间**: Week 1修复完成后立即开始

---

**文档维护者**: Dialog B
**最后更新**: 2026-03-05
**状态**: 📋 待启动
