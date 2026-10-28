# 📚 Locust压力测试 - 文档索引

## 🎯 快速导航

### 🚀 我想立即开始测试
→ 阅读 [README_LOAD_TESTING.md](README_LOAD_TESTING.md)
→ 然后运行: `./run_load_tests.sh light`

### 📖 我想了解如何使用
→ 阅读 [LOAD_TESTING_GUIDE.md](LOAD_TESTING_GUIDE.md)

### ⚡ 我需要快速参考
→ 阅读 [LOAD_TESTING_QUICK_REF.md](LOAD_TESTING_QUICK_REF.md)

### 📊 我想了解性能基准
→ 阅读 [PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)

### 📝 我需要编写测试报告
→ 使用 [LOAD_TESTING_REPORT.md](LOAD_TESTING_REPORT.md) 模板

### 🔍 我想了解项目详情
→ 阅读 [LOAD_TESTING_FINAL_DELIVERY.md](LOAD_TESTING_FINAL_DELIVERY.md)

---

## 📂 文件分类

### 核心脚本文件

| 文件 | 用途 | 如何使用 |
|------|------|----------|
| **locustfile.py** | 主测试脚本 | `locust -f locustfile.py` |
| **load_test_config.py** | 配置工具 | `python load_test_config.py medium` |
| **run_load_tests.sh** | Linux/Mac启动 | `./run_load_tests.sh light` |
| **run_load_tests.bat** | Windows启动 | `run_load_tests.bat light` |
| **compare_load_test_results.py** | 结果对比 | `python compare_load_test_results.py test1.csv test2.csv` |

### 入门文档

| 文件 | 内容 | 适合人群 |
|------|------|----------|
| **README_LOAD_TESTING.md** | 项目README，快速开始 | 所有人 |
| **LOAD_TESTING_QUICK_REF.md** | 快速参考，常用命令 | 已熟悉基础的用户 |
| **LOAD_TESTING_SUMMARY.txt** | 纯文本摘要 | 快速浏览 |

### 详细文档

| 文件 | 内容 | 适合人群 |
|------|------|----------|
| **LOAD_TESTING_GUIDE.md** | 完整使用指南 | 需要深入了解的用户 |
| **PERFORMANCE_BENCHMARKS.md** | 性能基准详解 | 性能工程师 |
| **LOAD_TESTING_REPORT.md** | 测试报告模板 | 需要编写报告的用户 |

### 总结文档

| 文件 | 内容 | 适合人群 |
|------|------|----------|
| **LOAD_TESTING_PROJECT_SUMMARY.md** | 项目功能总结 | 项目管理者 |
| **LOAD_TESTING_COMPLETION_REPORT.md** | 完成报告 | 项目验收 |
| **LOAD_TESTING_FINAL_DELIVERY.md** | 最终交付报告 | 项目交付 |
| **LOAD_TESTING_TASK_COMPLETE.md** | 任务完成摘要 | 快速确认 |

---

## 🎓 学习路径

### 初学者路径
1. 阅读 `README_LOAD_TESTING.md` (5分钟)
2. 安装Locust: `pip install locust`
3. 运行第一个测试: `./run_load_tests.sh light`
4. 查看生成的HTML报告
5. 阅读 `LOAD_TESTING_QUICK_REF.md` 了解更多命令

### 进阶用户路径
1. 阅读 `LOAD_TESTING_GUIDE.md` 了解详细用法
2. 阅读 `PERFORMANCE_BENCHMARKS.md` 了解性能目标
3. 运行不同场景: medium, heavy, peak
4. 使用 `compare_load_test_results.py` 对比结果
5. 根据需要修改 `locustfile.py`

### 专家路径
1. 研究 `locustfile.py` 的实现细节
2. 自定义测试场景
3. 集成到CI/CD流程
4. 实现分布式测试
5. 建立性能监控体系

---

## 📋 常见任务

### 任务1: 运行基本测试
```bash
# 1. 确保后端服务运行
python main.py

# 2. 运行轻负载测试
./run_load_tests.sh light

# 3. 查看报告
open results/load_test_light_*.html
```
**参考文档**: README_LOAD_TESTING.md

### 任务2: 运行完整测试套件
```bash
./run_load_tests.sh light
./run_load_tests.sh medium
./run_load_tests.sh heavy
./run_load_tests.sh peak
```
**参考文档**: LOAD_TESTING_GUIDE.md

