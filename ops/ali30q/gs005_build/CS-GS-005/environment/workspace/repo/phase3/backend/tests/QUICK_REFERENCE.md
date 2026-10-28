# Nexus Server 测试快速参考

## 快速开始

### 运行所有Nexus Server测试
```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
python -m pytest tests/test_nexus_server_integration.py tests/test_nexus_server_socketio.py -v
```

### 运行测试并生成覆盖率报告
```bash
python -m pytest tests/test_nexus_server_integration.py tests/test_nexus_server_socketio.py --cov=nexus_server --cov-report=html
```

## 测试文件

| 文件 | 测试数 | 描述 |
|------|--------|------|
| `test_nexus_server_integration.py` | 20 | 基础功能、消息路由、并发控制、错误处理、统计功能 |
| `test_nexus_server_socketio.py` | 18 | Socket.IO事件处理器测试 |
| **总计** | **38** | **完整的集成测试套件** |

## 测试覆盖率

- **初始**: 32%
- **当前**: 85%
- **提升**: +53%

## 测试分类

### 基础功能 (4个)
- 服务器启动/关闭
- 智能体注册/注销
- 多智能体管理

### 消息路由 (3个)
- 单播路由
- 广播路由
- 离线智能体处理

### 并发控制 (3个)
- 队列满处理
- 智能体数量限制
- 并发消息处理

### 错误处理 (3个)
- 无效消息格式
- 重复注册
- 消息过期

### Socket.IO事件 (18个)
- 连接管理 (connect/disconnect)
- 智能体注册 (hello)
- 消息处理 (message/request/accept/reject/progress/complete/share)
- 查询功能 (get_agents/get_stats)

### 统计功能 (2个)
- 获取统计信息
- 获取在线智能体

### 其他 (5个)
- 信息检索
- 统计跟踪
- FastAPI集成
- 自定义配置
- 消息验证

## 常用命令

### 运行特定测试
```bash
# 运行单个测试
pytest tests/test_nexus_server_integration.py::test_agent_registration -v

# 运行某个文件的所有测试
pytest tests/test_nexus_server_integration.py -v

# 运行匹配模式的测试
pytest tests/ -k "agent" -v
```

### 查看测试列表
```bash
pytest tests/test_nexus_server_integration.py tests/test_nexus_server_socketio.py --collect-only
```

### 生成详细报告
```bash
# HTML覆盖率报告
pytest tests/test_nexus_server_*.py --cov=nexus_server --cov-report=html

# 终端覆盖率报告
pytest tests/test_nexus_server_*.py --cov=nexus_server --cov-report=term-missing

# 同时生成两种报告
pytest tests/test_nexus_server_*.py --cov=nexus_server --cov-report=html --cov-report=term-missing
```

### 调试测试
```bash
# 显示print输出
pytest tests/test_nexus_server_integration.py -v -s

# 在第一个失败时停止
pytest tests/test_nexus_server_integration.py -x

# 显示详细的错误信息
pytest tests/test_nexus_server_integration.py -v --tb=long
```

## 测试结果

```
============================= test session starts =============================
collected 38 items

tests\test_nexus_server_integration.py ....................              [ 52%]
tests\test_nexus_server_socketio.py ..................                   [100%]

============================== tests coverage ================================
Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
nexus_server.py     179     27    85%
-----------------------------------------------
TOTAL               179     27    85%

======================= 38 passed, 15 warnings in 2.48s =======================
```

## 文件位置

- **测试文件**: `C:\Users\chunx\Projects\nautilus-core\phase3\backend\tests\`
  - `test_nexus_server_integration.py` (901行)
  - `test_nexus_server_socketio.py` (736行)
- **被测文件**: `C:\Users\chunx\Projects\nautilus-core\phase3\backend\nexus_server.py`
- **覆盖率报告**: `C:\Users\chunx\Projects\nautilus-core\phase3\backend\htmlcov\index.html`
- **测试总结**: `C:\Users\chunx\Projects\nautilus-core\phase3\backend\tests\NEXUS_SERVER_TEST_SUMMARY.md`

## 依赖项

```
pytest>=9.0.2
pytest-asyncio>=1.3.0
pytest-cov>=7.0.0
python-socketio
pydantic
```

## 注意事项

1. 测试使用异步函数，需要 `pytest-asyncio` 插件
2. 所有测试都是独立的，不依赖外部服务
3. 测试使用模拟数据，不会影响实际数据库
4. 某些测试会产生 DeprecationWarning（使用 datetime.utcnow()），这是预期的

## 持续集成

建议在CI/CD流程中添加：

```yaml
# 示例 GitHub Actions
- name: Run Nexus Server Tests
  run: |
    cd phase3/backend
    pytest tests/test_nexus_server_*.py --cov=nexus_server --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

---

**最后更新**: 2025-02-25
**维护者**: Development Team
