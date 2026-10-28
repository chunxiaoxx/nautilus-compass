# Phase 1.3 执行计划 - 24小时稳定性测试

**阶段**: Phase 1.3
**预计时间**: 3天（1天设置 + 24小时运行 + 1天分析）
**Agent数量**: 1个

---

## Agent 6 - 稳定性测试专家

### 任务目标
验证系统可以稳定运行24小时以上

### 具体工作

#### 1. 创建24小时测试脚本
**文件**: `tests/test_24h_stability.py`

```python
import asyncio
import time
import psutil
import logging
from datetime import datetime, timedelta
from nexus_client import NexusClient
from nexus_protocol.types import create_request_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StabilityTester:
    def __init__(self, duration_hours=24):
        self.duration = duration_hours * 3600
        self.start_time = None
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'memory_samples': [],
            'cpu_samples': []
        }

    async def monitor_resources(self):
        """监控资源使用"""
        process = psutil.Process()
        while time.time() - self.start_time < self.duration:
            self.metrics['memory_samples'].append(
                process.memory_info().rss / 1024 / 1024  # MB
            )
            self.metrics['cpu_samples'].append(
                process.cpu_percent(interval=1)
            )
            await asyncio.sleep(60)  # 每分钟采样

    async def send_messages(self, client, agent_id):
        """持续发送消息"""
        while time.time() - self.start_time < self.duration:
            try:
                msg = create_request_message(
                    from_agent=agent_id,
                    to_agent="test-receiver",
                    task_description="Stability test message"
                )
                await client.send_message(msg)
                self.metrics['messages_sent'] += 1
                await asyncio.sleep(1)  # 每秒1条消息
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                self.metrics['errors'] += 1

    async def run_test(self):
        """运行24小时测试"""
        self.start_time = time.time()
        logger.info(f"Starting 24-hour stability test at {datetime.now()}")

        # 创建10个客户端
        clients = []
        for i in range(10):
            client = NexusClient(f"stability-agent-{i}", "localhost", 8001)
            await client.connect()
            clients.append(client)

        # 启动任务
        tasks = [
            self.monitor_resources(),
            *[self.send_messages(client, f"stability-agent-{i}")
              for i, client in enumerate(clients)]
        ]

        await asyncio.gather(*tasks)

        # 清理
        for client in clients:
            await client.disconnect()

        logger.info(f"Test completed at {datetime.now()}")
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        report = f"""
# 24小时稳定性测试报告

## 测试时间
- 开始: {datetime.fromtimestamp(self.start_time)}
- 结束: {datetime.now()}
- 持续: {self.duration / 3600:.2f} 小时

## 消息统计
- 发送消息: {self.metrics['messages_sent']}
- 接收消息: {self.metrics['messages_received']}
- 错误数: {self.metrics['errors']}
- 成功率: {(1 - self.metrics['errors'] / max(self.metrics['messages_sent'], 1)) * 100:.2f}%

## 资源使用
- 平均内存: {sum(self.metrics['memory_samples']) / len(self.metrics['memory_samples']):.2f} MB
- 最大内存: {max(self.metrics['memory_samples']):.2f} MB
- 内存增长: {self.metrics['memory_samples'][-1] - self.metrics['memory_samples'][0]:.2f} MB
- 平均CPU: {sum(self.metrics['cpu_samples']) / len(self.metrics['cpu_samples']):.2f}%
- 最大CPU: {max(self.metrics['cpu_samples']):.2f}%

## 结论
{'✅ 测试通过 - 系统稳定' if self.metrics['errors'] < 100 and
 self.metrics['memory_samples'][-1] - self.metrics['memory_samples'][0] < 100
 else '❌ 测试失败 - 发现问题'}
"""

        with open('24H_STABILITY_REPORT.md', 'w') as f:
            f.write(report)

        logger.info("Report generated: 24H_STABILITY_REPORT.md")

if __name__ == "__main__":
    tester = StabilityTester(duration_hours=24)
    asyncio.run(tester.run_test())
```

