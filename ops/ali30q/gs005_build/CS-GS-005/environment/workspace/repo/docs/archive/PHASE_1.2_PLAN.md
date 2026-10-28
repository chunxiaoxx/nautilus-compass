# Phase 1.2 执行计划 - CI/CD + 监控

**阶段**: Phase 1.2
**预计时间**: 3天
**Agent数量**: 2个并行

---

## Agent 4 - CI/CD专家

### 任务目标
配置GitHub Actions自动化测试和部署

### 具体工作

#### 1. 创建GitHub Actions工作流
**文件**: `.github/workflows/test.yml`
```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          cd phase3/backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd phase3/backend
          pytest tests/ -v --cov=nexus_protocol --cov=nexus_server --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### 2. 创建代码质量检查工作流
**文件**: `.github/workflows/quality.yml`
```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install tools
        run: |
          pip install pylint flake8 black mypy bandit
      - name: Run pylint
        run: |
          cd phase3/backend
          pylint nexus_protocol/ nexus_server.py
      - name: Run flake8
        run: |
          cd phase3/backend
          flake8 nexus_protocol/ nexus_server.py
      - name: Run mypy
        run: |
          cd phase3/backend
          mypy nexus_protocol/ nexus_server.py
      - name: Run bandit
        run: |
          cd phase3/backend
          bandit -r nexus_protocol/ nexus_server.py
```

#### 3. 创建Docker构建工作流
**文件**: `.github/workflows/docker.yml`
```yaml
name: Docker Build

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: |
          cd phase3/backend
          docker build -t nexus-server:latest .
      - name: Test Docker image
        run: |
          docker run -d --name test-server -p 8001:8001 nexus-server:latest
          sleep 10
          curl http://localhost:8001/health
```

#### 4. 创建CI/CD文档
**文件**: `CI_CD_GUIDE.md`

### 验收标准
- ✅ GitHub Actions配置完成
- ✅ 测试工作流正常运行
- ✅ 代码质量检查正常运行
- ✅ Docker构建工作流正常运行
- ✅ 文档完整

---

## Agent 5 - 监控专家

### 任务目标
添加监控、日志和告警系统

### 具体工作

#### 1. 添加结构化日志
修改 `nexus_server.py`：
```python
import logging
import json
from datetime import datetime

# 配置结构化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def log(self, level, event, **kwargs):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'event': event,
            **kwargs
        }
        self.logger.log(getattr(logging, level), json.dumps(log_entry))

logger = StructuredLogger('nexus_server')
```

#### 2. 添加性能监控
创建 `monitoring/metrics.py`：
```python
import time
from collections import defaultdict
from datetime import datetime

class MetricsCollector:
    def __init__(self):
        self.metrics = defaultdict(list)

    def record_latency(self, operation, duration):
        self.metrics[f'{operation}_latency'].append(duration)

    def record_count(self, operation):
        self.metrics[f'{operation}_count'].append(1)

    def get_stats(self):
        stats = {}
        for key, values in self.metrics.items():
            if 'latency' in key:
                stats[key] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'p95': sorted(values)[int(len(values) * 0.95)]
                }
            else:
                stats[key] = sum(values)
        return stats
```

#### 3. 添加健康检查端点
修改 `nexus_server.py`：
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": time.time() - start_time,
        "agents": len(server.agents),
        "queue_size": server.message_queue.qsize()
    }

@app.get("/metrics")
async def get_metrics():
    return metrics_collector.get_stats()
```

#### 4. 创建监控文档
**文件**: `MONITORING_GUIDE.md`

### 验收标准
- ✅ 结构化日志已添加
- ✅ 性能监控已添加
- ✅ 健康检查端点正常
- ✅ 指标收集正常
- ✅ 文档完整

---

## 并行执行

两个Agent同时工作：
- Agent 4: CI/CD配置
- Agent 5: 监控系统

预计3天完成！

---

## 验收标准（超高标准）

### CI/CD
- ✅ 所有工作流配置正确
- ✅ 测试自动运行
- ✅ 代码质量自动检查
- ✅ Docker自动构建
- ✅ 无配置错误

### 监控
- ✅ 日志结构化且清晰
- ✅ 性能指标准确
- ✅ 健康检查可靠
- ✅ 告警及时
- ✅ 文档完整

### 整体
- ✅ 可以在生产环境使用
- ✅ 可以快速发现问题
- ✅ 可以快速定位问题
- ✅ 可以快速解决问题

---

**准备就绪，等待Phase 1.1完成后立即启动！**
