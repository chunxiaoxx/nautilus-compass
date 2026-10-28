# 工作流测试快速启动指南

## 快速开始（3步）

### 步骤 1: 启动 Nexus Server

打开第一个终端：

```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
python nexus_server.py
```

你应该看到：
```
Nexus Server 启动在 http://localhost:8001
```

### 步骤 2: 验证测试文件

打开第二个终端：

```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
python tests/verify_tests.py
```

确保所有检查通过。

### 步骤 3: 运行测试

```bash
# 运行所有测试
python tests/run_workflow_tests.py

# 或使用 pytest
pytest tests/test_workflow_integration.py -v
```

## 详细说明

### 环境准备

1. **检查 Python 版本**
   ```bash
   python --version  # 需要 Python 3.8+
   ```

2. **安装依赖**
   ```bash
   pip install pytest pytest-asyncio python-socketio aiohttp
   ```

3. **验证安装**
   ```bash
   python tests/verify_tests.py
   ```

### 运行选项

#### 选项 1: 使用快速运行脚本（推荐）

```bash
# 列出所有测试
python tests/run_workflow_tests.py --list

# 运行所有测试
python tests/run_workflow_tests.py

# 运行单个测试
python tests/run_workflow_tests.py --test 1

# 显示详细日志
python tests/run_workflow_tests.py --verbose

# 跳过服务器检查
python tests/run_workflow_tests.py --no-check
```

#### 选项 2: 使用 pytest

```bash
# 运行所有测试
pytest tests/test_workflow_integration.py -v

# 运行单个测试
pytest tests/test_workflow_integration.py::test_full_collaboration_workflow -v

# 显示详细输出
pytest tests/test_workflow_integration.py -v -s

# 只运行失败的测试
pytest tests/test_workflow_integration.py --lf
```

#### 选项 3: 直接运行 Python 文件

```bash
python tests/test_workflow_integration.py
```

### 测试列表

| 编号 | 测试名称 | 描述 | 预计时间 |
|------|---------|------|---------|
| 1 | 完整协作流程 | REQUEST → ACCEPT → PROGRESS → COMPLETE | 3-5秒 |
| 2 | 拒绝流程 | REQUEST → REJECT | 2-3秒 |
| 3 | 多次进度更新 | 10次进度更新 | 3-4秒 |
| 4 | 多智能体协作 | 3个智能体并行工作 | 4-6秒 |
| 5 | 智能体任务交接 | 任务在智能体间传递 | 5-8秒 |
| 6 | 知识分享流程 | SHARE 消息广播 | 2-3秒 |
| 7 | 选择性分享 | 定向知识分享 | 2-3秒 |
| 8 | 错误恢复流程 | 任务失败处理 | 3-4秒 |

**总计**: 约 1-2 分钟

### 预期输出示例

成功运行时的输出：

```
================================================================================
开始运行所有工作流集成测试
================================================================================

================================================================================
测试 1/8: 完整协作流程
================================================================================

✅ WorkflowAgentA 已连接并注册
✅ WorkflowAgentB 已连接并注册
📤 Agent A 发送 REQUEST 到 Agent B
📥 Agent B 收到 REQUEST: 处理数据集并生成报告
✅ Agent B 发送 ACCEPT
📥 Agent A 收到 ACCEPT
📊 Agent B 发送进度: 25%
📊 Agent A 收到进度更新: 25.0% - 开始处理任务
📊 Agent B 发送进度: 50%
📊 Agent A 收到进度更新: 50.0% - 任务进行中
📊 Agent B 发送进度: 75%
📊 Agent A 收到进度更新: 75.0% - 即将完成
✅ Agent B 发送 COMPLETE
📥 Agent A 收到 COMPLETE: success

✅ 测试 1 通过: 完整协作流程成功

[继续其他测试...]

================================================================================
测试总结
================================================================================
总计: 8 个测试
✅ 通过: 8
❌ 失败: 0
================================================================================
```

### 常见问题

#### Q1: 连接超时错误

**错误信息**: `TimeoutError: Connection timeout`

**解决方案**:
1. 确保 Nexus Server 正在运行
2. 检查端口 8001 是否被占用：
   ```bash
   netstat -ano | findstr :8001
   ```
3. 如果端口被占用，终止进程或更改端口

#### Q2: 模块导入错误

**错误信息**: `ModuleNotFoundError: No module named 'nexus_client'`

**解决方案**:
1. 检查路径设置
2. 确保 `agent-engine` 目录存在
3. 验证 `nexus_client.py` 文件存在

#### Q3: 测试卡住不动

**可能原因**:
- 消息未正确路由
- 事件处理器未注册
- 超时时间太短

**解决方案**:
1. 使用 `--verbose` 查看详细日志
2. 检查 Nexus Server 日志
3. 增加超时时间

#### Q4: 部分测试失败

**解决方案**:
1. 查看失败测试的详细日志
2. 单独运行失败的测试：
   ```bash
   python tests/run_workflow_tests.py --test <编号>
   ```
3. 检查测试状态和断言

### 调试技巧

1. **启用详细日志**
   ```bash
   python tests/run_workflow_tests.py --verbose
   ```

2. **使用 pytest 的调试选项**
   ```bash
   pytest tests/test_workflow_integration.py -v -s --tb=long
   ```

3. **查看 Nexus Server 日志**
   - Server 终端会显示所有消息路由信息

4. **添加断点**
   在测试代码中添加：
   ```python
   import pdb; pdb.set_trace()
   ```

5. **检查智能体状态**
   ```python
   print(f"Agent connected: {agent.is_connected()}")
   print(f"Agent registered: {agent.is_registered()}")
   print(f"Online agents: {agent.get_online_agents_list()}")
   ```

### 性能优化

如果测试运行缓慢：

1. **减少等待时间**
   - 调整 `asyncio.sleep()` 的时间
   - 减少超时时间

2. **并行运行测试**
   ```bash
   pytest tests/test_workflow_integration.py -n auto
   ```
   （需要安装 `pytest-xdist`）

3. **只运行特定测试**
   ```bash
   pytest tests/test_workflow_integration.py -k "collaboration"
   ```

### 持续集成

如果要在 CI/CD 中运行：

```yaml
# .github/workflows/test.yml 示例
name: Workflow Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio python-socketio aiohttp
      - name: Start Nexus Server
        run: |
          cd phase3/backend
          python nexus_server.py &
          sleep 5
      - name: Run tests
        run: |
          cd phase3/backend
          pytest tests/test_workflow_integration.py -v
```

### 下一步

测试通过后，你可以：

1. **扩展测试场景**
   - 添加更多边界情况
   - 测试错误处理
   - 测试性能极限

2. **集成到开发流程**
   - 添加到 pre-commit hook
   - 集成到 CI/CD 管道
   - 定期运行回归测试

3. **监控和分析**
   - 收集测试指标
   - 分析失败模式
   - 优化测试覆盖率

### 相关文档

- `README_WORKFLOW_TESTS.md` - 详细测试文档
- `test_workflow_integration.py` - 测试源代码
- `run_workflow_tests.py` - 快速运行脚本
- `verify_tests.py` - 验证脚本

### 获取帮助

如果遇到问题：

1. 查看详细文档：`README_WORKFLOW_TESTS.md`
2. 运行验证脚本：`python tests/verify_tests.py`
3. 查看测试日志
4. 联系开发团队

---

**版本**: 1.0.0
**更新时间**: 2026-02-25
**作者**: Nautilus Team
