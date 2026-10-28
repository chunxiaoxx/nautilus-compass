# 区块链集成测试文档

## 概述

本文档描述了区块链集成测试套件的使用方法和测试内容。

## 测试文件

- `test_blockchain_integration.py` - 完整的区块链集成测试套件（61个测试用例）

## 安装依赖

在运行测试之前，需要安装区块链相关依赖：

```bash
pip install web3>=6.0.0 eth-account>=0.9.0
```

或者安装完整依赖：

```bash
pip install -r requirements.txt
```

## 测试内容

### 1. TaskMarket 合约测试 (10个测试)
- 任务发布到链上
- 任务接受
- 任务提交
- 任务完成
- 任务查询
- 完整生命周期测试
- 错误处理（无合约、无账户、合约错误）

### 2. RewardPool 合约测试 (6个测试)
- 奖励余额查询
- 奖励提取
- 奖励查询和提取流程
- 错误处理

### 3. AgentRegistry 合约测试 (5个测试)
- Agent注册
- Agent信息查询
- 注册状态检查
- Agent注册流程
- 错误处理

### 4. Gas费用测试 (4个测试)
- Gas费用估算
- Gas成本计算
- 1:1费用分担
- 带Gas估算的交易

### 5. 错误处理和重试测试 (7个测试)
- 连接错误处理
- 交易超时
- 资金不足错误
- Nonce错误
- 合约Revert错误
- 网络拥堵处理

### 6. 交易失败场景测试 (5个测试)
- 交易被Revert
- 交易被丢弃
- 无效任务ID
- 过期截止时间
- 零奖励任务

### 7. Web3Config 测试 (5个测试)
- Web3连接成功/失败
- 账户管理
- 余额查询

### 8. 事件监听器测试 (6个测试)
- 事件处理器注册
- TaskPublished事件
- TaskAccepted事件
- RewardDistributed事件
- AgentRegistered事件
- 监听器启动/停止

### 9. 端到端集成测试 (4个测试)
- 完整任务工作流
- Agent注册和任务流程
- 多任务并行处理
- 多Agent奖励分配

### 10. 性能和压力测试 (3个测试)
- 大量任务发布（100个）
- 并发Agent注册（50个）
- 快速余额查询（100次）

## 运行测试

### 运行所有测试

```bash
pytest tests/test_blockchain_integration.py -v
```

### 运行特定测试类

```bash
# TaskMarket测试
pytest tests/test_blockchain_integration.py::TestTaskMarketIntegration -v

# RewardPool测试
pytest tests/test_blockchain_integration.py::TestRewardPoolIntegration -v

# AgentRegistry测试
pytest tests/test_blockchain_integration.py::TestAgentRegistryIntegration -v

# Gas费用测试
pytest tests/test_blockchain_integration.py::TestGasFeeSharing -v

# 错误处理测试
pytest tests/test_blockchain_integration.py::TestErrorHandlingAndRetry -v

# 端到端测试
pytest tests/test_blockchain_integration.py::TestEndToEndIntegration -v

# 性能测试
pytest tests/test_blockchain_integration.py::TestPerformanceAndStress -v
```

### 运行特定测试

```bash
pytest tests/test_blockchain_integration.py::TestTaskMarketIntegration::test_publish_task_success -v
```

### 运行Mock测试（不需要真实区块链）

```bash
pytest tests/test_blockchain_integration.py -v -k "not test_e2e"
```

### 运行端到端测试（需要测试网络）

```bash
# 需要配置环境变量
export SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/YOUR_PROJECT_ID"
export BLOCKCHAIN_PRIVATE_KEY="your_private_key"
export TASK_MARKET_ADDRESS="0x..."
export REWARD_POOL_ADDRESS="0x..."
export AGENT_REGISTRY_ADDRESS="0x..."

pytest tests/test_blockchain_integration.py -v -k "test_e2e"
```

## 环境变量配置

### Mock模式（默认）
不需要配置任何环境变量，所有测试使用Mock对象。

### 测试网络模式
需要配置以下环境变量：

```bash
# RPC节点URL
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
# 或使用Alchemy
ALCHEMY_API_KEY=your_alchemy_api_key

# 私钥（用于签名交易）
BLOCKCHAIN_PRIVATE_KEY=0x...

# 智能合约地址
TASK_MARKET_ADDRESS=0x...
REWARD_POOL_ADDRESS=0x...
AGENT_REGISTRY_ADDRESS=0x...
```

## CI/CD集成

测试已集成到CI/CD流程中：

### GitHub Actions配置

1. **Mock测试** - 在每次push和PR时运行
   - 不需要真实区块链连接
   - 快速验证代码逻辑

2. **测试网络测试** - 仅在main分支push时运行
   - 需要配置GitHub Secrets
   - 验证真实区块链交互

### 配置GitHub Secrets

在GitHub仓库设置中添加以下Secrets：

- `SEPOLIA_RPC_URL` - Sepolia测试网RPC URL
- `INFURA_PROJECT_ID` - Infura项目ID
- `TEST_PRIVATE_KEY` - 测试账户私钥
- `TASK_MARKET_ADDRESS` - TaskMarket合约地址
- `REWARD_POOL_ADDRESS` - RewardPool合约地址
- `AGENT_REGISTRY_ADDRESS` - AgentRegistry合约地址

## 测试覆盖率

目标测试覆盖率：90%以上

查看覆盖率报告：

```bash
pytest tests/test_blockchain_integration.py --cov=blockchain --cov-report=html
```

## 注意事项

1. **Mock测试** - 适合快速开发和CI/CD
   - 不消耗真实Gas
   - 运行速度快
   - 不验证真实合约逻辑

2. **测试网络测试** - 适合集成验证
   - 需要测试网ETH
   - 运行速度较慢
   - 验证真实合约交互

3. **私钥安全**
   - 永远不要在代码中硬编码私钥
   - 使用环境变量或密钥管理服务
   - 测试账户应该只包含测试网ETH

4. **Gas费用**
   - 测试网络测试会消耗测试网ETH
   - 从水龙头获取测试ETH：https://sepoliafaucet.com/

## 故障排查

### 问题：ModuleNotFoundError: No module named 'web3'
解决：安装web3依赖
```bash
pip install web3>=6.0.0 eth-account>=0.9.0
```

### 问题：连接超时
解决：检查RPC URL配置，确保网络连接正常

### 问题：交易失败
解决：
1. 检查账户余额是否充足
2. 检查合约地址是否正确
3. 检查Gas价格设置

### 问题：Nonce错误
解决：等待之前的交易确认，或手动重置Nonce

## 测试统计

- **总测试数量**: 61个
- **测试类数量**: 10个
- **代码行数**: 1161行
- **预计运行时间**:
  - Mock模式: ~30秒
  - 测试网络模式: ~5-10分钟

## 贡献指南

添加新测试时：

1. 遵循现有测试结构
2. 使用描述性的测试名称
3. 添加详细的文档字符串
4. 确保测试独立性
5. 使用适当的Mock对象
6. 添加断言验证结果

## 相关文档

- [Web3.py文档](https://web3py.readthedocs.io/)
- [Pytest文档](https://docs.pytest.org/)
- [Sepolia测试网](https://sepolia.dev/)
