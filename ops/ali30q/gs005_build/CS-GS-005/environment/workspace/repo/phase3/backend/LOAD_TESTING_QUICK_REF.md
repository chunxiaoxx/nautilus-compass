# Locust压力测试快速参考

## 快速开始

### 安装Locust
```bash
pip install locust
```

### 运行测试

#### 方法1: 使用快速启动脚本（推荐）

**Linux/Mac**:
```bash
# 轻负载测试
./run_load_tests.sh light

# 中负载测试
./run_load_tests.sh medium

# 重负载测试
./run_load_tests.sh heavy

# 使用Web界面
./run_load_tests.sh light --web
```

**Windows**:
```cmd
REM 轻负载测试
run_load_tests.bat light

REM 中负载测试
run_load_tests.bat medium

REM 重负载测试
run_load_tests.bat heavy

REM 使用Web界面
run_load_tests.bat light --web
```

#### 方法2: 使用Python配置脚本

```bash
# 列出所有场景
python load_test_config.py list

# 运行特定场景
python load_test_config.py light
python load_test_config.py medium
python load_test_config.py heavy
python load_test_config.py peak
```

#### 方法3: 直接使用Locust

```bash
# Web界面模式
locust -f locustfile.py --host=http://localhost:8000

# 无头模式
locust -f locustfile.py --host=http://localhost:8000 \
    --users 50 --spawn-rate 5 --run-time 10m --headless
```

## 测试场景

| 场景 | 用户数 | 启动速率 | 运行时间 | 命令 |
|------|--------|----------|----------|------|
| 轻负载 | 10 | 2/s | 5分钟 | `./run_load_tests.sh light` |
| 中负载 | 50 | 5/s | 10分钟 | `./run_load_tests.sh medium` |
| 重负载 | 100 | 10/s | 15分钟 | `./run_load_tests.sh heavy` |
| 峰值 | 200 | 20/s | 10分钟 | `./run_load_tests.sh peak` |
| 压力 | 500 | 50/s | 20分钟 | `./run_load_tests.sh stress` |
| 尖峰 | 300 | 100/s | 5分钟 | `./run_load_tests.sh spike` |
| 耐久 | 30 | 3/s | 60分钟 | `./run_load_tests.sh endurance` |

## 常用命令

### 指定目标主机
```bash
./run_load_tests.sh medium --host http://staging.example.com
```

### 使用Web界面
```bash
./run_load_tests.sh light --web
# 然后访问 http://localhost:8089
```

### 不生成报告
```bash
./run_load_tests.sh light --no-report
```

### 自定义测试
```bash
./run_load_tests.sh custom
# 然后输入自定义参数
```

## 查看结果

### 实时监控
- Web界面: http://localhost:8089
- 终端输出: 实时显示RPS、响应时间、错误率

### 测试报告
- HTML报告: `results/load_test_*.html`
- CSV统计: `results/load_test_*_stats.csv`
- 失败记录: `results/load_test_*_failures.csv`

## 性能指标

### 响应时间目标
- 平均: < 500ms
- P95: < 1s
- P99: < 2s

### 吞吐量目标
- 轻负载: 10-20 RPS
- 中负载: 50-100 RPS
- 重负载: 100-200 RPS
- 峰值: 200-400 RPS

### 错误率目标
- 轻负载: < 0.1%
- 中负载: < 0.5%
- 重负载: < 1%
- 峰值: < 2%

## 故障排查

### 连接被拒绝
```bash
# 检查服务是否运行
curl http://localhost:8000/health

# 启动服务
python main.py
```

### 响应时间过长
- 检查数据库查询性能
- 查看慢查询日志
- 监控系统资源

### 高错误率
- 查看错误日志: `tail -f logs/app.log`
- 检查数据库连接
- 减少并发用户数

## 相关文档

- [LOAD_TESTING_GUIDE.md](LOAD_TESTING_GUIDE.md) - 完整测试指南
- [PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md) - 性能基准
- [LOAD_TESTING_REPORT.md](LOAD_TESTING_REPORT.md) - 测试报告模板

## 测试前检查清单

- [ ] Locust已安装
- [ ] 后端服务正在运行
- [ ] 数据库已清理/重置
- [ ] 监控工具已启动
- [ ] 了解性能基准

## 测试后检查清单

- [ ] 保存测试报告
- [ ] 分析性能数据
- [ ] 记录发现的问题
- [ ] 更新性能基准
- [ ] 清理测试数据
