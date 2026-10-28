# Locust压力测试指南

## 目录
- [简介](#简介)
- [安装Locust](#安装locust)
- [快速开始](#快速开始)
- [测试场景](#测试场景)
- [运行测试](#运行测试)
- [分析结果](#分析结果)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)

## 简介

本指南介绍如何使用Locust对Nautilus Backend API进行压力测试。Locust是一个开源的负载测试工具，使用Python编写，易于使用和扩展。

### 测试目标

- 验证API在不同负载下的性能表现
- 识别系统瓶颈和性能问题
- 确保系统满足性能基准要求
- 测试系统在极端负载下的稳定性

## 安装Locust

### 方法1: 使用pip安装

```bash
pip install locust
```

### 方法2: 使用requirements.txt

在项目根目录添加到requirements.txt:

```bash
echo "locust>=2.15.0" >> requirements.txt
pip install -r requirements.txt
```

### 验证安装

```bash
locust --version
```

应该显示类似: `locust 2.15.0`

## 快速开始

### 1. 启动后端服务

确保Nautilus Backend正在运行:

```bash
# 开发环境
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 运行简单测试

```bash
# 使用Web界面
locust -f locustfile.py --host=http://localhost:8000

# 然后访问 http://localhost:8089
```

### 3. 使用配置脚本

```bash
# 轻负载测试（10用户）
python load_test_config.py light

# 中负载测试（50用户）
python load_test_config.py medium

# 重负载测试（100用户）
python load_test_config.py heavy

# 峰值负载测试（200用户）
python load_test_config.py peak
```

## 测试场景

### 场景1: 轻负载 (Light)
- **用户数**: 10
- **启动速率**: 2用户/秒
- **运行时间**: 5分钟
- **适用场景**: 开发环境、功能验证

```bash
python load_test_config.py light
```

### 场景2: 中负载 (Medium)
- **用户数**: 50
- **启动速率**: 5用户/秒
- **运行时间**: 10分钟
- **适用场景**: 测试环境、日常负载

```bash
python load_test_config.py medium
```

### 场景3: 重负载 (Heavy)
- **用户数**: 100
- **启动速率**: 10用户/秒
- **运行时间**: 15分钟
- **适用场景**: 高峰期负载测试

```bash
python load_test_config.py heavy
```

### 场景4: 峰值负载 (Peak)
- **用户数**: 200
- **启动速率**: 20用户/秒
- **运行时间**: 10分钟
- **适用场景**: 极端峰值测试

```bash
python load_test_config.py peak
```

### 场景5: 压力测试 (Stress)
- **用户数**: 500
- **启动速率**: 50用户/秒
- **运行时间**: 20分钟
- **适用场景**: 找出系统崩溃点

```bash
python load_test_config.py stress
```

### 场景6: 尖峰测试 (Spike)
- **用户数**: 300
- **启动速率**: 100用户/秒
- **运行时间**: 5分钟
- **适用场景**: 测试系统弹性

```bash
python load_test_config.py spike
```

### 场景7: 耐久测试 (Endurance)
- **用户数**: 30
- **启动速率**: 3用户/秒
- **运行时间**: 60分钟
- **适用场景**: 内存泄漏检测

```bash
python load_test_config.py endurance
```

## 运行测试

### 命令行模式（无头模式）

```bash
# 基本用法
locust -f locustfile.py --host=http://localhost:8000 \
    --users 50 --spawn-rate 5 --run-time 10m --headless

# 生成CSV报告
locust -f locustfile.py --host=http://localhost:8000 \
    --users 50 --spawn-rate 5 --run-time 10m --headless \
    --csv=results/test_results

# 生成HTML报告
locust -f locustfile.py --host=http://localhost:8000 \
    --users 50 --spawn-rate 5 --run-time 10m --headless \
    --html=results/test_report.html
```

### Web界面模式

```bash
# 启动Web界面
locust -f locustfile.py --host=http://localhost:8000

# 自定义Web端口
locust -f locustfile.py --host=http://localhost:8000 \
    --web-host=0.0.0.0 --web-port=8089
```

然后访问: http://localhost:8089

### 使用配置脚本

```bash
# 列出所有场景
python load_test_config.py list

# 列出所有环境
python load_test_config.py environments

# 运行特定场景和环境
python load_test_config.py medium staging

# 使用Web界面
python load_test_config.py light local --no-headless

# 自定义CSV输出
python load_test_config.py heavy local --csv my_test_results
```

## 分析结果

### 关键指标

#### 1. 响应时间 (Response Time)
- **平均响应时间**: 应该 < 500ms
- **中位数响应时间**: 应该 < 300ms
- **95百分位**: 应该 < 1s
- **99百分位**: 应该 < 2s

#### 2. 吞吐量 (Throughput)
- **RPS (Requests Per Second)**: 每秒请求数
- **目标**:
  - 轻负载: 10-20 RPS
  - 中负载: 50-100 RPS
  - 重负载: 100-200 RPS
  - 峰值: 200-400 RPS

#### 3. 错误率 (Error Rate)
- **目标**: < 1%
- **可接受**: < 5%
- **不可接受**: > 10%

#### 4. 并发用户数 (Concurrent Users)
- 系统应该能够支持的同时在线用户数

### 查看实时统计

在Web界面中，可以看到:
- 实时请求统计
- 响应时间分布图
- 错误统计
- 每个端点的性能指标

### 分析CSV报告

测试完成后会生成以下CSV文件:

```
test_results_stats.csv          # 统计数据
test_results_stats_history.csv  # 历史数据
test_results_failures.csv       # 失败记录
test_results_exceptions.csv     # 异常记录
```

### 分析HTML报告

HTML报告包含:
- 总体统计信息
- 响应时间图表
- 请求分布
- 失败详情

## 最佳实践

### 1. 测试前准备

```bash
# 清理数据库
python rebuild_test_db.py

# 确保服务正常运行
curl http://localhost:8000/health

# 检查系统资源
htop  # 或 top
```

### 2. 逐步增加负载

不要一开始就运行最大负载，应该逐步增加:

```bash
# 第1步: 轻负载
python load_test_config.py light

# 第2步: 中负载
python load_test_config.py medium

# 第3步: 重负载
python load_test_config.py heavy

# 第4步: 峰值负载
python load_test_config.py peak
```

### 3. 监控系统资源

在测试期间监控:
- CPU使用率
- 内存使用率
- 磁盘I/O
- 网络带宽
- 数据库连接数

```bash
# 使用监控脚本
python monitoring/verify_monitoring_setup.py

# 查看日志
tail -f logs/app.log
```

### 4. 记录测试结果

为每次测试创建记录:
- 测试日期和时间
- 测试场景
- 系统配置
- 测试结果
- 发现的问题

### 5. 测试不同场景

- **正常流量**: 模拟日常使用
- **峰值流量**: 模拟高峰期
- **突发流量**: 模拟突然增加
- **持续负载**: 测试长期稳定性

## 故障排查

### 问题1: 连接被拒绝

```
Connection refused
```

**解决方案**:
- 确保后端服务正在运行
- 检查端口是否正确
- 检查防火墙设置

### 问题2: 响应时间过长

```
Response time > 5s
```

**解决方案**:
- 检查数据库查询性能
- 检查是否有慢查询
- 增加数据库连接池大小
- 优化API代码

### 问题3: 高错误率

```
Error rate > 10%
```

**解决方案**:
- 查看错误日志
- 检查数据库连接
- 检查内存使用
- 减少并发用户数

### 问题4: 内存泄漏

```
Memory usage keeps increasing
```

**解决方案**:
- 运行耐久测试
- 使用内存分析工具
- 检查数据库连接是否正确关闭
- 检查缓存是否正确清理

### 问题5: 数据库连接池耗尽

```
Too many connections
```

**解决方案**:
- 增加连接池大小
- 减少连接超时时间
- 优化查询效率
- 使用连接池监控

## 测试检查清单

### 测试前
- [ ] 后端服务正常运行
- [ ] 数据库已清理/重置
- [ ] 监控工具已启动
- [ ] 测试环境已配置
- [ ] 已了解性能基准

### 测试中
- [ ] 监控系统资源
- [ ] 记录异常情况
- [ ] 观察错误率
- [ ] 检查响应时间
- [ ] 查看日志输出

### 测试后
- [ ] 保存测试报告
- [ ] 分析性能数据
- [ ] 记录发现的问题
- [ ] 更新性能基准
- [ ] 清理测试数据

## 高级用法

### 自定义用户行为

编辑 `locustfile.py` 添加新的任务:

```python
@task(1)
def custom_task(self):
    """自定义任务"""
    self.client.get("/api/custom-endpoint")
```

### 分布式测试

在多台机器上运行测试:

```bash
# Master节点
locust -f locustfile.py --master --host=http://localhost:8000

# Worker节点
locust -f locustfile.py --worker --master-host=<master-ip>
```

### 使用环境变量

```bash
export LOCUST_HOST=http://localhost:8000
export LOCUST_USERS=100
export LOCUST_SPAWN_RATE=10

locust -f locustfile.py
```

## 相关文档

- [PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md) - 性能基准
- [LOAD_TESTING_REPORT.md](LOAD_TESTING_REPORT.md) - 测试报告模板
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - 性能优化指南

## 支持

如有问题，请查看:
- Locust官方文档: https://docs.locust.io/
- 项目README: [README.md](README.md)
- 性能优化指南: [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md)
