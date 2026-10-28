# Nexus Protocol 压力测试指南

本指南介绍如何运行Nexus Protocol的压力测试套件。

## 目录

- [快速开始](#快速开始)
- [测试场景](#测试场景)
- [运行测试](#运行测试)
- [配置选项](#配置选项)
- [结果分析](#结果分析)
- [故障排查](#故障排查)

---

## 快速开始

### 前置条件

1. Python 3.9+
2. 已安装所有依赖包
3. Nexus服务器运行在 `localhost:8001`

### 安装依赖

```bash
cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
pip install -r requirements.txt
```

### 启动服务器

```bash
# 在一个终端窗口启动服务器
python nexus_server.py
```

### 运行测试

```bash
# 在另一个终端窗口运行测试

# Windows
run_stress_tests.bat

# Linux/Mac
bash run_stress_tests.sh

# 或直接使用Python
python tests/run_stress_tests.py --level quick --test all --verbose
```

---

## 测试场景

### 1. 并发连接测试 (test_100_concurrent_agents)

**目标**: 验证服务器可以处理100个智能体同时连接

**测试内容**:
- 创建100个客户端
- 并发连接到服务器
- 验证注册成功
- 检查连接稳定性

**预期时间**: 2-3分钟

**成功标准**:
- 连接成功率 ≥95%
- 平均连接时间 <2秒
- 5秒后连接保持率 ≥95%

### 2. 消息吞吐量测试 (test_1000_messages_per_second)

**目标**: 验证系统可以处理高吞吐量消息

**测试内容**:
- 10个发送者，10个接收者
- 发送1000条消息
- 测量延迟和吞吐量

**预期时间**: 3-5分钟

**成功标准**:
- 消息接收率 ≥95%
- 吞吐量 ≥100条/秒
- 平均延迟 <1秒
- P95延迟 <2秒

### 3. 长时间运行测试 (test_long_running_stability)

**目标**: 验证系统长时间运行稳定性

**测试内容**:
- 20个智能体持续运行
- 每5秒发送消息
- 运行5分钟（快速版）或1小时（完整版）

**预期时间**: 5分钟 - 1小时

**成功标准**:
- 连接稳定率 ≥90%
- 消息接收率 ≥90%
- 无崩溃或异常

### 4. 内存泄漏检测 (test_memory_leak_detection)

**目标**: 检测内存泄漏

**测试内容**:
- 50次迭代
- 每次创建10个智能体
- 连接、发送消息、断开
- 监控内存使用

**预期时间**: 5-10分钟

**成功标准**:
- 内存增长 <50%
- 无明显内存泄漏

---

## 运行测试

### 方法1: 使用启动脚本（推荐）

**Windows**:
```bash
run_stress_tests.bat
```

**Linux/Mac**:
```bash
bash run_stress_tests.sh
```

脚本会引导你选择：
1. 测试级别（quick/standard/full）
2. 测试类型（all/concurrent/throughput/longrun/memory）

### 方法2: 使用Python脚本

```bash
# 运行所有测试（快速模式）
python tests/run_stress_tests.py --level quick --test all --verbose

# 运行单个测试
python tests/run_stress_tests.py --test concurrent --verbose
python tests/run_stress_tests.py --test throughput --verbose
python tests/run_stress_tests.py --test longrun --verbose
python tests/run_stress_tests.py --test memory --verbose

# 标准测试
python tests/run_stress_tests.py --level standard --test all --verbose

# 完整测试
python tests/run_stress_tests.py --level full --test all --verbose
```

### 方法3: 直接使用pytest

```bash
# 运行所有压力测试
python -m pytest tests/test_stress.py -v -s -m stress

# 运行单个测试
python -m pytest tests/test_stress.py::TestConcurrentAgents::test_100_concurrent_agents -v -s
python -m pytest tests/test_stress.py::TestMessageThroughput::test_1000_messages_per_second -v -s
python -m pytest tests/test_stress.py::TestLongRunning::test_long_running_stability -v -s
python -m pytest tests/test_stress.py::TestResourceMonitoring::test_memory_leak_detection -v -s

# 跳过慢速测试
python -m pytest tests/test_stress.py -v -s -m "stress and not slow"
```

---

## 配置选项

### 测试级别

- **quick**: 快速测试，适合开发阶段（5-10分钟）
- **standard**: 标准测试，适合CI/CD（20-30分钟）
- **full**: 完整测试，适合发布前验证（1-2小时）

### 测试类型

- **all**: 运行所有测试
- **concurrent**: 仅运行并发连接测试
- **throughput**: 仅运行消息吞吐量测试
- **longrun**: 仅运行长时间运行测试
- **memory**: 仅运行内存泄漏检测

### 环境变量

可以通过环境变量自定义测试配置：

```bash
# 设置服务器URL
export NEXUS_SERVER_URL="http://localhost:8001"

# 设置测试超时
export TEST_TIMEOUT=60

# 设置并发数量
export CONCURRENT_AGENTS=100

# 设置消息数量
export MESSAGE_COUNT=1000
```

---

## 结果分析

### 查看测试输出

测试运行时会实时输出：
- 测试进度
- 性能指标
- 错误信息

### 性能报告

测试完成后，更新 `PERFORMANCE_REPORT.md` 文件，包含：
- 详细的性能指标
- 瓶颈分析
- 优化建议

### 关键指标

**连接性能**:
- 平均连接时间
- 最大连接时间
- 连接成功率

**消息性能**:
- 吞吐量（条/秒）
- 平均延迟
- P95/P99延迟

**稳定性**:
- 连接保持率
- 消息接收率
- 错误率

**资源使用**:
- CPU使用率
- 内存使用
- 内存增长率

---

## 故障排查

### 问题1: 服务器连接失败

**症状**: `Connection refused` 或 `Connection timeout`

**解决方案**:
1. 确认服务器正在运行：`curl http://localhost:8001/health`
2. 检查端口是否被占用：`netstat -ano | findstr 8001`
3. 检查防火墙设置
4. 查看服务器日志：`nexus_server.log`

### 问题2: 测试超时

**症状**: `TimeoutError: Registration timeout`

**解决方案**:
1. 增加超时时间：修改 `TEST_TIMEOUT` 变量
2. 减少并发数量
3. 检查网络延迟
4. 检查服务器性能

### 问题3: 内存不足

**症状**: `MemoryError` 或系统变慢

**解决方案**:
1. 减少并发智能体数量
2. 减少消息数量
3. 增加系统内存
4. 分批运行测试

### 问题4: 依赖包缺失

**症状**: `ModuleNotFoundError`

**解决方案**:
```bash
pip install -r requirements.txt
```

### 问题5: psutil安装失败

**症状**: psutil安装错误（Windows）

**解决方案**:
1. 测试会自动跳过内存监控
2. 或手动安装：`pip install psutil`
3. 或使用预编译包

### 问题6: 测试失败率高

**症状**: 多个测试失败

**解决方案**:
1. 检查服务器日志
2. 降低测试强度
3. 检查网络稳定性
4. 重启服务器后重试

---

## 最佳实践

### 1. 测试前准备

- 关闭其他占用资源的程序
- 确保网络稳定
- 清理旧的日志文件
- 重启服务器

### 2. 测试执行

- 从quick级别开始
- 逐步增加测试强度
- 记录每次测试结果
- 对比不同版本性能

### 3. 结果记录

- 更新PERFORMANCE_REPORT.md
- 保存测试日志
- 截图关键指标
- 记录环境信息

### 4. 持续改进

- 定期运行压力测试
- 跟踪性能趋势
- 优化瓶颈点
- 更新测试用例

---

## 示例输出

### 成功的测试输出

```
======================================================================
测试场景1: 100个智能体并发连接
======================================================================

创建 100 个客户端...
✓ 已创建 100 个客户端

并发连接 100 个客户端...
  已连接: 10/100
  已连接: 20/100
  ...
  已连接: 100/100

✓ 连接完成:
  - 已连接: 100/100
  - 已注册: 100/100

等待5秒，验证服务器稳定性...
✓ 5秒后仍连接: 100/100

性能指标:
  - 总耗时: 15.23秒
  - 平均连接时间: 0.152秒
  - 最大连接时间: 0.845秒
  - 中位连接时间: 0.138秒
  - 错误数: 0

✅ 测试通过: 100个智能体并发连接成功
```

---

## 附录

### A. 测试文件结构

```
phase3/backend/
├── tests/
│   ├── test_stress.py              # 压力测试主文件
│   └── run_stress_tests.py         # 测试运行脚本
├── run_stress_tests.sh             # Linux/Mac启动脚本
├── run_stress_tests.bat            # Windows启动脚本
├── PERFORMANCE_REPORT.md           # 性能报告模板
├── STRESS_TEST_GUIDE.md            # 本指南
└── requirements.txt                # 依赖包列表
```

### B. 相关文档

- [Nexus Protocol规范](NEXUS_PROTOCOL_SPEC.md)
- [性能报告](PERFORMANCE_REPORT.md)
- [集成测试指南](tests/README.md)

### C. 联系方式

如有问题，请联系：
- 项目负责人: [待填写]
- 技术支持: [待填写]

---

**文档版本**: 1.0.0
**最后更新**: 2026-02-25
**维护者**: 压力测试专家
