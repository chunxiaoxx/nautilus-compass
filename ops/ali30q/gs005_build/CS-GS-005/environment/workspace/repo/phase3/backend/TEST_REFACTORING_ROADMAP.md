# 测试架构重构路线图

**目标**: 建立稳定、可靠的测试架构
**优先级**: 中期（1-2个月）
**前置条件**: 核心功能稳定运行

---

## 问题诊断

### 当前测试架构的致命缺陷

```
┌─────────────────────────────────────────────────────────┐
│  问题: 15个测试文件各自管理独立数据库                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  test_api.py          → test_api.db                     │
│  test_performance.py  → test_performance.db             │
│  test_gas_api.py      → test_gas_api.db                 │
│  ...                  → ...                             │
│                                                         │
│  所有文件都设置: app.dependency_overrides[get_db]        │
│                                                         │
│  结果: 全局状态冲突 → 测试失败 → 不稳定                  │
└─────────────────────────────────────────────────────────┘
```

---

## 重构方案

### 阶段1: 统一数据库管理 (1周)

#### 目标
- 所有测试使用同一个数据库实例
- 在 `conftest.py` 中集中管理

#### 实施步骤

**1. 修改 conftest.py**
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from models.database import Base
from utils.database import get_db

# 全局测试数据库
TEST_DATABASE_URL = "sqlite:///./test_unified.db"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)

def override_get_db():
    """统一的数据库override"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """会话级别的数据库设置"""
    # 设置全局override
    app.dependency_overrides[get_db] = override_get_db

    # 创建所有表
    Base.metadata.create_all(bind=test_engine)

    yield

    # 清理
    Base.metadata.drop_all(bind=test_engine)
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

@pytest.fixture(scope="function", autouse=True)
def clean_database():
    """每个测试前清理数据库"""
    db = TestingSessionLocal()
    try:
        # 清空所有表
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    finally:
        db.close()
    yield
```

**2. 修改所有测试文件**

删除每个测试文件中的：
```python
# ❌ 删除这些
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_XXX.db"
engine = create_engine(...)
app.dependency_overrides[get_db] = override_get_db
```

使用统一的fixture：
```python
# ✅ 使用这些
from conftest import TestingSessionLocal

def test_something():
    db = TestingSessionLocal()
    # ... 测试代码
    db.close()
```

**3. 影响的文件清单**
- [ ] test_api_tasks_extended.py
- [ ] test_api_rewards_extended.py
- [ ] test_api_auth_extended.py
- [ ] test_performance.py
- [ ] test_gas_api.py
- [ ] test_e2e_edge_cases.py
- [ ] test_api_extended.py
- [ ] test_e2e_agents_rewards.py
- [ ] test_e2e_tasks.py
- [ ] test_api_complete.py
- [ ] test_e2e_websocket.py
- [ ] test_e2e_api_keys.py
- [ ] test_postgres_integration.py
- [ ] test_e2e_auth.py
- [ ] test_integration.py

---

### 阶段2: 改进测试隔离 (1周)

#### 使用事务回滚

```python
@pytest.fixture(scope="function")
def db_session():
    """提供事务隔离的数据库会话"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    # 回滚事务，确保测试隔离
    session.close()
    transaction.rollback()
    connection.close()
```

#### 使用示例

```python
def test_create_task(db_session):
    """测试创建任务"""
    task = Task(
        task_id="test_123",
        publisher="0x123...",
        description="Test task"
    )
    db_session.add(task)
    db_session.commit()

    # 验证
    assert db_session.query(Task).count() == 1

    # 测试结束后自动回滚，不影响其他测试
