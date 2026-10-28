# 区块链集成使用指南

本文档说明如何使用增强后的区块链集成功能。

---

## 目录

1. [基础使用](#基础使用)
2. [交易重试](#交易重试)
3. [监控功能](#监控功能)
4. [事件监听](#事件监听)
5. [Gas优化](#gas优化)
6. [错误处理](#错误处理)

---

## 基础使用

### 初始化区块链服务

```python
from blockchain import get_blockchain_service

# 获取区块链服务实例
service = get_blockchain_service()

# 发布任务
tx_hash = service.publish_task_on_chain(
    task_id="task_001",
    title="数据分析任务",
    description="分析用户行为数据",
    reward=1000000000000000000,  # 1 ETH in Wei
    deadline=1735689600  # Unix时间戳
)

if tx_hash:
    print(f"任务发布成功: {tx_hash}")
else:
    print("任务发布失败")
```

### 查询区块链数据

```python
# 获取任务信息
task_info = service.get_task_from_chain("task_001")
if task_info:
    print(f"任务创建者: {task_info['creator']}")
    print(f"任务奖励: {task_info['reward']} Wei")
    print(f"任务状态: {task_info['status']}")

# 获取Agent信息
agent_info = service.get_agent_from_chain("0x...")
if agent_info:
    print(f"Agent名称: {agent_info['name']}")
    print(f"声誉值: {agent_info['reputation']}")
    print(f"完成任务数: {agent_info['completed_tasks']}")

# 获取奖励余额
balance = service.get_reward_balance_from_chain("0x...")
if balance is not None:
    print(f"奖励余额: {balance} Wei")
```

---

## 交易重试

### 使用默认重试配置

```python
from blockchain import get_blockchain_service

service = get_blockchain_service()

# 所有交易方法都自动使用重试机制
tx_hash = service.accept_task_on_chain("task_001")
# 如果失败会自动重试最多3次，每次增加Gas价格
```

### 自定义重试配置

```python
from blockchain.transaction_retry import (
    TransactionRetryManager,
    TransactionRetryConfig
)

# 创建自定义配置
config = TransactionRetryConfig(
    max_retries=5,              # 最大重试5次
    initial_delay=3.0,          # 初始延迟3秒
    max_delay=60.0,             # 最大延迟60秒
    backoff_factor=2.0,         # 退避因子2.0
    gas_price_increase_factor=1.15,  # Gas价格每次增加15%
    timeout=180                 # 超时时间180秒
)

# 使用自定义配置
retry_manager = TransactionRetryManager(config)

# 构建交易函数
def build_transaction():
    from blockchain import get_task_market, get_web3_config

    task_market = get_task_market()
    config = get_web3_config()
    account = config.get_account()

    return task_market.functions.acceptTask("task_001").build_transaction({
        'from': account,
        'gasPrice': retry_manager.get_optimal_gas_price("high"),
        'nonce': config.w3.eth.get_transaction_count(account)
    })

# 执行交易
tx_hash = retry_manager.execute_with_retry(
    build_transaction,
    operation_name="AcceptTask"
)
```

### 取消待处理的交易

```python
from blockchain.transaction_retry import get_retry_manager

retry_manager = get_retry_manager()

# 取消nonce为5的交易
cancel_tx = retry_manager.cancel_transaction(
    nonce=5,
    gas_price_multiplier=1.5  # Gas价格提高50%
)

if cancel_tx:
    print(f"取消交易已发送: {cancel_tx}")
```

---

## 监控功能

### 跟踪交易

```python
from blockchain import get_monitor

monitor = get_monitor()

# 发送交易后立即跟踪
tx_hash = service.publish_task_on_chain(...)
if tx_hash:
    monitor.track_transaction(tx_hash, "publish_task")

# 更新交易状态
import time
time.sleep(30)  # 等待交易确认
metrics = monitor.update_transaction_status(tx_hash)

if metrics:
    print(f"交易状态: {metrics.status}")
    print(f"Gas使用: {metrics.gas_used}")
    print(f"总成本: {metrics.total_cost} Wei")
```

### 获取统计信息

```python
from blockchain import get_monitor

monitor = get_monitor()

# 获取综合统计
stats = monitor.get_overall_statistics()
print(f"总交易数: {stats['transactions']['total']}")
print(f"成功率: {stats['transactions']['success_rate_percent']:.2f}%")
print(f"总Gas费用: {stats['gas']['total_cost_eth']} ETH")

# 获取Gas统计（最近24小时）
gas_stats = monitor.get_gas_statistics(hours=24)
print(f"当前Gas价格: {gas_stats['current_gas_price_gwei']:.2f} Gwei")
print(f"平均Gas价格: {gas_stats['average_gas_price_gwei']:.2f} Gwei")
print(f"网络拥堵: {gas_stats['current_congestion']}")

# 获取连接状态
conn_status = monitor.get_connection_status()
print(f"连接状态: {'已连接' if conn_status['is_connected'] else '断开'}")
print(f"区块高度: {conn_status['block_number']}")
print(f"延迟: {conn_status['latency_ms']:.2f}ms")
```

### 生成监控报告

```python
from blockchain import get_monitor

monitor = get_monitor()

# 生成文本报告
report = monitor.generate_report()
print(report)

# 获取交易历史
history = monitor.get_transaction_history(
    limit=50,
    status_filter="success"  # 只获取成功的交易
)

for tx in history:
    print(f"{tx['timestamp']}: {tx['operation_type']} - {tx['tx_hash']}")
```

### 定期记录Gas价格

```python
import asyncio
from blockchain import get_monitor

async def gas_price_monitor():
    monitor = get_monitor()

    while True:
        # 记录当前Gas价格
        metrics = monitor.record_gas_price()
        if metrics:
            print(f"Gas价格: {metrics.gas_price_gwei:.2f} Gwei ({metrics.network_congestion})")

        await asyncio.sleep(60)  # 每分钟记录一次

# 运行监控
asyncio.run(gas_price_monitor())
```

---

## 事件监听

### 启动事件监听器

```python
import asyncio
from blockchain import get_event_listener

async def main():
    listener = get_event_listener()

    # 注册事件处理器
    async def handle_task_published(task_id, creator, reward):
        print(f"新任务发布: {task_id}")
        print(f"创建者: {creator}")
        print(f"奖励: {reward} Wei")
        # 在这里添加业务逻辑，如更新数据库

    async def handle_task_completed(task_id, agent, reward):
        print(f"任务完成: {task_id}")
        print(f"Agent: {agent}")
        print(f"奖励: {reward} Wei")
        # 在这里添加业务逻辑

    # 注册处理器
    listener.register_handler('TaskPublished', handle_task_published)
    listener.register_handler('TaskCompleted', handle_task_completed)

    # 启动监听器
    await listener.start()

# 运行
asyncio.run(main())
```

### 查看监听器统计

```python
from blockchain import get_event_listener

listener = get_event_listener()

# 获取统计信息
stats = listener.get_statistics()
print(f"运行状态: {stats['is_running']}")
print(f"错误次数: {stats['error_count']}")
print(f"缓存事件数: {stats['cached_events']}")
print(f"最后处理区块: {stats['last_processed_blocks']}")

# 获取最近的事件
recent_events = listener.get_recent_events(count=10)
for event_data in recent_events:
    event = event_data['event']
    print(f"事件: {event['event']}, 区块: {event['blockNumber']}")
```

### 自定义监听器配置

```python
from blockchain.event_listener import BlockchainEventListener

# 创建自定义配置的监听器
listener = BlockchainEventListener(
    reconnect_delay=10,          # 重连延迟10秒
    max_reconnect_attempts=20,   # 最多重连20次
    poll_interval=10,            # 每10秒轮询一次
    max_block_range=500          # 每次最多扫描500个区块
)

# 使用自定义监听器
# ...
```

---

## Gas优化

### 估算交易成本

```python
from blockchain import get_blockchain_service

service = get_blockchain_service()

# 估算发布任务的成本
cost_estimate = service.estimate_transaction_cost(
    operation_type="publish_task",
    task_id="task_001",
    title="测试任务",
    description="测试描述",
    reward=1000000000000000000,
    deadline=1735689600
)

if cost_estimate:
    print(f"估算Gas: {cost_estimate['estimated_gas']}")
    print(f"Gas价格: {cost_estimate['gas_price_gwei']:.2f} Gwei")
    print(f"估算成本: {cost_estimate['estimated_cost_eth']:.6f} ETH")
```

### 使用不同优先级的Gas价格

```python
from blockchain.transaction_retry import get_retry_manager

retry_manager = get_retry_manager()

# 低优先级（便宜但慢）
low_gas = retry_manager.get_optimal_gas_price("low")

# 标准优先级（平衡）
standard_gas = retry_manager.get_optimal_gas_price("standard")

# 高优先级（贵但快）
high_gas = retry_manager.get_optimal_gas_price("high")

print(f"低优先级: {low_gas} Wei")
print(f"标准优先级: {standard_gas} Wei")
print(f"高优先级: {high_gas} Wei")
```

### 智能Gas估算

```python
from blockchain.transaction_retry import get_retry_manager
from blockchain import get_task_market, get_web3_config

retry_manager = get_retry_manager()
task_market = get_task_market()
config = get_web3_config()

# 构建交易
transaction = task_market.functions.acceptTask("task_001").build_transaction({
    'from': config.get_account(),
    'gasPrice': config.w3.eth.gas_price,
    'nonce': config.w3.eth.get_transaction_count(config.get_account())
})

# 估算Gas并添加20%缓冲
estimated_gas = retry_manager.estimate_gas_with_buffer(transaction, buffer_percent=20)
transaction['gas'] = estimated_gas

print(f"估算Gas（含缓冲）: {estimated_gas}")
```

### 计算任务总Gas费用

```python
from blockchain import get_blockchain_service

service = get_blockchain_service()

# 任务相关的所有交易哈希
tx_hashes = [
    "0x...",  # publish_task
    "0x...",  # accept_task
    "0x...",  # submit_task
    "0x..."   # complete_task
]

# 计算总Gas费用
gas_info = service.calculate_task_total_gas(tx_hashes)

if gas_info:
    print(f"总Gas使用: {gas_info['total_gas_used']}")
    print(f"总Gas费用: {gas_info['total_gas_cost']} Wei")
    print(f"Agent分担: {gas_info['gas_split']} Wei (50%)")
```

---

## 错误处理

### 处理常见错误

```python
from blockchain import get_blockchain_service
from web3.exceptions import ContractLogicError, TimeExhausted

service = get_blockchain_service()

try:
    tx_hash = service.publish_task_on_chain(
        task_id="task_001",
        title="测试任务",
        description="测试",
        reward=1000000000000000000,
        deadline=1735689600
    )

    if tx_hash:
        print(f"交易成功: {tx_hash}")
    else:
        print("交易失败，请检查日志")

except ContractLogicError as e:
    print(f"合约逻辑错误: {e}")
    # 可能是任务ID重复、参数无效等

except TimeExhausted as e:
    print(f"交易超时: {e}")
    # 交易可能仍在处理中

except ValueError as e:
    error_msg = str(e)
    if "insufficient funds" in error_msg.lower():
        print("余额不足")
    elif "gas" in error_msg.lower():
        print("Gas相关错误")
    else:
        print(f"参数错误: {e}")

except Exception as e:
    print(f"未知错误: {e}")
```

### 检查交易状态

```python
from blockchain.transaction_retry import get_retry_manager

retry_manager = get_retry_manager()

# 检查交易状态
status = retry_manager.check_transaction_status("0x...")

print(f"状态: {status['status']}")
print(f"区块号: {status.get('block_number', 'N/A')}")
print(f"Gas使用: {status.get('gas_used', 'N/A')}")
print(f"确认数: {status.get('confirmations', 'N/A')}")
```

### 连接状态检查

```python
from blockchain import get_monitor

monitor = get_monitor()

# 检查连接
metrics = monitor.check_connection()

if metrics.is_connected:
    print(f"连接正常，区块高度: {metrics.block_number}")
    print(f"延迟: {metrics.latency_ms:.2f}ms")
else:
    print(f"连接失败: {metrics.error_message}")
```

---

## 完整示例

### 完整的任务发布和监控流程

```python
import asyncio
from blockchain import (
    get_blockchain_service,
    get_monitor,
    get_event_listener
)

async def publish_and_monitor_task():
    # 初始化服务
    service = get_blockchain_service()
    monitor = get_monitor()
    listener = get_event_listener()

    # 注册事件处理器
    async def handle_task_published(task_id, creator, reward):
        print(f"✅ 任务已发布到区块链: {task_id}")

    listener.register_handler('TaskPublished', handle_task_published)

    # 启动事件监听器（后台运行）
    asyncio.create_task(listener.start())

    # 发布任务
    print("📤 发布任务...")
    tx_hash = service.publish_task_on_chain(
        task_id="task_001",
        title="数据分析任务",
        description="分析用户行为数据",
        reward=1000000000000000000,
        deadline=1735689600
    )

    if not tx_hash:
        print("❌ 任务发布失败")
        return

    print(f"📝 交易已提交: {tx_hash}")

    # 跟踪交易
    monitor.track_transaction(tx_hash, "publish_task")

    # 等待交易确认
    print("⏳ 等待交易确认...")
    await asyncio.sleep(30)

    # 更新交易状态
    metrics = monitor.update_transaction_status(tx_hash)

    if metrics and metrics.status == "success":
        print(f"✅ 交易成功确认")
        print(f"   Gas使用: {metrics.gas_used}")
        print(f"   总成本: {service.w3.from_wei(metrics.total_cost, 'ether')} ETH")
        print(f"   确认数: {metrics.confirmations}")
    else:
        print("❌ 交易失败或未确认")

    # 生成报告
    print("\n📊 监控报告:")
    print(monitor.generate_report())

    # 停止监听器
    listener.stop()

# 运行
if __name__ == "__main__":
    asyncio.run(publish_and_monitor_task())
```

---

## 最佳实践

### 1. 始终使用监控

```python
from blockchain import get_blockchain_service, get_monitor

service = get_blockchain_service()
monitor = get_monitor()

# 发送交易后立即跟踪
tx_hash = service.publish_task_on_chain(...)
if tx_hash:
    monitor.track_transaction(tx_hash, "publish_task")
```

### 2. 定期检查连接状态

```python
import asyncio
from blockchain import get_monitor

async def connection_monitor():
    monitor = get_monitor()
    while True:
        monitor.check_connection()
        await asyncio.sleep(60)  # 每分钟检查一次
```

### 3. 记录Gas价格趋势

```python
import asyncio
from blockchain import get_monitor

async def gas_price_tracker():
    monitor = get_monitor()
    while True:
        monitor.record_gas_price()
        await asyncio.sleep(300)  # 每5分钟记录一次
```

### 4. 使用事件监听器同步状态

```python
from blockchain import get_event_listener

listener = get_event_listener()

async def sync_task_status(task_id, agent, reward):
    # 更新数据库
    # await update_database(task_id, status="completed")
    pass

listener.register_handler('TaskCompleted', sync_task_status)
```

### 5. 估算成本后再执行

```python
from blockchain import get_blockchain_service

service = get_blockchain_service()

# 先估算成本
estimate = service.estimate_transaction_cost(
    operation_type="publish_task",
    task_id="task_001",
    title="测试",
    description="测试",
    reward=1000000000000000000,
    deadline=1735689600
)

if estimate and estimate['estimated_cost_eth'] < 0.01:
    # 成本可接受，执行交易
    tx_hash = service.publish_task_on_chain(...)
else:
    print("成本过高，取消操作")
```

---

## 故障排查

### 问题：交易一直失败

**解决方案**:
1. 检查账户余额
2. 检查Gas价格是否过低
3. 查看监控日志
4. 增加重试次数和Gas价格

### 问题：事件监听器不工作

**解决方案**:
1. 检查合约地址是否正确
2. 检查网络连接
3. 查看监听器统计信息
4. 检查事件处理器是否正确注册

### 问题：Gas费用过高

**解决方案**:
1. 使用低优先级Gas价格
2. 在网络不拥堵时执行交易
3. 优化合约调用
4. 批量处理交易

---

**文档结束**

*更多信息请参考 BLOCKCHAIN_INTEGRATION_COMPLETE_REPORT.md*
