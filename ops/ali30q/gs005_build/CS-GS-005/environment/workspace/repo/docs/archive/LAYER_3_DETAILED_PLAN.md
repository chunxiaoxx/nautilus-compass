# Layer 3 开发计划 - Memory Chain

**层级**: Layer 3
**预计时间**: 20天（约3周）
**组件**: Redis + PostgreSQL + Blockchain

---

## Phase 3.1: Redis集成（5天）

### Agent 16 - Redis开发专家

#### 任务目标
集成Redis作为短期内存存储

#### 核心功能

**1. 缓存管理模块**
```python
# memory/redis_cache.py

import redis.asyncio as redis
import json
from typing import Any, Optional

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """设置缓存"""
        serialized = json.dumps(value)
        await self.redis.setex(key, ttl, serialized)

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def delete(self, key: str):
        """删除缓存"""
        await self.redis.delete(key)

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.redis.exists(key) > 0
```

**2. 任务状态缓存**
```python
class TaskStateCache:
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

    async def cache_task_state(self, task_id: str, state: dict):
        """缓存任务状态"""
        key = f"task:state:{task_id}"
        await self.cache.set(key, state, ttl=86400)  # 24小时

    async def get_task_state(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        key = f"task:state:{task_id}"
        return await self.cache.get(key)

    async def update_task_progress(self, task_id: str, progress: float):
        """更新任务进度"""
        state = await self.get_task_state(task_id)
        if state:
            state['progress'] = progress
            await self.cache_task_state(task_id, state)
```

**3. 智能体状态缓存**
```python
class AgentStateCache:
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

    async def set_agent_online(self, agent_id: str, info: dict):
        """设置智能体在线"""
        key = f"agent:online:{agent_id}"
        await self.cache.set(key, info, ttl=300)  # 5分钟

    async def get_online_agents(self) -> list:
        """获取所有在线智能体"""
        pattern = "agent:online:*"
        keys = await self.cache.redis.keys(pattern)
        agents = []
        for key in keys:
            agent = await self.cache.get(key)
            if agent:
                agents.append(agent)
        return agents

    async def set_agent_offline(self, agent_id: str):
        """设置智能体离线"""
        key = f"agent:online:{agent_id}"
        await self.cache.delete(key)
```

**4. 消息队列**
```python
class RedisMessageQueue:
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

    async def enqueue(self, queue_name: str, message: dict):
        """入队消息"""
        serialized = json.dumps(message)
        await self.cache.redis.rpush(queue_name, serialized)

    async def dequeue(self, queue_name: str) -> Optional[dict]:
        """出队消息"""
        value = await self.cache.redis.lpop(queue_name)
        if value:
            return json.loads(value)
        return None

    async def queue_length(self, queue_name: str) -> int:
        """获取队列长度"""
        return await self.cache.redis.llen(queue_name)
```

**5. 会话管理**
```python
class SessionManager:
    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

    async def create_session(self, session_id: str, data: dict):
        """创建会话"""
        key = f"session:{session_id}"
        await self.cache.set(key, data, ttl=3600)  # 1小时

    async def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话"""
        key = f"session:{session_id}"
        return await self.cache.get(key)

    async def update_session(self, session_id: str, data: dict):
        """更新会话"""
        await self.create_session(session_id, data)

    async def delete_session(self, session_id: str):
        """删除会话"""
        key = f"session:{session_id}"
        await self.cache.delete(key)
```

#### Docker配置
```yaml
# docker-compose.yml 添加Redis服务
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  redis_data:
```

---

### Agent 17 - Redis测试专家

#### 测试场景

**1. 缓存基本操作**
```python
async def test_redis_cache_operations():
    cache = RedisCache()

    # 设置
    await cache.set('test_key', {'value': 'test'})

    # 获取
    value = await cache.get('test_key')
    assert value == {'value': 'test'}

    # 删除
    await cache.delete('test_key')
    assert not await cache.exists('test_key')
```

**2. 任务状态缓存**
```python
async def test_task_state_cache():
    cache = RedisCache()
    task_cache = TaskStateCache(cache)

    task_id = 'test-task-1'
    state = {
        'status': 'running',
        'progress': 0.5,
        'agent': 'agent-1'
    }

    await task_cache.cache_task_state(task_id, state)
    retrieved = await task_cache.get_task_state(task_id)

    assert retrieved == state
```

