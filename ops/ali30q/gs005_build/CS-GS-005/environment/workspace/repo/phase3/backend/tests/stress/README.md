# 压力测试快速参考指南

## 快速开始

### 1. 运行压力测试

```bash
# 轻负载测试（100并发，10分钟）
python tests/stress/run_production_tests.py --level light

# 中负载测试（500并发，15分钟）
python tests/stress/run_production_tests.py --level medium

# 重负载测试（1000并发，20分钟）
python tests/stress/run_production_tests.py --level heavy

# 峰值测试（2000并发，15分钟）
python tests/stress/run_production_tests.py --level peak

# 耐久测试（200并发，60分钟）
python tests/stress/run_production_tests.py --level endurance
```

### 2. 监控系统资源

```bash
# 在另一个终端运行
python tests/stress/monitor_resources.py --duration 3600 --interval 5
```

### 3. 分析测试结果

```bash
# 分析最新的测试结果
python tests/stress/analyze_test_results.py --csv results/production_light_*_stats.csv
```

## 测试场景对比

| 场景 | 并发数 | 时长 | 适用场景 |
|------|--------|------|---------|
| light | 100 | 10m | 开发验证 |
| medium | 500 | 15m | 正常负载 |
| heavy | 1000 | 20m | 高峰负载 |
| peak | 2000 | 15m | 极限测试 |
| endurance | 200 | 60m | 稳定性测试 |

## 性能指标

### 响应时间
- **优秀**: P95 < 200ms
- **良好**: P95 < 500ms
- **可接受**: P95 < 1000ms
- **需优化**: P95 > 1000ms

### 错误率
- **优秀**: < 0.1%
- **良好**: < 0.5%
- **可接受**: < 1%
- **不可接受**: > 1%

### 吞吐量
- **轻负载**: > 100 req/s
- **中负载**: > 500 req/s
- **重负载**: > 1000 req/s

## 常见问题

### Q: 测试失败怎么办？
A: 检查服务器是否运行，查看日志文件，降低并发数重试。

### Q: 如何查看实时测试进度？
A: 使用 `--no-headless` 参数打开Web界面。

### Q: 测试结果保存在哪里？
A: `tests/stress/results/` 目录。

### Q: 如何对比多次测试结果？
A: 使用分析工具对比不同时间的CSV文件。

## 文件说明

- `production_load_test.py` - 主测试脚本
- `run_production_tests.py` - 测试运行器
- `monitor_resources.py` - 资源监控
- `analyze_test_results.py` - 结果分析
- `results/` - 测试结果目录

## 相关文档

- [完整测试报告](../PRODUCTION_STRESS_TEST_REPORT.md)
- [性能优化指南](../PERFORMANCE_OPTIMIZATION.md)
- [负载测试指南](../LOAD_TESTING_GUIDE.md)
