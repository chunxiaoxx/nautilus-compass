# 测试运行指南

本指南说明如何运行新增的测试并验证覆盖率提升。

---

## 快速开始

### Windows用户

```bash
# 运行验证脚本
run_new_tests.bat
```

### Linux/Mac用户

```bash
# 添加执行权限
chmod +x run_new_tests.sh

# 运行验证脚本
./run_new_tests.sh
```

---

## 手动运行测试

### 1. 运行单个测试文件

```bash
# 认证API测试
pytest tests/test_api_auth_extended.py -v

# 奖励API测试
pytest tests/test_api_rewards_extended.py -v

# 任务API测试
pytest tests/test_api_tasks_extended.py -v

# 区块链服务Mock测试
pytest tests/test_blockchain_service_mock.py -v
```

### 2. 运行所有新增测试

```bash
pytest tests/test_api_auth_extended.py \
       tests/test_api_rewards_extended.py \
       tests/test_api_tasks_extended.py \
       tests/test_blockchain_service_mock.py -v
```

### 3. 运行特定测试类

```bash
# 运行密码验证测试
pytest tests/test_api_auth_extended.py::TestPasswordValidation -v

# 运行余额测试
pytest tests/test_api_rewards_extended.py::TestGetBalance -v

# 运行任务创建测试
pytest tests/test_api_tasks_extended.py::TestCreateTask -v
```

### 4. 运行特定测试方法

```bash
# 运行单个测试方法
pytest tests/test_api_auth_extended.py::TestPasswordValidation::test_password_too_short -v
```

---

## 生成覆盖率报告

### 1. 生成HTML报告

```bash
pytest tests/test_api_auth_extended.py \
       tests/test_api_rewards_extended.py \
       tests/test_api_tasks_extended.py \
       tests/test_blockchain_service_mock.py \
       --cov=api --cov=blockchain \
       --cov-report=html \
       --cov-report=term-missing
```

查看报告：
- Windows: `start htmlcov/index.html`
- Mac: `open htmlcov/index.html`
- Linux: `xdg-open htmlcov/index.html`

### 2. 生成终端报告

```bash
pytest tests/test_api_auth_extended.py \
       tests/test_api_rewards_extended.py \
       tests/test_api_tasks_extended.py \
       tests/test_blockchain_service_mock.py \
       --cov=api --cov=blockchain \
       --cov-report=term-missing
```

### 3. 生成XML报告（用于CI/CD）

```bash
pytest tests/test_api_auth_extended.py \
       tests/test_api_rewards_extended.py \
       tests/test_api_tasks_extended.py \
       tests/test_blockchain_service_mock.py \
       --cov=api --cov=blockchain \
       --cov-report=xml
```

---

## 运行所有测试

### 1. 运行所有测试（包括新旧测试）

```bash
pytest
```

### 2. 运行所有测试并生成覆盖率

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

### 3. 排除慢速测试

```bash
pytest -m "not slow"
```

### 4. 只运行特定标记的测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration
```

---

## 调试测试

### 1. 显示详细输出

```bash
pytest tests/test_api_auth_extended.py -vv
```

### 2. 显示print输出

```bash
pytest tests/test_api_auth_extended.py -s
```

### 3. 在第一个失败时停止

```bash
pytest tests/test_api_auth_extended.py -x
```

### 4. 显示完整的traceback

```bash
pytest tests/test_api_auth_extended.py --tb=long
```

### 5. 只运行失败的测试

```bash
# 第一次运行
pytest tests/test_api_auth_extended.py

# 只重新运行失败的测试
pytest --lf
```

### 6. 使用pdb调试

```bash
pytest tests/test_api_auth_extended.py --pdb
```

---

## 性能分析

### 1. 显示最慢的10个测试

```bash
pytest tests/test_api_auth_extended.py --durations=10
```

### 2. 并行运行测试（需要pytest-xdist）

```bash
# 安装
pip install pytest-xdist

# 使用所有CPU核心
pytest -n auto

# 使用指定数量的进程
pytest -n 4
```

---

## 持续集成配置

### GitHub Actions示例

```yaml
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
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term-missing

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## 常见问题

### Q1: 测试失败：JWT_SECRET未设置

**问题**: `ValueError: JWT_SECRET environment variable is required`

**解决方案**:
- 确保 `tests/conftest.py` 中已设置环境变量
- 或创建 `.env` 文件并设置 `JWT_SECRET`

### Q2: 测试失败：数据库连接错误

**问题**: `sqlalchemy.exc.OperationalError`

**解决方案**:
- 测试使用内存SQLite数据库，不需要外部数据库
- 检查 `conftest.py` 中的数据库配置

### Q3: 测试失败：区块链连接错误

**问题**: `Failed to connect to Sepolia network`

**解决方案**:
- 新增的mock测试不需要真实区块链连接
- 确保运行的是 `test_blockchain_service_mock.py` 而不是 `test_blockchain_integration.py`

### Q4: 覆盖率报告不准确

**问题**: 覆盖率显示为0%或异常低

**解决方案**:
```bash
# 清除旧的覆盖率数据
rm -rf .coverage htmlcov/

# 重新运行测试
pytest --cov=. --cov-report=html
```

### Q5: 测试运行很慢

**解决方案**:
```bash
# 使用并行测试
pip install pytest-xdist
pytest -n auto

# 或只运行快速测试
pytest -m "not slow"
```

---

## 测试最佳实践

### 1. 编写测试前

- 阅读现有测试了解模式
- 确保理解要测试的功能
- 考虑边界条件和错误情况

### 2. 编写测试时

- 使用描述性的测试名称
- 每个测试只测试一个功能点
- 使用fixture管理测试数据
- 添加必要的注释

### 3. 测试命名规范

```python
def test_<功能>_<场景>_<预期结果>():
    """测试描述"""
    pass

# 示例
def test_create_task_with_negative_reward_raises_error():
    """测试创建负数奖励的任务会抛出错误"""
    pass
```

### 4. 使用fixture

```python
@pytest.fixture
def test_user():
    """创建测试用户"""
    # 设置
    user = create_user()
    yield user
    # 清理
    delete_user(user)
```

### 5. 使用参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("valid@email.com", True),
    ("invalid", False),
    ("@example.com", False),
])
def test_email_validation(input, expected):
    assert validate_email(input) == expected
```

---

## 覆盖率目标

### 当前状态
- 总体覆盖率: 28%
- API模块: 63%
- 区块链模块: 32%

### 短期目标（新增测试后）
- 总体覆盖率: 50%+
- API模块: 85%+
- 区块链模块: 60%+

### 最终目标
- 总体覆盖率: 98%+
- 所有关键模块: 90%+

---

## 下一步

1. **运行新增测试**
   ```bash
   ./run_new_tests.sh  # 或 run_new_tests.bat
   ```

2. **查看覆盖率报告**
   ```bash
   open htmlcov/index.html
   ```

3. **修复失败的测试**
   - 查看错误信息
   - 调整测试或修复代码
   - 重新运行测试

4. **继续添加测试**
   - 参考 `TEST_COVERAGE_IMPROVEMENT_REPORT.md`
   - 按优先级添加缺失的测试
   - 持续提升覆盖率

---

## 资源链接

- [Pytest文档](https://docs.pytest.org/)
- [Coverage.py文档](https://coverage.readthedocs.io/)
- [测试覆盖率提升报告](./TEST_COVERAGE_IMPROVEMENT_REPORT.md)
- [工作总结](./TEST_COVERAGE_WORK_SUMMARY.md)

---

**最后更新**: 2026-02-27