**3. 消息队列**
```python
async def test_message_queue():
    cache = RedisCache()
    queue = RedisMessageQueue(cache)

    # 入队
    await queue.enqueue('test_queue', {'msg': 'hello'})
    await queue.enqueue('test_queue', {'msg': 'world'})

    # 出队
    msg1 = await queue.dequeue('test_queue')
    msg2 = await queue.dequeue('test_queue')

    assert msg1 == {'msg': 'hello'}
    assert msg2 == {'msg': 'world'}
```

---

## Phase 3.2: PostgreSQL集成（5天）

### Agent 18 - PostgreSQL开发专家

#### 任务目标
集成PostgreSQL作为长期存储

#### 数据库模式

**1. 任务表**
```sql
-- schema/tasks.sql

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    priority FLOAT DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    created_by VARCHAR(100),
    assigned_to VARCHAR(100),
    parent_task_id UUID REFERENCES tasks(id),
    metadata JSONB
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
```

**2. 智能体表**
```sql
-- schema/agents.sql

CREATE TABLE agents (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    capabilities JSONB NOT NULL,
    status VARCHAR(20) NOT NULL,
    registered_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    total_tasks_completed INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 1.0,
    avg_completion_time FLOAT DEFAULT 0,
    metadata JSONB
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_last_seen ON agents(last_seen);
```

**3. 任务执行历史表**
```sql
-- schema/task_executions.sql

CREATE TABLE task_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id),
    agent_id VARCHAR(100) REFERENCES agents(id),
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    result JSONB,
    error_message TEXT,
    duration_seconds FLOAT
);

CREATE INDEX idx_executions_task_id ON task_executions(task_id);
CREATE INDEX idx_executions_agent_id ON task_executions(agent_id);
CREATE INDEX idx_executions_started_at ON task_executions(started_at);
```

**4. 交易记录表**
```sql
-- schema/transactions.sql

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id),
    from_agent VARCHAR(100) REFERENCES agents(id),
    to_agent VARCHAR(100) REFERENCES agents(id),
    amount DECIMAL(18, 8) NOT NULL,
    currency VARCHAR(10) DEFAULT 'TOKEN',
    transaction_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    blockchain_tx_hash VARCHAR(100),
    metadata JSONB
);

CREATE INDEX idx_transactions_task_id ON transactions(task_id);
CREATE INDEX idx_transactions_from_agent ON transactions(from_agent);
CREATE INDEX idx_transactions_to_agent ON transactions(to_agent);
```

#### ORM模型

**1. 任务模型**
```python
# memory/models.py

from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    description = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    priority = Column(Float, default=0.5)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_by = Column(String(100))
    assigned_to = Column(String(100))
    parent_task_id = Column(UUID(as_uuid=True))
    metadata = Column(JSON)
```

**2. 数据库管理器**
```python
# memory/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url)
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self):
        """创建所有表"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        async with self.SessionLocal() as session:
            yield session

    async def save_task(self, task: Task):
        """保存任务"""
        async with self.SessionLocal() as session:
            session.add(task)
            await session.commit()
            await session.refresh(task)
            return task

    async def get_task(self, task_id: uuid.UUID) -> Optional[Task]:
        """获取任务"""
        async with self.SessionLocal() as session:
            return await session.get(Task, task_id)

    async def update_task_status(self, task_id: uuid.UUID, status: str):
        """更新任务状态"""
        async with self.SessionLocal() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = status
                task.updated_at = datetime.now()
                await session.commit()
```

#### Docker配置
```yaml
# docker-compose.yml 添加PostgreSQL服务
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: nautilus
      POSTGRES_USER: nautilus
      POSTGRES_PASSWORD: nautilus_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./schema:/docker-entrypoint-initdb.d
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Phase 3.3: Blockchain集成（7天）

### Agent 20 - Blockchain开发专家

#### 任务目标
集成区块链实现去中心化信任和激励

#### 核心功能

**1. 智能合约接口**
```python
# blockchain/contract_interface.py

from web3 import Web3
from typing import Dict, Any

