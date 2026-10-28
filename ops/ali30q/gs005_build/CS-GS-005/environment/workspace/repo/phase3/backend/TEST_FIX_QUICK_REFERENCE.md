# 测试修复快速参考指南

## 🚀 快速开始

### 运行所有测试
```bash
cd /c/Users/chunx/Projects/nautilus-core/phase3/backend
python -m pytest tests/ -v
```

### 运行特定测试文件
```bash
python -m pytest tests/test_api_complete.py -v
```

### 获取测试统计
```bash
python -m pytest tests/ --tb=no -q
```

---

## 📋 当前状态

### ✅ 完全通过的模块 (100%)
- test_api.py
- test_api_complete.py ⭐ 新修复
- test_api_extended.py ⭐ 新修复
- test_coverage_boost.py
- test_database_models.py
- test_websocket.py
- test_workflow.py
- test_error_handling.py
- test_gas_fee_sharing.py

### 🟡 部分通过的模块 (>50%)
- test_stress.py (90%)
- test_blockchain_integration.py (73%)
- test_integration.py (67%)
- test_e2e_edge_cases.py (64%)
- test_e2e_agents_rewards.py (55%)

### 🔴 需要修复的模块 (<50%)
- test_e2e_auth.py (47%)
- test_e2e_api_keys.py (38%)
- test_gas_api.py (0%)
- test_e2e_tasks.py (0%)
- test_postgres_integration.py (0%)

---

## 🛠️ 修复模式

### 模式1: 数据库Fixture (推荐)

**适用于**: API端点测试

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models.database import Base
from utils.database import get_db

# 创建测试引擎
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# 在测试中使用
class TestExample:
    def test_endpoint(self, setup_database):
        from api.tasks import router

        app = FastAPI()
        app.include_router(router, prefix="/tasks")
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/tasks/")

        assert response.status_code == 200
```

---

### 模式2: Mock Web3 (区块链测试)

**适用于**: 区块链集成测试

```python
import pytest
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture
def mock_web3():
    """Mock Web3连接"""
    with patch('blockchain.web3_config.Web3') as mock_w3:
        # Mock连接
        mock_w3.return_value.is_connected.return_value = True

        # Mock账户
        mock_account = Mock()
        mock_account.address = "0x1234567890123456789012345678901234567890"
        mock_w3.return_value.eth.account.from_key.return_value = mock_account

        # Mock合约
        mock_contract = MagicMock()
        mock_contract.functions.publishTask.return_value.transact.return_value = "0xabc123"
        mock_w3.return_value.eth.contract.return_value = mock_contract

        yield mock_w3

class TestBlockchain:
    def test_publish_task(self, mock_web3):
        from blockchain.blockchain_service import BlockchainService

        service = BlockchainService()
        result = service.publish_task("task_001", 1000, 3600)

        assert result is not None
```

---

### 模式3: 认证Fixture

**适用于**: 需要认证的E2E测试

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def authenticated_client(client):
    """创建已认证的客户端"""
    # 注册用户
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
        "wallet_address": "0x1234567890123456789012345678901234567890"
    })

    # 提取token
    token = response.json()["access_token"]

    # 设置认证头
    client.headers = {"Authorization": f"Bearer {token}"}

    return client

class TestAuthenticatedEndpoints:
    def test_create_task(self, authenticated_client):
        response = authenticated_client.post("/api/tasks", json={
            "description": "Test task",
            "reward": 1000,
            "task_type": "CODE",
            "timeout": 3600
        })

        assert response.status_code == 201
```

---

## 🔧 常见问题修复

### 问题1: "no such table" 错误

**症状**:
```
sqlalchemy.exc.OperationalError: no such table: tasks
```

**原因**: 没有创建数据库表

**修复**:
```python
@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)  # 添加这行
    yield
    Base.metadata.drop_all(bind=engine)
```

---

### 问题2: "ConnectionError: Failed to connect to Sepolia"

**症状**:
```
ConnectionError: Failed to connect to Sepolia network
```

**原因**: 测试尝试连接真实网络

**修复**: 使用Mock或跳过测试
```python
@pytest.mark.skipif(
    not os.getenv("SEPOLIA_RPC_URL"),
    reason="Sepolia RPC URL not configured"
)
def test_real_blockchain():
    pass
```