```

---

### 阶段3: 优化测试性能 (3天)

#### 1. 使用内存数据库
```python
TEST_DATABASE_URL = "sqlite:///:memory:"
```

#### 2. 并行运行测试
```bash
pip install pytest-xdist
pytest -n auto  # 自动使用所有CPU核心
```

#### 3. 缓存fixture
```python
@pytest.fixture(scope="session")
def sample_user():
    """会话级别的示例用户，避免重复创建"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "wallet_address": "0x123..."
    }
```

---

### 阶段4: 建立测试标准 (持续)

#### 测试编写规范

**✅ 好的实践**
```python
def test_create_task_success(db_session, sample_user):
    """测试成功创建任务"""
    # Arrange - 准备数据
    task_data = {
        "task_id": "test_123",
        "publisher": sample_user["wallet_address"],
        "description": "Test task"
    }

    # Act - 执行操作
    task = Task(**task_data)
    db_session.add(task)
    db_session.commit()

    # Assert - 验证结果
    assert db_session.query(Task).count() == 1
    assert task.task_id == "test_123"
```

**❌ 避免的做法**
```python
def test_something():
    """不清楚的测试名称"""
    # 直接操作全局状态
    app.dependency_overrides[get_db] = my_override

    # 没有清理
    # 依赖其他测试的数据
    # 使用硬编码的ID
```

#### 测试组织结构

```
tests/
├── conftest.py              # 全局配置和fixture
├── fixtures/                # 共享的fixture
│   ├── __init__.py
│   ├── database.py          # 数据库fixture
│   ├── users.py             # 用户fixture
│   └── tasks.py             # 任务fixture
├── unit/                    # 单元测试
│   ├── test_models.py
│   ├── test_utils.py
│   └── test_services.py
├── integration/             # 集成测试
│   ├── test_api_auth.py
│   ├── test_api_tasks.py
│   └── test_api_rewards.py
└── e2e/                     # 端到端测试
    ├── test_task_workflow.py
    └── test_agent_workflow.py
```

---

## 实施计划

### 第1周: 准备和规划
- [ ] 代码审查当前测试
- [ ] 创建重构分支
- [ ] 备份当前测试数据库
- [ ] 设置测试环境

### 第2周: 统一数据库管理
- [ ] 修改 conftest.py
- [ ] 重构前5个测试文件
- [ ] 运行测试验证
- [ ] 修复发现的问题

### 第3周: 继续重构
- [ ] 重构剩余10个测试文件
- [ ] 添加事务隔离
- [ ] 优化测试性能
- [ ] 完整测试套件验证

### 第4周: 优化和文档
- [ ] 性能优化
- [ ] 编写测试指南
- [ ] 代码审查
- [ ] 合并到主分支

---

## 成功指标

### 测试稳定性
- ✅ 连续10次运行，通过率变化 < 1%
- ✅ 测试总数保持一致
- ✅ 无随机失败

### 测试性能
- ✅ 完整测试套件 < 5分钟
- ✅ 单个测试 < 1秒
- ✅ 支持并行运行

### 代码质量
- ✅ 测试覆盖率 > 80%
- ✅ 所有测试有清晰的文档
- ✅ 遵循统一的编码规范

---

## 风险管理

### 潜在风险

1. **破坏现有测试**
   - 缓解: 在独立分支工作，频繁验证

2. **时间超支**
   - 缓解: 分阶段实施，每周评估进度

3. **团队抵触**
   - 缓解: 充分沟通，展示收益

### 回滚计划

如果重构失败：
1. 恢复到重构前的代码
2. 保留文档和经验教训
3. 重新评估方案

---

## 资源需求

### 人力
- **主要开发者**: 1人，全职4周
- **代码审查**: 1人，每周2小时
- **测试验证**: 1人，每周4小时

### 工具
- pytest-xdist (并行测试)
- pytest-cov (覆盖率)
- pytest-timeout (超时控制)
- pytest-mock (mock工具)

### 环境
- 独立的测试分支
- CI/CD 配置
- 测试数据库

---

## 参考资料

### 最佳实践
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

### 相关文档
- TEST_FIX_REPORT.md - 问题分析
- TEST_FIX_SUMMARY.md - 执行摘要
- TEST_OPTIMIZATION_REPORT.md - 初始报告

---

**创建时间**: 2026-02-27
**预计完成**: 2026-03-27 (1个月)
**优先级**: 中
**状态**: 待批准
