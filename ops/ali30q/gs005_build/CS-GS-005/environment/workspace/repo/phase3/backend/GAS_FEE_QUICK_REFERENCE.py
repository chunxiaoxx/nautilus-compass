"""
Gas费用分担机制 - 快速参考
"""

# ============================================================================
# API使用示例
# ============================================================================

# 1. 查询任务的Gas费用信息
GET /api/tasks/{task_id}/gas

# 响应示例：
{
  "task_id": 1,
  "gas_used": 225000,                    # 总Gas使用量
  "gas_cost": 4500000000000000,          # 总Gas费用 (0.0045 ETH)
  "gas_split": 2250000000000000,         # Agent承担50% (0.00225 ETH)
  "reward": 10000000000000000,           # 原始奖励 (0.01 ETH)
  "actual_reward": 7750000000000000,     # 实际奖励 (0.00775 ETH)
  "transactions": [
    {
      "type": "publish",
      "tx_hash": "0xabc...",
      "description": "Task published by publisher"
    },
    {
      "type": "accept",
      "tx_hash": "0xdef...",
      "description": "Task accepted by agent"
    },
    {
      "type": "submit",
      "tx_hash": "0xghi...",
      "description": "Result submitted by agent"
    },
    {
      "type": "complete",
      "tx_hash": "0xjkl...",
      "description": "Task completed by publisher"
    }
  ]
}

# 2. 完成任务（自动计算Gas）
POST /api/tasks/{task_id}/complete
Authorization: Bearer <jwt_token>

# 响应包含gas_used, gas_cost, gas_split字段


# ============================================================================
# 代码使用示例
# ============================================================================

# 在Python代码中使用BlockchainService

from blockchain import get_blockchain_service

blockchain = get_blockchain_service()

# 获取单个交易的Gas信息
gas_info = blockchain.get_transaction_gas_used('0xabc123...')
# 返回: {'gas_used': 100000, 'gas_price': 20000000000, 'gas_cost': 2000000000000000}

# 计算50%分担
gas_split = blockchain.calculate_gas_split(total_gas_cost=4500000000000000)
# 返回: 2250000000000000

# 计算任务所有交易的总Gas
tx_hashes = [
    task.blockchain_tx_hash,
    task.blockchain_accept_tx,
    task.blockchain_submit_tx,
    task.blockchain_complete_tx
]
gas_info = blockchain.calculate_task_total_gas(tx_hashes)
# 返回: {
#   'total_gas_used': 225000,
#   'total_gas_cost': 4500000000000000,
#   'gas_split': 2250000000000000
# }


# ============================================================================
# 数据库字段
# ============================================================================

# Task表新增字段：
# - gas_used (BigInteger): 总Gas使用量
# - gas_cost (BigInteger): 总Gas费用（Wei）
# - gas_split (BigInteger): Agent承担的Gas费用（50%）


# ============================================================================
# Gas费用分担流程
# ============================================================================

"""
任务生命周期中的Gas费用：

1. 发布任务 (Publisher支付)
   - 交易: publishTask()
   - Gas: ~500,000
   - 支付方: Publisher

2. 接受任务 (Agent支付)
   - 交易: acceptTask()
   - Gas: ~200,000
   - 支付方: Agent

3. 提交结果 (Agent支付)
   - 交易: submitTask()
   - Gas: ~200,000
   - 支付方: Agent

4. 完成任务 (Publisher支付)
   - 交易: completeTask()
   - Gas: ~300,000
   - 支付方: Publisher

5. Gas费用结算
   - 总Gas费用 = 所有交易的Gas费用总和
   - Agent承担 = 总Gas费用 / 2
   - 实际奖励 = 原始奖励 - Agent承担的Gas费用
"""


# ============================================================================
# 部署步骤
# ============================================================================

"""
1. 安装依赖
   pip install web3>=6.0.0

2. 运行数据库迁移
   cd C:\Users\chunx\Projects\nautilus-core\phase3\backend
   alembic upgrade head

3. 重启服务
   uvicorn main:app --reload

4. 运行测试
   pytest tests/test_gas_fee_sharing.py -v
   pytest tests/test_gas_api.py -v
"""


# ============================================================================
# 注意事项
# ============================================================================

"""
1. Gas费用可能超过奖励
   - 在高Gas价格或低奖励的情况下，Agent的实际收益可能为负
   - 建议在任务发布时验证奖励是否足够覆盖预期Gas费用

2. 交易确认时间
   - Gas计算需要等待所有交易确认
   - 在任务完成时进行计算

3. 精度处理
   - 使用整数除法计算50%
   - 奇数金额时Agent承担的略少（向下取整）

4. 异常处理
   - 如果Gas计算失败，任务仍会标记为完成
   - 但gas_used, gas_cost, gas_split字段为None
   - 建议监控日志中的警告信息
"""


# ============================================================================
# 测试覆盖
# ============================================================================

"""
test_gas_fee_sharing.py:
- ✓ 获取交易Gas使用情况
- ✓ 计算50%分担
- ✓ 处理奇数Gas费用
- ✓ 计算多个交易的总Gas
- ✓ 处理None交易哈希
- ✓ 异常处理

test_gas_api.py:
- ✓ 查询Gas信息端点
- ✓ 任务完成时的Gas计算
- ✓ 各种Gas费用场景
- ✓ 权限验证
- ✓ 高Gas低奖励场景
"""