---

### 问题3: "KeyError: 'access_token'"

**症状**:
```
KeyError: 'access_token'
```

**原因**: 注册/登录失败，没有返回token

**修复**: 检查响应状态码
```python
response = client.post("/api/auth/register", json={...})
assert response.status_code == 201, f"Registration failed: {response.json()}"
token = response.json()["access_token"]
```

---

### 问题4: "422 Unprocessable Entity"

**症状**:
```
HTTP/1.1 422 Unprocessable Entity
```

**原因**: 请求体格式不正确

**修复**: 检查Pydantic模型
```python
# 查看详细错误
response = client.post("/api/endpoint", json={...})
if response.status_code == 422:
    print(response.json())  # 查看验证错误详情
```

---

## 📊 测试命令速查

### 基本命令
```bash
# 运行所有测试
pytest tests/

# 详细输出
pytest tests/ -v

# 显示print输出
pytest tests/ -s

# 停在第一个失败
pytest tests/ -x

# 只运行失败的测试
pytest tests/ --lf

# 运行特定标记的测试
pytest tests/ -m "not slow"
```

### 调试命令
```bash
# 显示完整错误
pytest tests/ --tb=long

# 显示简短错误
pytest tests/ --tb=short

# 不显示错误详情
pytest tests/ --tb=no

# 进入调试器
pytest tests/ --pdb
```

### 覆盖率命令
```bash
# 生成覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 查看覆盖率
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 🎯 修复优先级

### 第1优先级 (立即修复)
1. ✅ test_api_complete.py - **已完成**
2. ✅ test_api_extended.py - **已完成**
3. 🔄 test_blockchain_integration.py - Mock Web3

### 第2优先级 (本周完成)
4. test_e2e_auth.py - 修复认证
5. test_e2e_tasks.py - 修复认证
6. test_e2e_agents_rewards.py - 修复认证

### 第3优先级 (下周完成)
7. test_gas_api.py - Mock Gas估算
8. test_e2e_api_keys.py - 修复API Key
9. test_e2e_edge_cases.py - 更新验证规则

---

## 📝 修复检查清单

### 开始修复前
- [ ] 阅读测试文件，理解测试意图
- [ ] 运行测试，查看具体错误
- [ ] 确定问题类型（数据库/Mock/认证/其他）
- [ ] 选择合适的修复模式

### 修复过程中
- [ ] 创建或使用合适的fixture
- [ ] 确保测试隔离（每个测试独立）
- [ ] 添加必要的Mock
- [ ] 验证修复有效

### 修复完成后
- [ ] 运行单个测试文件确认通过
- [ ] 运行所有测试确认没有破坏其他测试
- [ ] 更新文档
- [ ] 提交代码

---

## 🔗 相关文件

### 文档
- `TEST_FIX_REPORT.md` - 详细修复报告
- `TEST_FIX_SUMMARY.md` - 修复总结
- `README.md` - 项目说明

### 示例代码
- `tests/test_api_complete.py` - 数据库fixture示例
- `tests/test_e2e_auth.py` - 认证测试示例
- `tests/conftest.py` - 全局配置

### 工具脚本
- `fix_tests.py` - 测试修复工具
- `rebuild_test_db.py` - 重建测试数据库

---

## 💡 最佳实践

### DO ✅
- 使用内存数据库进行测试
- 使用dependency_overrides覆盖依赖
- 每个测试后清理数据
- Mock外部服务（区块链、API等）
- 使用有意义的测试名称
- 添加清晰的断言消息

### DON'T ❌
- 不要连接真实的外部服务
- 不要在测试间共享可变状态
- 不要使用sleep等待异步操作
- 不要忽略测试失败
- 不要写过于复杂的测试
- 不要跳过测试而不注明原因

---

## 📞 获取帮助

### 查看错误详情
```bash
pytest tests/test_file.py::TestClass::test_method -v --tb=long
```

### 查看测试覆盖的代码
```bash
pytest tests/ --cov=api --cov-report=term-missing
```

### 调试特定测试
```python
# 在测试中添加
import pdb; pdb.set_trace()

# 或使用pytest
pytest tests/test_file.py --pdb
```

---

**最后更新**: 2026-02-26 10:00:00
**维护者**: AI测试修复专家