#### 2. 创建内存泄漏检测脚本
**文件**: `tests/test_memory_leak.py`

```python
import asyncio
import tracemalloc
import gc
from nexus_client import NexusClient

async def test_memory_leak():
    """检测内存泄漏"""
    tracemalloc.start()

    # 运行1000次连接/断开循环
    for i in range(1000):
        client = NexusClient(f"leak-test-{i}", "localhost", 8001)
        await client.connect()
        await client.disconnect()

        if i % 100 == 0:
            gc.collect()
            current, peak = tracemalloc.get_traced_memory()
            print(f"Iteration {i}: Current={current/1024/1024:.2f}MB, Peak={peak/1024/1024:.2f}MB")

    tracemalloc.stop()
```

#### 3. 创建并发压力测试
**文件**: `tests/test_concurrent_stress.py`

```python
import asyncio
from nexus_client import NexusClient

async def stress_test():
    """并发压力测试"""
    # 创建100个客户端
    clients = []
    for i in range(100):
        client = NexusClient(f"stress-agent-{i}", "localhost", 8001)
        await client.connect()
        clients.append(client)

    # 每个客户端发送1000条消息
    async def send_messages(client, agent_id):
        for j in range(1000):
            msg = create_request_message(
                from_agent=agent_id,
                to_agent="stress-receiver",
                task_description=f"Stress test message {j}"
            )
            await client.send_message(msg)

    # 并发执行
    await asyncio.gather(*[
        send_messages(client, f"stress-agent-{i}")
        for i, client in enumerate(clients)
    ])

    # 清理
    for client in clients:
        await client.disconnect()
```

#### 4. 创建监控脚本
**文件**: `tests/monitor_stability.py`

```python
import time
import requests
import psutil
from datetime import datetime

def monitor_server(duration_hours=24):
    """监控服务器状态"""
    start_time = time.time()
    duration = duration_hours * 3600

    while time.time() - start_time < duration:
        try:
            # 检查健康状态
            health = requests.get('http://localhost:8001/health').json()

            # 检查指标
            metrics = requests.get('http://localhost:8001/metrics').json()

            # 检查系统资源
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent

            print(f"[{datetime.now()}] Health: {health['status']}, "
                  f"Agents: {health['agents']}, "
                  f"CPU: {cpu}%, Memory: {memory}%")

        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")

        time.sleep(60)  # 每分钟检查一次
```

#### 5. 创建自动化测试脚本
**文件**: `run_stability_tests.sh`

```bash
#!/bin/bash

echo "Starting 24-hour stability test..."

# 启动服务器
cd C:/Users/chunx/Projects/nautilus-core/phase3/backend
python nexus_server.py &
SERVER_PID=$!

sleep 5

# 启动监控
python tests/monitor_stability.py &
MONITOR_PID=$!

# 运行稳定性测试
python tests/test_24h_stability.py

# 运行内存泄漏测试
python tests/test_memory_leak.py

# 运行并发压力测试
python tests/test_concurrent_stress.py

# 停止监控和服务器
kill $MONITOR_PID
kill $SERVER_PID

echo "Tests completed!"
```

---

## 验收标准（超高标准）

### 稳定性
- ✅ 24小时无崩溃
- ✅ 24小时无重启
- ✅ 错误率 < 0.1%
- ✅ 响应时间稳定

### 资源使用
- ✅ 无内存泄漏（增长 < 100MB）
- ✅ CPU使用稳定（< 80%）
- ✅ 内存使用稳定（< 1GB）
- ✅ 无资源耗尽

### 性能
- ✅ 消息吞吐量稳定
- ✅ 延迟稳定
- ✅ 无性能退化
- ✅ 并发处理正常

### 报告
- ✅ 详细的测试报告
- ✅ 资源使用图表
- ✅ 问题分析
- ✅ 改进建议

---

**准备就绪，等待Phase 1.2完成后立即启动！**