### 任务3: 使用Web界面
```bash
./run_load_tests.sh light --web
# 访问 http://localhost:8089
```
**参考文档**: LOAD_TESTING_GUIDE.md

### 任务4: 对比测试结果
```bash
python compare_load_test_results.py \
    results/test1_stats.csv \
    results/test2_stats.csv
```
**参考文档**: LOAD_TESTING_GUIDE.md

### 任务5: 编写测试报告
1. 运行测试并保存结果
2. 使用 `LOAD_TESTING_REPORT.md` 作为模板
3. 填写测试数据和分析
**参考文档**: LOAD_TESTING_REPORT.md

---

## 🔍 按主题查找

### 安装和配置
- README_LOAD_TESTING.md → "安装依赖"
- LOAD_TESTING_GUIDE.md → "安装Locust"

### 运行测试
- LOAD_TESTING_QUICK_REF.md → "快速开始"
- LOAD_TESTING_GUIDE.md → "运行测试"
- README_LOAD_TESTING.md → "使用方法"

### 测试场景
- LOAD_TESTING_GUIDE.md → "测试场景"
- PERFORMANCE_BENCHMARKS.md → "负载场景基准"
- load_test_config.py → 场景配置代码

### 性能基准
- PERFORMANCE_BENCHMARKS.md → 完整的性能基准
- LOAD_TESTING_REPORT.md → "预期结果"

### 结果分析
- LOAD_TESTING_GUIDE.md → "分析结果"
- LOAD_TESTING_REPORT.md → "如何解读结果"
- compare_load_test_results.py → 结果对比工具

### 故障排查
- LOAD_TESTING_GUIDE.md → "故障排查"
- LOAD_TESTING_QUICK_REF.md → "故障排查"
- README_LOAD_TESTING.md → "常见问题"

### 最佳实践
- LOAD_TESTING_GUIDE.md → "最佳实践"
- PERFORMANCE_BENCHMARKS.md → "测量方法"

### 自定义和扩展
- locustfile.py → 测试脚本源码
- LOAD_TESTING_GUIDE.md → "高级用法"

---

## 📊 文档统计

- **总文件数**: 14个
- **核心脚本**: 5个 (1,240行代码)
- **文档文件**: 9个 (2,506行文档)
- **总大小**: 约100KB

---

## ✅ 快速检查清单

### 开始测试前
- [ ] 已安装Locust (`pip install locust`)
- [ ] 后端服务正在运行
- [ ] 已阅读 README_LOAD_TESTING.md
- [ ] 了解基本命令

### 运行测试时
- [ ] 选择合适的测试场景
- [ ] 监控系统资源
- [ ] 观察错误率
- [ ] 记录异常情况

### 测试完成后
- [ ] 保存测试报告
- [ ] 分析性能数据
- [ ] 对比历史结果
- [ ] 记录发现的问题

---

## 🆘 需要帮助？

### 问题: 不知道从哪里开始
→ 阅读 [README_LOAD_TESTING.md](README_LOAD_TESTING.md)

### 问题: 命令记不住
→ 查看 [LOAD_TESTING_QUICK_REF.md](LOAD_TESTING_QUICK_REF.md)

### 问题: 测试失败了
→ 查看 [LOAD_TESTING_GUIDE.md](LOAD_TESTING_GUIDE.md) 的"故障排查"部分

### 问题: 不知道性能是否达标
→ 对照 [PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)

### 问题: 需要编写报告
→ 使用 [LOAD_TESTING_REPORT.md](LOAD_TESTING_REPORT.md) 模板

---

## 🎯 推荐阅读顺序

**第一次使用** (30分钟):
1. README_LOAD_TESTING.md (10分钟)
2. LOAD_TESTING_QUICK_REF.md (5分钟)
3. 运行第一个测试 (10分钟)
4. 查看报告 (5分钟)

**深入学习** (2小时):
1. LOAD_TESTING_GUIDE.md (45分钟)
2. PERFORMANCE_BENCHMARKS.md (30分钟)
3. 运行多个场景 (30分钟)
4. 对比结果 (15分钟)

**完全掌握** (1天):
1. 阅读所有文档 (3小时)
2. 研究源码 (2小时)
3. 运行完整测试套件 (2小时)
4. 自定义测试场景 (1小时)

---

**最后更新**: 2026-02-26
**文档版本**: 1.0
