# Gas费用1:1分担机制实现文档

## 概述
本文档描述了任务发布者和执行者1:1分担Gas费用的机制实现。

## 实现内容

### 1. 数据库模型更新 (models/database.py)

在Task表中添加了以下字段：
- `gas_used`: 记录所有交易的总Gas使用量
- `gas_cost`: 记录总Gas费用（Wei）
- `gas_split`: 记录Agent应承担的Gas费用（50%）

### 2. 区块链服务层 (blockchain/blockchain_service.py)

添加了以下Gas计算方法：

#### get_transaction_gas_used(tx_hash)
- 获取单个交易的Gas使用情况
- 返回gas_used、gas_price和gas_cost

#### calculate_gas_split(total_gas_cost)
- 计算Gas费用分担（50%）
- 使用整数除法确保精确计算

#### calculate_task_total_gas(tx_hashes)
- 计算任务所有交易的总Gas费用
- 支持多个交易哈希列表
- 自动过滤None值

### 3. API端点更新 (api/tasks.py)

#### 更新TaskResponse模型
添加了gas_used、gas_cost、gas_split字段到响应中

#### 更新complete_task端点
- 任务完成时自动计算所有交易的Gas费用
- 从奖励中扣除Agent的Gas份额（50%）
- 记录详细的Gas信息到日志

#### 新增GET /api/tasks/{id}/gas端点
查询任务的Gas费用详情，返回：
- gas_used: 总Gas使用量
- gas_cost: 总Gas费用
- gas_split: Agent承担的份额
- reward: 原始奖励
- actual_reward: 扣除Gas后的实际奖励
- transactions: 所有交易的详细列表

### 4. 数据库迁移

创建了Alembic迁移脚本：
- 文件: alembic/versions/add_gas_fee_fields.py
- 添加gas_used、gas_cost、gas_split字段

### 5. 测试

#### test_gas_fee_sharing.py
测试Gas计算核心功能：
- 获取交易Gas使用情况
- 计算50%分担
- 处理奇数Gas费用
- 计算多个交易的总Gas
- 异常处理

#### test_gas_api.py
测试API端点：
- Gas信息查询
- 任务完成时的Gas计算
- 各种Gas费用场景
- 权限验证

## Gas费用分担流程

1. **任务发布**: 发布者支付Gas（publish交易）
2. **任务接受**: Agent支付Gas（accept交易）
3. **任务提交**: Agent支付Gas（submit交易）
4. **任务完成**:
   - 发布者支付Gas（complete交易）
   - 系统计算所有交易的总Gas费用
   - 从奖励中扣除50%作为Agent的Gas份额
   - Agent实际获得: reward - gas_split

## 使用示例

### 查询任务Gas信息
```bash
GET /api/tasks/1/gas
```

响应：
```json
{
  "task_id": 1,
  "gas_used": 225000,
  "gas_cost": 4500000000000000,
  "gas_split": 2250000000000000,
  "reward": 10000000000000000,
  "actual_reward": 7750000000000000,
  "transactions": [
    {
      "type": "publish",
      "tx_hash": "0xabc...",
      "description": "Task published by publisher"
    },
    ...
  ]
}
```

### 完成任务（自动计算Gas）
```bash
POST /api/tasks/1/complete
Authorization: Bearer <token>
```

响应包含gas_used、gas_cost、gas_split字段。

## 注意事项

1. **Gas费用可能超过奖励**: 在高Gas价格或低奖励的情况下，Agent的实际收益可能为负。建议在生产环境中添加验证。

2. **交易失败处理**: 如果某些交易未上链，对应的tx_hash为None，系统会自动跳过。

3. **精度处理**: 使用整数除法计算50%，奇数金额时Agent承担的略少。

4. **异步计算**: Gas计算在任务完成时进行，需要等待所有交易确认。

## 依赖更新

在requirements.txt中添加：
```
web3>=6.0.0
```

## 数据库迁移

运行迁移添加新字段：
```bash
alembic upgrade head
```

## 测试运行

```bash
# 安装依赖
pip install web3>=6.0.0

# 运行测试
pytest tests/test_gas_fee_sharing.py -v
pytest tests/test_gas_api.py -v
```