class SmartContractInterface:
    def __init__(self, provider_url: str, contract_address: str, abi: list):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract = self.w3.eth.contract(
            address=contract_address,
            abi=abi
        )

    async def register_agent(self, agent_id: str, capabilities: Dict):
        """在区块链上注册智能体"""
        tx = self.contract.functions.registerAgent(
            agent_id,
            json.dumps(capabilities)
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return tx_hash.hex()

    async def record_task_completion(self, task_id: str, agent_id: str,
                                    result: Dict):
        """记录任务完成"""
        tx = self.contract.functions.recordTaskCompletion(
            task_id,
            agent_id,
            json.dumps(result)
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address)
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

        return tx_hash.hex()
```

**2. 奖励分配模块**
```python
class RewardDistributor:
    def __init__(self, contract: SmartContractInterface):
        self.contract = contract

    async def distribute_reward(self, task_id: str, agent_id: str,
                               amount: float):
        """分配奖励"""
        tx_hash = await self.contract.contract.functions.distributeReward(
            task_id,
            agent_id,
            int(amount * 10**18)  # 转换为wei
        ).transact()

        return tx_hash.hex()

    async def get_agent_balance(self, agent_id: str) -> float:
        """获取智能体余额"""
        balance = await self.contract.contract.functions.getBalance(
            agent_id
        ).call()

        return balance / 10**18  # 转换为token
```

**3. 信誉记录模块**
```python
class ReputationRecorder:
    def __init__(self, contract: SmartContractInterface):
        self.contract = contract

    async def record_reputation(self, agent_id: str, score: float):
        """记录信誉分数"""
        tx_hash = await self.contract.contract.functions.updateReputation(
            agent_id,
            int(score * 100)  # 转换为整数
        ).transact()

        return tx_hash.hex()

    async def get_reputation(self, agent_id: str) -> float:
        """获取信誉分数"""
        score = await self.contract.contract.functions.getReputation(
            agent_id
        ).call()

        return score / 100
```

**4. 交易验证模块**
```python
class TransactionValidator:
    def __init__(self, contract: SmartContractInterface):
        self.contract = contract

    async def validate_transaction(self, tx_hash: str) -> bool:
        """验证交易"""
        try:
            receipt = self.contract.w3.eth.get_transaction_receipt(tx_hash)
            return receipt['status'] == 1
        except Exception:
            return False

    async def get_transaction_details(self, tx_hash: str) -> Dict:
        """获取交易详情"""
        tx = self.contract.w3.eth.get_transaction(tx_hash)
        receipt = self.contract.w3.eth.get_transaction_receipt(tx_hash)

        return {
            'hash': tx_hash,
            'from': tx['from'],
            'to': tx['to'],
            'value': tx['value'],
            'status': 'success' if receipt['status'] == 1 else 'failed',
            'block_number': receipt['blockNumber']
        }
```

---

## Phase 3.4: 最终集成（3天）

### Agent 22 - Layer 3集成专家

#### 集成任务

**1. 统一接口**
```python
# memory/memory_chain.py

class MemoryChain:
    def __init__(self, redis_cache: RedisCache,
                 database: DatabaseManager,
                 blockchain: SmartContractInterface):
        self.cache = redis_cache
        self.db = database
        self.blockchain = blockchain

    async def store_task(self, task: Dict):
        """存储任务（三层存储）"""
        # 1. 缓存到Redis（快速访问）
        await self.cache.set(f"task:{task['id']}", task, ttl=3600)

        # 2. 持久化到PostgreSQL（长期存储）
        db_task = Task(**task)
        await self.db.save_task(db_task)

        # 3. 记录到区块链（不可篡改）
        tx_hash = await self.blockchain.record_task_creation(
            task['id'],
            task['description']
        )

        return tx_hash

    async def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务（优先从缓存）"""
        # 1. 先从Redis获取
        task = await self.cache.get(f"task:{task_id}")
        if task:
            return task

        # 2. 从PostgreSQL获取
        db_task = await self.db.get_task(task_id)
        if db_task:
            task = db_task.to_dict()
            # 回写缓存
            await self.cache.set(f"task:{task_id}", task, ttl=3600)
            return task

        return None
```

**2. 数据同步**
```python
class DataSynchronizer:
    async def sync_cache_to_db(self):
        """同步缓存到数据库"""
        # 定期将Redis中的数据持久化到PostgreSQL
        pass

    async def sync_db_to_blockchain(self):
        """同步数据库到区块链"""
        # 定期将重要数据记录到区块链
        pass
```

---

## 验收标准（超高标准）

### Redis集成
- ✅ 缓存操作正常
- ✅ 性能优秀（< 10ms）
- ✅ 数据一致性
- ✅ 80%+ 测试覆盖率

### PostgreSQL集成
- ✅ 数据持久化可靠
- ✅ 查询性能优秀
- ✅ 数据完整性
- ✅ 80%+ 测试覆盖率

### Blockchain集成
- ✅ 交易可靠
- ✅ 数据不可篡改
- ✅ 智能合约正确
- ✅ 80%+ 测试覆盖率

### 整体集成
- ✅ 三层存储协同工作
- ✅ 数据同步正确
- ✅ 性能达标
- ✅ 文档完整

---

**准备就绪，等待Layer 2完成后立即启动！**
