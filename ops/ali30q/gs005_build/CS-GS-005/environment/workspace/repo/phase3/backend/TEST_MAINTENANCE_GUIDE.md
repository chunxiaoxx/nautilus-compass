# 测试维护指南

**版本**: 1.0
**更新日期**: 2026-02-26
**适用项目**: Nautilus Core Phase 3 Backend

---

## 目录

1. [测试架构概述](#测试架构概述)
2. [如何编写好的测试](#如何编写好的测试)
3. [如何调试失败的测试](#如何调试失败的测试)
4. [测试最佳实践](#测试最佳实践)
5. [常见问题和解决方案](#常见问题和解决方案)
6. [测试工具和命令](#测试工具和命令)

---

## 测试架构概述

### 测试目录结构

```
tests/
├── conftest.py                    # 全局 fixtures
├── test_api.py                    # API 基础测试
├── test_api_complete.py           # API 完整测试
├── test_api_extended.py           # API 扩展测试
├── test_blockchain_integration.py # 区块链集成测试
├── test_coverage_boost.py         # 覆盖率提升测试
├── test_database_models.py        # 数据库模型测试
├── test_e2e_*.py                  # 端到端测试
├── test_gas_api.py                # Gas API 测试
├── test_performance.py            # 性能测试
├── test_stress.py                 # 压力测试
└── ...
```

### 测试类型

1. **单元测试**: 测试单个函数或类
2. **集成测试**: 测试多个组件的交互
3. **E2E 测试**: 测试完整的用户流程
4. **性能测试**: 测试系统性能指标
5. **压力测试**: 测试系统在高负载下的表现

### 测试框架

- **pytest**: 主测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 代码覆盖率
- **FastAPI TestClient**: API 测试客户端

---

## 如何编写好的测试

### 1. 测试命名规范

```python
# ✅ 好的命名
def test_user_registration_with_valid_data():
    """测试使用有效数据注册用户"""
    pass

def test_user_registration_with_duplicate_email():
    """测试使用重复邮箱注册用户"""
    pass

# ❌ 不好的命名
def test_1():
    pass

def test_user():
    pass
```

**规则**:
- 使用 `test_` 前缀
- 描述测试的具体场景
- 使用下划线分隔单词
- 包含被测试的功能和条件

### 2. 测试结构 (AAA 模式)

```python
def test_create_task_success(client, auth_token):
    """测试成功创建任务"""

    # Arrange (准备)
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "reward": 1000000000000000000,
        "deadline": "2025-12-31T23:59:59"
    }

    # Act (执行)
    response = client.post(
        "/api/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    # Assert (断言)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == task_data["title"]
    assert "task_id" in data
```

### 3. 使用 Fixtures

```python
# conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()

    # 创建表
    Base.metadata.create_all(engine)

    yield session

    # 清理
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    return user
```

### 4. 测试数据管理

```python
# ✅ 好的做法：使用工厂函数
def create_test_user(username="testuser", email="test@example.com"):
    """创建测试用户的工厂函数"""
    return User(
        username=username,
        email=email,
        hashed_password="hashed_password",
        wallet_address=f"0x{username}{'0'*36}"
    )

def test_multiple_users(db_session):
    user1 = create_test_user("user1", "user1@example.com")
    user2 = create_test_user("user2", "user2@example.com")
    db_session.add_all([user1, user2])
    db_session.commit()

# ❌ 不好的做法：硬编码测试数据
def test_user_creation(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password",
        wallet_address="0x1234567890123456789012345678901234567890"
    )
    db_session.add(user)
    db_session.commit()
```

### 5. 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """测试异步操作"""
    result = await some_async_function()
    assert result is not None

@pytest.mark.asyncio
async def test_websocket_connection(client):
    """测试 WebSocket 连接"""
    async with client.websocket_connect("/ws") as websocket:
        await websocket.send_json({"type": "ping"})
        data = await websocket.receive_json()
        assert data["type"] == "pong"
```

### 6. 参数化测试

```python
import pytest

@pytest.mark.parametrize("username,email,expected_status", [
    ("user1", "user1@example.com", 201),
    ("", "user2@example.com", 422),  # 空用户名
    ("user3", "", 422),  # 空邮箱
    ("user4", "invalid-email", 422),  # 无效邮箱
])
def test_user_registration_validation(client, username, email, expected_status):
    """测试用户注册验证"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "password123",
            "wallet_address": "0x1234567890123456789012345678901234567890"
        }
    )
    assert response.status_code == expected_status
```

---

## 如何调试失败的测试

### 1. 查看详细错误信息

```bash
# 显示完整的错误堆栈
pytest tests/test_api.py -v --tb=long

# 显示简短的错误信息
pytest tests/test_api.py -v --tb=short

# 只显示一行错误
pytest tests/test_api.py -v --tb=line

# 不显示错误堆栈
pytest tests/test_api.py -v --tb=no
```

### 2. 运行单个测试

```bash
# 运行单个测试文件
pytest tests/test_api.py -v

# 运行单个测试类
pytest tests/test_api.py::TestModels -v

# 运行单个测试函数
pytest tests/test_api.py::TestModels::test_task_status_enum -v
```

### 3. 使用 print 调试

```python
def test_create_task(client, auth_token):
    task_data = {"title": "Test Task"}

    print(f"\n发送数据: {task_data}")
    response = client.post("/api/tasks", json=task_data)
    print(f"响应状态: {response.status_code}")
    print(f"响应数据: {response.json()}")

    assert response.status_code == 201
```

运行时使用 `-s` 标志查看 print 输出：
```bash
pytest tests/test_api.py::test_create_task -v -s
```

### 4. 使用 pytest 的调试器

```python
def test_complex_logic():
    result = complex_function()

    # 在这里暂停并进入调试器
    import pdb; pdb.set_trace()

    assert result == expected_value
```

或使用 pytest 的内置调试器：
```bash
pytest tests/test_api.py --pdb
```

### 5. 查看日志

```bash
# 显示所有日志
pytest tests/test_api.py -v --log-cli-level=DEBUG

# 只显示错误日志
pytest tests/test_api.py -v --log-cli-level=ERROR
```

### 6. 检查测试隔离

```bash
# 运行测试两次，检查是否有状态污染
pytest tests/test_api.py -v --count=2

# 随机顺序运行测试
pytest tests/test_api.py -v --random-order
```

### 7. 常见失败原因检查清单

- [ ] 数据库状态是否正确清理？
- [ ] Fixture 是否正确设置和清理？
- [ ] 测试是否依赖于其他测试的执行顺序？
- [ ] 异步操作是否正确等待？
- [ ] Mock 对象是否正确配置？
- [ ] 测试数据是否唯一（避免冲突）？
- [ ] 环境变量是否正确设置？

---

## 测试最佳实践

### 1. 测试隔离

**原则**: 每个测试应该独立运行，不依赖其他测试

```python
# ✅ 好的做法
@pytest.fixture
def clean_database():
    """每个测试前清理数据库"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

def test_user_creation(clean_database):
    # 测试在干净的数据库上运行
    pass

# ❌ 不好的做法
def test_create_user():
    user = create_user("test")
    # 没有清理，影响后续测试

def test_list_users():
    # 依赖于上一个测试创建的用户
    users = list_users()
    assert len(users) == 1  # 可能失败
```

### 2. 使用 Mock 对象

```python
from unittest.mock import Mock, patch

def test_blockchain_integration_with_mock():
    """使用 Mock 测试区块链集成"""

    # Mock 区块链客户端
    with patch('blockchain.web3_client.Web3') as mock_web3:
        mock_web3.eth.get_balance.return_value = 1000000000000000000

        balance = get_user_balance("0x1234...")
        assert balance == 1000000000000000000
        mock_web3.eth.get_balance.assert_called_once()
```

### 3. 测试边界条件

```python
def test_reward_validation():
    """测试奖励验证的边界条件"""

    # 测试零值
    assert validate_reward(0) == False

    # 测试负值
    assert validate_reward(-1) == False

    # 测试最小有效值
    assert validate_reward(1) == True

    # 测试最大值
    assert validate_reward(10**30) == True

    # 测试超大值
    assert validate_reward(10**50) == False
```

### 4. 测试错误处理

```python
def test_error_handling():
    """测试错误处理"""

    # 测试预期的异常
    with pytest.raises(ValueError):
        invalid_operation()

    # 测试异常消息
    with pytest.raises(ValueError, match="Invalid input"):
        invalid_operation()

    # 测试 HTTP 错误
    response = client.post("/api/invalid")
    assert response.status_code == 404
```

### 5. 性能测试

```python
import time

def test_api_performance():
    """测试 API 性能"""

    start_time = time.time()
    response = client.get("/api/tasks?limit=100")
    end_time = time.time()

    duration = end_time - start_time

    assert response.status_code == 200
    assert duration < 1.0  # 应该在 1 秒内完成
```

### 6. 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest tests/ --cov=. --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html
```

### 7. 持续集成

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.13
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/ -v --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 常见问题和解决方案

### 问题 1: 测试在单独运行时通过，但在套件中失败

**原因**: 测试隔离不足，存在状态污染

**解决方案**:
```python
# 使用 autouse fixture 确保每个测试前清理
@pytest.fixture(autouse=True)
def reset_database():
    """每个测试前重置数据库"""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
```

### 问题 2: 数据库表不存在错误

**原因**: 数据库未正确初始化

**解决方案**:
```python
@pytest.fixture(scope="session")
def setup_database():
    """会话级别的数据库设置"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(setup_database):
    """使用已设置的数据库"""
    session = Session()
    yield session
    session.rollback()
    session.close()
```

### 问题 3: 异步测试超时

**原因**: 异步操作未正确等待

**解决方案**:
```python
@pytest.mark.asyncio
@pytest.mark.timeout(10)  # 设置超时
async def test_async_operation():
    result = await asyncio.wait_for(
        some_async_function(),
        timeout=5.0
    )
    assert result is not None
```

### 问题 4: Mock 对象未生效

**原因**: Mock 的路径不正确

**解决方案**:
```python
# ❌ 错误：Mock 导入的位置
with patch('original_module.function') as mock_func:
    pass

# ✅ 正确：Mock 使用的位置
with patch('my_module.function') as mock_func:
    pass
```

### 问题 5: 测试数据冲突

**原因**: 使用了相同的测试数据

**解决方案**:
```python
import uuid

def create_unique_user():
    """创建唯一的测试用户"""
    unique_id = str(uuid.uuid4())[:8]
    return User(
        username=f"user_{unique_id}",
        email=f"user_{unique_id}@example.com",
        wallet_address=f"0x{unique_id}{'0'*32}"
    )
```

### 问题 6: 并发测试失败

**原因**: TestClient 不是线程安全的

**解决方案**:
```python
# 使用异步并发而不是线程
@pytest.mark.asyncio
async def test_concurrent_requests():
    async with httpx.AsyncClient(app=app) as client:
        tasks = [
            client.get("/api/tasks")
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)
        assert all(r.status_code == 200 for r in responses)
```

### 问题 7: 性能测试不稳定

**原因**: 性能阈值过严或环境差异

**解决方案**:
```python
def test_performance_with_tolerance():
    """使用容差的性能测试"""
    durations = []

    # 运行多次取平均值
    for _ in range(5):
        start = time.time()
        response = client.get("/api/tasks")
        durations.append(time.time() - start)

    avg_duration = sum(durations) / len(durations)

    # 使用更宽松的阈值
    assert avg_duration < 2.0  # 而不是 0.5
```

---

## 测试工具和命令

### 基本命令

```bash
# 运行所有测试
pytest tests/

# 运行特定文件
pytest tests/test_api.py

# 运行特定测试
pytest tests/test_api.py::test_function_name

# 详细输出
pytest tests/ -v

# 显示 print 输出
pytest tests/ -s

# 停在第一个失败
pytest tests/ -x

# 显示最慢的 10 个测试
pytest tests/ --durations=10
```

### 覆盖率命令

```bash
# 生成覆盖率报告
pytest tests/ --cov=.

# 生成 HTML 报告
pytest tests/ --cov=. --cov-report=html

# 只显示未覆盖的行
pytest tests/ --cov=. --cov-report=term-missing
```

### 调试命令

```bash
# 进入调试器
pytest tests/ --pdb

# 在失败时进入调试器
pytest tests/ --pdb --maxfail=1

# 显示详细日志
pytest tests/ --log-cli-level=DEBUG
```

### 过滤命令

```bash
# 运行标记的测试
pytest tests/ -m "slow"

# 排除标记的测试
pytest tests/ -m "not slow"

# 按名称过滤
pytest tests/ -k "test_user"

# 排除某些测试
pytest tests/ -k "not test_slow"
```

### 并行运行

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 使用多个 CPU 核心
pytest tests/ -n auto

# 使用指定数量的核心
pytest tests/ -n 4
```

### 重试失败的测试

```bash
# 安装 pytest-rerunfailures
pip install pytest-rerunfailures

# 重试失败的测试 3 次
pytest tests/ --reruns 3

# 重试时延迟 1 秒
pytest tests/ --reruns 3 --reruns-delay 1
```

---

## 测试检查清单

### 编写新测试时

- [ ] 测试名称清晰描述测试场景
- [ ] 使用 AAA 模式组织测试
- [ ] 测试是独立的，不依赖其他测试
- [ ] 使用适当的 fixtures
- [ ] 包含正面和负面测试用例
- [ ] 测试边界条件
- [ ] 添加适当的文档字符串
- [ ] 测试通过且稳定

### 修复失败的测试时

- [ ] 理解测试的目的
- [ ] 重现失败场景
- [ ] 检查测试隔离
- [ ] 检查数据库状态
- [ ] 检查 Mock 配置
- [ ] 验证修复不影响其他测试
- [ ] 添加注释说明修复原因

### 代码审查时

- [ ] 测试覆盖了新功能
- [ ] 测试是可维护的
- [ ] 测试执行速度合理
- [ ] 没有重复的测试代码
- [ ] 使用了适当的断言
- [ ] 错误消息清晰有用

---

## 参考资源

### 官方文档
- [pytest 文档](https://docs.pytest.org/)
- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)

### 推荐阅读
- "Test Driven Development" by Kent Beck
- "Growing Object-Oriented Software, Guided by Tests" by Steve Freeman
- "The Art of Unit Testing" by Roy Osherove

### 内部资源
- 测试优化报告: `TEST_OPTIMIZATION_REPORT.md`
- 项目 README: `README.md`
- API 文档: `docs/api.md`

---

**维护者**: Nautilus Core Team
**最后更新**: 2026-02-26
**版本**: 1.0
