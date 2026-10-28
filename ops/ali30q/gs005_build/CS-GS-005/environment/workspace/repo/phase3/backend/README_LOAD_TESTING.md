# Locust压力测试 - README

## 概述

本目录包含Nautilus Backend API的完整Locust压力测试方案。

## 快速开始

### 1. 安装依赖

```bash
pip install locust
```

### 2. 启动后端服务

```bash
python main.py
```

### 3. 运行测试

**最简单的方式**:
```bash
# Linux/Mac
./run_load_tests.sh light

# Windows
run_load_tests.bat light
```

## 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `locustfile.py` | 主测试脚本，包含所有测试场景 |
| `load_test_config.py` | 配置管理工具，预定义测试场景 |
| `run_load_tests.sh` | Linux/Mac快速启动脚本 |
| `run_load_tests.bat` | Windows快速启动脚本 |
| `compare_load_test_results.py` | 结果对比工具 |

### 文档文件

| 文件 | 说明 |
|------|------|
| `LOAD_TESTING_GUIDE.md` | 完整的测试指南 |
| `PERFORMANCE_BENCHMARKS.md` | 性能基准文档 |
| `LOAD_TESTING_REPORT.md` | 测试报告模板 |
| `LOAD_TESTING_QUICK_REF.md` | 快速参考 |
| `LOAD_TESTING_PROJECT_SUMMARY.md` | 项目总结 |
| `README_LOAD_TESTING.md` | 本文档 |

## 测试场景

| 场景 | 用户数 | 时长 | 用途 |
|------|--------|------|------|
| light | 10 | 5分钟 | 基本功能验证 |
| medium | 50 | 10分钟 | 日常负载测试 |
| heavy | 100 | 15分钟 | 高负载测试 |
| peak | 200 | 10分钟 | 峰值负载测试 |
| stress | 500 | 20分钟 | 压力测试 |
| spike | 300 | 5分钟 | 尖峰测试 |
| endurance | 30 | 60分钟 | 耐久测试 |

## 使用方法

### 方法1: 快速启动脚本（推荐）

```bash
# 运行轻负载测试
./run_load_tests.sh light

# 运行中负载测试
./run_load_tests.sh medium

# 使用Web界面
./run_load_tests.sh light --web

# 指定目标主机
./run_load_tests.sh medium --host http://staging.example.com
```

### 方法2: Python配置脚本

```bash
# 列出所有场景
python load_test_config.py list

# 运行测试
python load_test_config.py medium

# 指定环境
python load_test_config.py heavy staging
```

### 方法3: 直接使用Locust

```bash
# Web界面
locust -f locustfile.py --host=http://localhost:8000

# 无头模式
locust -f locustfile.py --host=http://localhost:8000 \
    --users 50 --spawn-rate 5 --run-time 10m --headless
```

## 查看结果

### 实时监控
- Web界面: http://localhost:8089
- 终端输出: 实时显示统计信息

### 测试报告
测试完成后，报告保存在 `results/` 目录:
- `load_test_*.html` - HTML可视化报告
- `load_test_*_stats.csv` - 详细统计数据
- `load_test_*_failures.csv` - 失败记录
- `load_test_*_exceptions.csv` - 异常记录

### 对比结果

```bash
python compare_load_test_results.py \
    results/test1_stats.csv \
    results/test2_stats.csv
```

## 测试的API端点

### 认证 (3个)
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

### 任务 (5个)
- GET /api/tasks
- POST /api/tasks
- GET /api/tasks/{id}
- POST /api/tasks/{id}/accept
- POST /api/tasks/{id}/submit

### Agent (3个)
- GET /api/agents
- POST /api/agents
- GET /api/agents/{id}

### 奖励 (3个)
- GET /api/rewards/balance
- GET /api/rewards/history
- POST /api/rewards/withdraw

**总计**: 14个关键端点

## 性能目标

### 响应时间
- 平均: < 300ms
- P95: < 1s
- P99: < 2s

### 吞吐量
- 轻负载: 10-20 RPS
- 中负载: 50-100 RPS
- 重负载: 100-200 RPS
- 峰值: 200-400 RPS

### 错误率
- 轻负载: < 0.1%
- 中负载: < 0.5%
- 重负载: < 1%
- 峰值: < 2%

## 常见问题

### Q: 如何安装Locust?
```bash
pip install locust
```

### Q: 如何检查后端服务是否运行?
```bash
curl http://localhost:8000/health
```

### Q: 测试报告保存在哪里?
报告保存在 `results/` 目录，文件名包含时间戳。

### Q: 如何停止正在运行的测试?
按 `Ctrl+C` 停止测试。

### Q: 可以在生产环境运行吗?
不建议。压力测试会产生大量负载，可能影响生产服务。

### Q: 如何自定义测试场景?
编辑 `locustfile.py` 添加新的任务，或使用 `custom` 场景。

## 故障排查

### 连接被拒绝
```bash
# 检查服务
curl http://localhost:8000/health

# 启动服务
python main.py
```

### 响应时间过长
- 检查数据库性能
- 查看系统资源使用
- 减少并发用户数

### 高错误率
- 查看日志: `tail -f logs/app.log`
- 检查数据库连接
- 验证测试数据

## 最佳实践

### 测试前
1. 清理测试数据库
2. 确保服务正常运行
3. 启动监控工具
4. 了解性能基准

### 测试中
1. 监控系统资源
2. 观察错误率
3. 记录异常情况

### 测试后
1. 保存测试报告
2. 分析性能数据
3. 记录发现的问题
4. 更新性能基准

## 进阶使用

### 分布式测试

```bash
# Master节点
locust -f locustfile.py --master --host=http://localhost:8000

# Worker节点
locust -f locustfile.py --worker --master-host=<master-ip>
```

### 自定义报告

```bash
locust -f locustfile.py --host=http://localhost:8000 \
    --users 100 --spawn-rate 10 --run-time 10m \
    --headless \
    --csv my_test \
    --html my_report.html
```

### 环境变量

```bash
export LOCUST_HOST=http://localhost:8000
export LOCUST_USERS=100
export LOCUST_SPAWN_RATE=10

locust -f locustfile.py
```

## 相关资源

### 项目文档
- [完整测试指南](LOAD_TESTING_GUIDE.md)
- [性能基准](PERFORMANCE_BENCHMARKS.md)
- [测试报告模板](LOAD_TESTING_REPORT.md)
- [快速参考](LOAD_TESTING_QUICK_REF.md)

### 外部资源
- [Locust官方文档](https://docs.locust.io/)
- [Locust GitHub](https://github.com/locustio/locust)

## 支持

如有问题或建议:
1. 查看文档目录中的详细指南
2. 检查Locust官方文档
3. 查看项目日志文件

## 更新日志

- **2026-02-26**: 初始版本
  - 创建完整的测试脚本
  - 添加7种预定义场景
  - 创建快速启动脚本
  - 编写完整文档

---

**版本**: 1.0
**最后更新**: 2026-02-26
**维护者**: Nautilus Team
