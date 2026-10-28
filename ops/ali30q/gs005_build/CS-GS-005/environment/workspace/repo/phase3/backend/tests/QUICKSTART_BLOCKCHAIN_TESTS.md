# 区块链集成测试快速开始指南

## 快速开始

### 1. 安装依赖

```bash
pip install web3>=6.0.0 eth-account>=0.9.0
```

### 2. 运行测试

#### Windows用户
```bash
run_blockchain_tests.bat
```

#### Linux/Mac用户
```bash
chmod +x run_blockchain_tests.sh
./run_blockchain_tests.sh
```

#### 直接使用pytest
```bash
# 运行所有Mock测试（推荐首次运行）
pytest tests/test_blockchain_integration.py -v -k "not test_e2e"

# 运行所有测试
pytest tests/test_blockchain_integration.py -v

# 运行特定测试类
pytest tests/test_blockchain_integration.py::TestTaskMarketIntegration -v
```

## 测试内容概览

| 测试类 | 测试数 | 说明 |
|--------|--------|------|
| TestTaskMarketIntegration | 10 | TaskMarket合约测试 |
| TestRewardPoolIntegration | 6 | RewardPool合约测试 |
| TestAgentRegistryIntegration | 5 | AgentRegistry合约测试 |
| TestGasFeeSharing | 4 | Gas费用1:1分担测试 |
| TestErrorHandlingAndRetry | 7 | 错误处理和重试测试 |
| TestTransactionFailureScenarios | 5 | 交易失败场景测试 |
| TestWeb3Config | 5 | Web3配置测试 |
| TestBlockchainEventListener | 6 | 事件监听器测试 |
| TestEndToEndIntegration | 4 | 端到端集成测试 |
| TestPerformanceAndStress | 3 | 性能和压力测试 |
| **总计** | **61** | **完整测试覆盖** |

## 文件结构

```
backend/
├── tests/
│   ├── test_blockchain_integration.py          # 主测试文件 (1161行)
│   ├── conftest.py                             # Pytest配置
│   ├── README_BLOCKCHAIN_TESTS.md              # 详细文档
│   ├── BLOCKCHAIN_TEST_COMPLETION_REPORT.md    # 完成报告
│   └── QUICKSTART_BLOCKCHAIN_TESTS.md          # 本文件
├── .github/workflows/
│   └── ci-cd.yml                               # CI/CD配置（已更新）
├── run_blockchain_tests.sh                     # Linux/Mac运行脚本
└── run_blockchain_tests.bat                    # Windows运行脚本
```

## 常用命令

```bash
# 查看所有测试
pytest tests/test_blockchain_integration.py --collect-only

# 运行Mock测试（快速）
pytest tests/test_blockchain_integration.py -v -k "not test_e2e"

# 运行端到端测试（需要配置环境变量）
pytest tests/test_blockchain_integration.py -v -k "test_e2e"

# 生成覆盖率报告
pytest tests/test_blockchain_integration.py --cov=blockchain --cov-report=html

# 运行特定测试
pytest tests/test_blockchain_integration.py::TestTaskMarketIntegration::test_publish_task_success -v
```

## 环境变量（可选，用于测试网络测试）

```bash
# Linux/Mac
export SEPOLIA_RPC_URL="https://sepolia.infura.io/v3/YOUR_PROJECT_ID"
export BLOCKCHAIN_PRIVATE_KEY="0x..."
export TASK_MARKET_ADDRESS="0x..."
export REWARD_POOL_ADDRESS="0x..."
export AGENT_REGISTRY_ADDRESS="0x..."

# Windows
set SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_PROJECT_ID
set BLOCKCHAIN_PRIVATE_KEY=0x...
set TASK_MARKET_ADDRESS=0x...
set REWARD_POOL_ADDRESS=0x...
set AGENT_REGISTRY_ADDRESS=0x...
```

## 故障排查

### 问题：ModuleNotFoundError: No module named 'web3'
**解决**：
```bash
pip install web3>=6.0.0 eth-account>=0.9.0
```

### 问题：测试失败
**解决**：
1. 确保已安装所有依赖
2. 首次运行使用Mock测试：`pytest tests/test_blockchain_integration.py -v -k "not test_e2e"`
3. 查看详细错误信息：`pytest tests/test_blockchain_integration.py -v --tb=long`

### 问题：需要真实区块链测试
**解决**：
1. 配置环境变量（见上方）
2. 获取测试网ETH：https://sepoliafaucet.com/
3. 运行端到端测试：`pytest tests/test_blockchain_integration.py -v -k "test_e2e"`

## 更多信息

详细文档请查看：`tests/README_BLOCKCHAIN_TESTS.md`

完成报告请查看：`tests/BLOCKCHAIN_TEST_COMPLETION_REPORT.md`
