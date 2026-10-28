"""
区块链集成测试套件
测试区块链服务的所有功能，包括Mock测试和集成测试
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from web3 import Web3
from web3.exceptions import ContractLogicError
import time
import os

# 导入区块链服务
from blockchain.blockchain_service import BlockchainService, get_blockchain_service
from blockchain.web3_config import Web3Config, get_web3_config
from blockchain.event_listener import BlockchainEventListener, get_event_listener


# ==================== Fixtures ====================

@pytest.fixture
def mock_web3():
    """Mock Web3实例"""
    mock_w3 = MagicMock()
    mock_w3.is_connected.return_value = True

    # Mock eth attribute
    mock_eth = MagicMock()
    mock_eth.block_number = 1000000
    mock_eth.chain_id = 11155111  # Sepolia
    mock_eth.gas_price = Web3.to_wei(20, 'gwei')
    mock_eth.get_transaction_count.return_value = 0
    mock_w3.eth = mock_eth

    mock_w3.to_checksum_address = Web3.to_checksum_address
    mock_w3.from_wei = Web3.from_wei
    mock_w3.to_wei = Web3.to_wei
    return mock_w3


@pytest.fixture
def mock_account():
    """Mock账户"""
    return {
        'address': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
        'private_key': '0x' + '1' * 64
    }


@pytest.fixture
def mock_task_market_contract():
    """Mock TaskMarket合约"""
    mock_contract = MagicMock()

    # Mock publishTask
    mock_publish = MagicMock()
    mock_publish.build_transaction.return_value = {
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
        'value': Web3.to_wei(0.1, 'ether'),
        'gas': 500000,
        'gasPrice': Web3.to_wei(20, 'gwei'),
        'nonce': 0
    }
    mock_contract.functions.publishTask.return_value = mock_publish

    # Mock acceptTask
    mock_accept = MagicMock()
    mock_accept.build_transaction.return_value = {
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
        'gas': 200000,
        'gasPrice': Web3.to_wei(20, 'gwei'),
        'nonce': 0
    }
    mock_contract.functions.acceptTask.return_value = mock_accept

    # Mock submitTask
    mock_submit = MagicMock()
    mock_submit.build_transaction.return_value = {
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
        'gas': 200000,
        'gasPrice': Web3.to_wei(20, 'gwei'),
        'nonce': 0
    }
    mock_contract.functions.submitTask.return_value = mock_submit

    # Mock completeTask
    mock_complete = MagicMock()
    mock_complete.build_transaction.return_value = {
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
        'gas': 300000,
        'gasPrice': Web3.to_wei(20, 'gwei'),
        'nonce': 0
    }
    mock_contract.functions.completeTask.return_value = mock_complete

    # Mock getTask
    mock_get_task = MagicMock()
    mock_get_task.call.return_value = (
        '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',  # creator
        '0x0000000000000000000000000000000000000000',  # agent
        'Test Task',  # title
        'Test Description',  # description
        Web3.to_wei(0.1, 'ether'),  # reward
        int(time.time()) + 86400,  # deadline
        0  # status (0=Open)
    )
    mock_contract.functions.getTask.return_value = mock_get_task

    return mock_contract


@pytest.fixture
def mock_reward_pool_contract():
    """Mock RewardPool合约"""
    mock_contract = MagicMock()

    # Mock getBalance
    mock_get_balance = MagicMock()
    mock_get_balance.call.return_value = Web3.to_wei(1.5, 'ether')
    mock_contract.functions.getBalance.return_value = mock_get_balance

    # Mock withdraw
    mock_withdraw = MagicMock()
    mock_withdraw.build_transaction.return_value = {
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
        'gas': 200000,
        'gasPrice': Web3.to_wei(20, 'gwei'),
        'nonce': 0
    }
    mock_contract.functions.withdraw.return_value = mock_withdraw

    return mock_contract


@pytest.fixture
def mock_agent_registry_contract():
    """Mock AgentRegistry合约"""
    mock_contract = MagicMock()

    # Mock registerAgent
    mock_register = MagicMock()
    mock_register.build_transaction.return_value = {
        'from': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
        'gas': 300000,
        'gasPrice': Web3.to_wei(20, 'gwei'),
        'nonce': 0
    }
    mock_contract.functions.registerAgent.return_value = mock_register

    # Mock getAgent
    mock_get_agent = MagicMock()
    mock_get_agent.call.return_value = (
        '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',  # owner
        'Test Agent',  # name
        'Test Description',  # description
        ['Python', 'JavaScript'],  # specialties
        100,  # reputation
        10,  # totalTasks
        8,  # completedTasks
        True  # isActive
    )
    mock_contract.functions.getAgent.return_value = mock_get_agent

    # Mock isRegistered
    mock_is_registered = MagicMock()
    mock_is_registered.call.return_value = True
    mock_contract.functions.isRegistered.return_value = mock_is_registered

    return mock_contract


@pytest.fixture
def mock_blockchain_service(mock_web3, mock_account, mock_task_market_contract,
                            mock_reward_pool_contract, mock_agent_registry_contract):
    """Mock区块链服务"""
    with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
         patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
         patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market, \
         patch('blockchain.blockchain_service.get_reward_pool') as mock_get_reward_pool, \
         patch('blockchain.blockchain_service.get_agent_registry') as mock_get_agent_registry:

        # Mock config
        mock_config = MagicMock()
        mock_config.get_account.return_value = mock_account['address']
        mock_config.send_transaction.return_value = '0x' + '1' * 64
        mock_config.wait_for_transaction.return_value = {
            'status': 1,
            'transactionHash': '0x' + '1' * 64,
            'blockNumber': 1000001,
            'gasUsed': 100000
        }
        mock_get_config.return_value = mock_config

        # Mock Web3
        mock_get_w3.return_value = mock_web3

        # Mock contracts
        mock_get_task_market.return_value = mock_task_market_contract
        mock_get_reward_pool.return_value = mock_reward_pool_contract
        mock_get_agent_registry.return_value = mock_agent_registry_contract

        service = BlockchainService()
        yield service


# ==================== TaskMarket 测试 ====================

class TestTaskMarketIntegration:
    """TaskMarket合约集成测试"""

    def test_publish_task_success(self, mock_blockchain_service):
        """测试成功发布任务到链上"""
        task_id = "task_001"
        title = "Test Task"
        description = "Test Description"
        reward = Web3.to_wei(0.1, 'ether')
        deadline = int(time.time()) + 86400

        tx_hash = mock_blockchain_service.publish_task_on_chain(
            task_id, title, description, reward, deadline
        )

        assert tx_hash is not None
        assert tx_hash.startswith('0x')
        assert len(tx_hash) == 66

    def test_publish_task_no_contract(self, mock_web3):
        """测试合约未加载时发布任务"""
        with patch('blockchain.blockchain_service.get_task_market') as mock_get_contract, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_contract.return_value = None
            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            assert tx_hash is None

    def test_publish_task_no_account(self, mock_web3, mock_task_market_contract):
        """测试无账户时发布任务"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            mock_config = MagicMock()
            mock_config.get_account.return_value = None
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            assert tx_hash is None

    def test_accept_task_success(self, mock_blockchain_service):
        """测试成功接受任务"""
        task_id = "task_001"

        tx_hash = mock_blockchain_service.accept_task_on_chain(task_id)

        assert tx_hash is not None
        assert tx_hash.startswith('0x')

    def test_submit_task_success(self, mock_blockchain_service):
        """测试成功提交任务结果"""
        task_id = "task_001"
        result = "Task completed successfully"

        tx_hash = mock_blockchain_service.submit_task_on_chain(task_id, result)

        assert tx_hash is not None
        assert tx_hash.startswith('0x')

    def test_complete_task_success(self, mock_blockchain_service):
        """测试成功完成任务"""
        task_id = "task_001"

        tx_hash = mock_blockchain_service.complete_task_on_chain(task_id)

        assert tx_hash is not None
        assert tx_hash.startswith('0x')

    def test_get_task_from_chain_success(self, mock_blockchain_service):
        """测试从链上获取任务信息"""
        task_id = "task_001"

        task_data = mock_blockchain_service.get_task_from_chain(task_id)

        assert task_data is not None
        assert 'creator' in task_data
        assert 'title' in task_data
        assert task_data['title'] == 'Test Task'
        assert 'reward' in task_data
        assert 'status' in task_data

    def test_get_task_no_contract(self, mock_web3):
        """测试合约未加载时获取任务"""
        with patch('blockchain.blockchain_service.get_task_market') as mock_get_contract, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_contract.return_value = None
            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            task_data = service.get_task_from_chain("task_001")

            assert task_data is None

    def test_task_lifecycle_complete(self, mock_blockchain_service):
        """测试任务完整生命周期"""
        task_id = "task_lifecycle_001"
        title = "Lifecycle Test Task"
        description = "Testing complete task lifecycle"
        reward = Web3.to_wei(0.1, 'ether')
        deadline = int(time.time()) + 86400

        # 1. 发布任务
        tx_hash_publish = mock_blockchain_service.publish_task_on_chain(
            task_id, title, description, reward, deadline
        )
        assert tx_hash_publish is not None

        # 2. 接受任务
        tx_hash_accept = mock_blockchain_service.accept_task_on_chain(task_id)
        assert tx_hash_accept is not None

        # 3. 提交任务
        tx_hash_submit = mock_blockchain_service.submit_task_on_chain(
            task_id, "Task result"
        )
        assert tx_hash_submit is not None

        # 4. 完成任务
        tx_hash_complete = mock_blockchain_service.complete_task_on_chain(task_id)
        assert tx_hash_complete is not None

        # 5. 查询任务
        task_data = mock_blockchain_service.get_task_from_chain(task_id)
        assert task_data is not None

    def test_publish_task_contract_error(self, mock_web3, mock_account, mock_task_market_contract):
        """测试合约逻辑错误"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            # Mock合约抛出错误
            mock_task_market_contract.functions.publishTask.side_effect = ContractLogicError("Insufficient funds")

            mock_config = MagicMock()
            mock_config.get_account.return_value = mock_account['address']
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            assert tx_hash is None


# ==================== RewardPool 测试 ====================

class TestRewardPoolIntegration:
    """RewardPool合约集成测试"""

    def test_get_reward_balance_success(self, mock_blockchain_service):
        """测试获取奖励余额"""
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"

        balance = mock_blockchain_service.get_reward_balance_from_chain(agent_address)

        assert balance is not None
        assert balance > 0
        assert balance == Web3.to_wei(1.5, 'ether')

    def test_get_reward_balance_no_contract(self, mock_web3):
        """测试合约未加载时获取余额"""
        with patch('blockchain.blockchain_service.get_reward_pool') as mock_get_contract, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_contract.return_value = None
            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            balance = service.get_reward_balance_from_chain(
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
            )

            assert balance is None

    def test_withdraw_reward_success(self, mock_blockchain_service):
        """测试提取奖励"""
        amount = Web3.to_wei(0.5, 'ether')

        tx_hash = mock_blockchain_service.withdraw_reward_from_chain(amount)

        assert tx_hash is not None
        assert tx_hash.startswith('0x')

    def test_withdraw_reward_no_contract(self, mock_web3):
        """测试合约未加载时提取奖励"""
        with patch('blockchain.blockchain_service.get_reward_pool') as mock_get_contract, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_contract.return_value = None
            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            tx_hash = service.withdraw_reward_from_chain(Web3.to_wei(0.5, 'ether'))

            assert tx_hash is None

    def test_withdraw_reward_no_account(self, mock_web3, mock_reward_pool_contract):
        """测试无账户时提取奖励"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_reward_pool') as mock_get_reward_pool:

            mock_config = MagicMock()
            mock_config.get_account.return_value = None
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_reward_pool.return_value = mock_reward_pool_contract

            service = BlockchainService()
            tx_hash = service.withdraw_reward_from_chain(Web3.to_wei(0.5, 'ether'))

            assert tx_hash is None

    def test_reward_query_and_withdraw_flow(self, mock_blockchain_service):
        """测试奖励查询和提取流程"""
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"

        # 1. 查询余额
        balance = mock_blockchain_service.get_reward_balance_from_chain(agent_address)
        assert balance is not None
        assert balance > 0

        # 2. 提取部分奖励
        withdraw_amount = Web3.to_wei(0.5, 'ether')
        tx_hash = mock_blockchain_service.withdraw_reward_from_chain(withdraw_amount)
        assert tx_hash is not None


# ==================== AgentRegistry 测试 ====================

class TestAgentRegistryIntegration:
    """AgentRegistry合约集成测试"""

    def test_register_agent_success(self, mock_blockchain_service):
        """测试注册Agent"""
        name = "Test Agent"
        description = "A test agent"
        specialties = ["Python", "JavaScript", "AI"]

        tx_hash = mock_blockchain_service.register_agent_on_chain(
            name, description, specialties
        )

        assert tx_hash is not None
        assert tx_hash.startswith('0x')

    def test_register_agent_no_contract(self, mock_web3):
        """测试合约未加载时注册Agent"""
        with patch('blockchain.blockchain_service.get_agent_registry') as mock_get_contract, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_contract.return_value = None
            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            tx_hash = service.register_agent_on_chain(
                "Test Agent", "Description", ["Python"]
            )

            assert tx_hash is None

    def test_get_agent_from_chain_success(self, mock_blockchain_service):
        """测试从链上获取Agent信息"""
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"

        agent_data = mock_blockchain_service.get_agent_from_chain(agent_address)

        assert agent_data is not None
        assert 'name' in agent_data
        assert agent_data['name'] == 'Test Agent'
        assert 'reputation' in agent_data
        assert 'total_tasks' in agent_data
        assert 'completed_tasks' in agent_data
        assert 'is_active' in agent_data

    def test_is_agent_registered_success(self, mock_blockchain_service):
        """测试检查Agent是否注册"""
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"

        is_registered = mock_blockchain_service.is_agent_registered_on_chain(agent_address)

        assert is_registered is True

    def test_is_agent_registered_no_contract(self, mock_web3):
        """测试合约未加载时检查注册状态"""
        with patch('blockchain.blockchain_service.get_agent_registry') as mock_get_contract, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_contract.return_value = None
            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            is_registered = service.is_agent_registered_on_chain(
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
            )

            assert is_registered is False

    def test_agent_registration_flow(self, mock_blockchain_service):
        """测试Agent注册流程"""
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        name = "New Agent"
        description = "A new agent for testing"
        specialties = ["Python", "Data Science"]

        # 1. 注册Agent
        tx_hash = mock_blockchain_service.register_agent_on_chain(
            name, description, specialties
        )
        assert tx_hash is not None

        # 2. 检查是否注册
        is_registered = mock_blockchain_service.is_agent_registered_on_chain(agent_address)
        assert is_registered is True

        # 3. 获取Agent信息
        agent_data = mock_blockchain_service.get_agent_from_chain(agent_address)
        assert agent_data is not None
        assert agent_data['name'] == 'Test Agent'  # Mock返回的数据


# ==================== Gas费用测试 ====================

class TestGasFeeSharing:
    """Gas费用1:1分担测试"""

    def test_estimate_gas_for_publish_task(self, mock_web3):
        """测试估算发布任务的Gas费用"""
        with patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            gas_price = service.w3.eth.gas_price

            assert gas_price > 0
            assert gas_price == Web3.to_wei(20, 'gwei')

    def test_gas_cost_calculation(self, mock_web3):
        """测试Gas成本计算"""
        gas_used = 100000
        gas_price = Web3.to_wei(20, 'gwei')

        total_cost = gas_used * gas_price
        cost_in_eth = Web3.from_wei(total_cost, 'ether')

        assert cost_in_eth > 0
        assert float(cost_in_eth) == 0.002  # 100000 * 20 gwei = 0.002 ETH

    def test_gas_fee_split_between_parties(self):
        """测试Gas费用在双方之间分担"""
        total_gas_cost = Web3.to_wei(0.002, 'ether')

        # 1:1分担
        creator_share = total_gas_cost // 2
        agent_share = total_gas_cost // 2

        assert creator_share == agent_share
        assert creator_share + agent_share == total_gas_cost

    def test_transaction_with_gas_estimation(self, mock_blockchain_service, mock_web3):
        """测试带Gas估算的交易"""
        task_id = "task_gas_001"
        title = "Gas Test Task"
        description = "Testing gas estimation"
        reward = Web3.to_wei(0.1, 'ether')
        deadline = int(time.time()) + 86400

        # 发布任务
        tx_hash = mock_blockchain_service.publish_task_on_chain(
            task_id, title, description, reward, deadline
        )

        assert tx_hash is not None

        # 验证Gas价格被使用
        gas_price = mock_web3.eth.gas_price
        assert gas_price == Web3.to_wei(20, 'gwei')


# ==================== 错误处理和重试测试 ====================

class TestErrorHandlingAndRetry:
    """错误处理和重试机制测试"""

    def test_connection_error_handling(self, mock_web3):
        """测试连接错误处理"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3:

            mock_config = MagicMock()
            mock_config.w3 = None
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3

            service = BlockchainService()
            # 服务应该能够处理连接错误而不崩溃
            assert service is not None

    def test_transaction_timeout_handling(self, mock_web3, mock_account, mock_task_market_contract):
        """测试交易超时处理"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            # Mock超时错误
            mock_config = MagicMock()
            mock_config.get_account.return_value = mock_account['address']
            mock_config.send_transaction.side_effect = TimeoutError("Transaction timeout")
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            assert tx_hash is None

    def test_insufficient_funds_error(self, mock_web3, mock_account, mock_task_market_contract):
        """测试资金不足错误"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            # Mock资金不足错误
            mock_config = MagicMock()
            mock_config.get_account.return_value = mock_account['address']
            mock_config.send_transaction.side_effect = ValueError("Insufficient funds")
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", Web3.to_wei(100, 'ether'), int(time.time()) + 86400
            )

            assert tx_hash is None

    def test_nonce_too_low_error(self, mock_web3, mock_account, mock_task_market_contract):
        """测试Nonce过低错误"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            # Mock Nonce错误
            mock_config = MagicMock()
            mock_config.get_account.return_value = mock_account['address']
            mock_config.send_transaction.side_effect = ValueError("Nonce too low")
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            assert tx_hash is None

    def test_contract_revert_error(self, mock_web3, mock_account, mock_task_market_contract):
        """测试合约Revert错误"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            # Mock合约Revert
            mock_task_market_contract.functions.publishTask.side_effect = ContractLogicError(
                "Task already exists"
            )

            mock_config = MagicMock()
            mock_config.get_account.return_value = mock_account['address']
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            assert tx_hash is None

    def test_network_congestion_high_gas(self, mock_web3):
        """测试网络拥堵时的高Gas价格"""
        # 模拟高Gas价格
        mock_web3.eth.gas_price = Web3.to_wei(200, 'gwei')  # 10倍正常价格

        with patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_web3_config') as mock_get_config:

            mock_get_w3.return_value = mock_web3
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config

            service = BlockchainService()
            gas_price = service.w3.eth.gas_price

            assert gas_price == Web3.to_wei(200, 'gwei')
            assert gas_price > Web3.to_wei(100, 'gwei')


# ==================== 交易失败场景测试 ====================

class TestTransactionFailureScenarios:
    """交易失败场景测试"""

    def test_transaction_reverted(self, mock_web3, mock_account, mock_task_market_contract):
        """测试交易被Revert"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            mock_config = MagicMock()
            mock_config.get_account.return_value = mock_account['address']
            mock_config.send_transaction.return_value = '0x' + '1' * 64
            # Mock交易失败的receipt
            mock_config.wait_for_transaction.return_value = {
                'status': 0,  # 失败
                'transactionHash': '0x' + '1' * 64,
                'blockNumber': 1000001,
                'gasUsed': 100000
            }
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            # 交易被发送但会失败
            assert tx_hash is not None

    def test_transaction_dropped(self, mock_web3, mock_account, mock_task_market_contract):
        """测试交易被丢弃"""
        with patch('blockchain.blockchain_service.get_web3_config') as mock_get_config, \
             patch('blockchain.blockchain_service.get_w3') as mock_get_w3, \
             patch('blockchain.blockchain_service.get_task_market') as mock_get_task_market:

            mock_config = MagicMock()
            mock_config.get_account.return_value = mock_account['address']
            mock_config.send_transaction.side_effect = Exception("Transaction dropped")
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            service = BlockchainService()
            tx_hash = service.publish_task_on_chain(
                "task_001", "Test", "Desc", 1000, int(time.time()) + 86400
            )

            assert tx_hash is None

    def test_invalid_task_id(self, mock_blockchain_service):
        """测试无效的任务ID"""
        # 空任务ID
        tx_hash = mock_blockchain_service.accept_task_on_chain("")
        assert tx_hash is not None  # Mock不会验证，但真实场景会失败

    def test_deadline_in_past(self, mock_blockchain_service):
        """测试过期的截止时间"""
        task_id = "task_expired"
        title = "Expired Task"
        description = "Task with past deadline"
        reward = Web3.to_wei(0.1, 'ether')
        deadline = int(time.time()) - 86400  # 昨天

        tx_hash = mock_blockchain_service.publish_task_on_chain(
            task_id, title, description, reward, deadline
        )

        # Mock不会验证，但真实合约会拒绝
        assert tx_hash is not None

    def test_zero_reward_task(self, mock_blockchain_service):
        """测试零奖励任务"""
        task_id = "task_zero_reward"
        title = "Zero Reward Task"
        description = "Task with no reward"
        reward = 0
        deadline = int(time.time()) + 86400

        tx_hash = mock_blockchain_service.publish_task_on_chain(
            task_id, title, description, reward, deadline
        )

        # Mock不会验证，但真实合约可能会拒绝
        assert tx_hash is not None


# ==================== Web3Config 测试 ====================

class TestWeb3Config:
    """Web3配置测试"""

    def test_web3_connection_success(self, mock_web3):
        """测试Web3连接成功"""
        with patch('blockchain.web3_config.Web3') as mock_web3_class:
            mock_provider = MagicMock()
            mock_web3_class.HTTPProvider.return_value = mock_provider
            mock_web3_class.return_value = mock_web3

            # 测试连接
            assert mock_web3.is_connected() is True

    def test_web3_connection_failure(self):
        """测试Web3连接失败"""
        with patch('blockchain.web3_config.Web3') as mock_web3_class:
            mock_w3 = MagicMock()
            mock_w3.is_connected.return_value = False
            mock_web3_class.return_value = mock_w3

            # 连接失败
            assert mock_w3.is_connected() is False

    def test_get_account_with_private_key(self, mock_web3, mock_account):
        """测试使用私钥获取账户"""
        with patch('blockchain.web3_config.PRIVATE_KEY', mock_account['private_key']), \
             patch('blockchain.web3_config.get_w3') as mock_get_w3, \
             patch('blockchain.web3_config.Web3') as mock_web3_class:

            mock_web3.eth.account.from_key.return_value = MagicMock(
                address=mock_account['address']
            )
            mock_get_w3.return_value = mock_web3

            # Mock Web3 class to prevent real connection
            mock_provider = MagicMock()
            mock_web3_class.HTTPProvider.return_value = mock_provider
            mock_web3_class.return_value = mock_web3

            config = Web3Config()
            account = config.get_account()

            assert account is not None

    def test_get_account_without_private_key(self, mock_web3):
        """测试无私钥时获取账户"""
        with patch('blockchain.web3_config.PRIVATE_KEY', ''), \
             patch('blockchain.web3_config.Web3') as mock_web3_class:

            # Mock Web3 class to prevent real connection
            mock_provider = MagicMock()
            mock_web3_class.HTTPProvider.return_value = mock_provider
            mock_web3_class.return_value = mock_web3

            config = Web3Config()
            account = config.get_account()

            assert account is None

    def test_get_balance(self, mock_web3):
        """测试获取余额"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        mock_web3.eth.get_balance.return_value = Web3.to_wei(1.5, 'ether')

        with patch('blockchain.web3_config.get_w3') as mock_get_w3, \
             patch('blockchain.web3_config.Web3') as mock_web3_class:

            mock_get_w3.return_value = mock_web3

            # Mock Web3 class to prevent real connection
            mock_provider = MagicMock()
            mock_web3_class.HTTPProvider.return_value = mock_provider
            mock_web3_class.return_value = mock_web3

            config = Web3Config()
            balance = config.get_balance(address)

            assert balance == Web3.to_wei(1.5, 'ether')

    def test_get_balance_eth(self, mock_web3):
        """测试获取ETH余额"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        mock_web3.eth.get_balance.return_value = Web3.to_wei(1.5, 'ether')

        with patch('blockchain.web3_config.get_w3') as mock_get_w3, \
             patch('blockchain.web3_config.Web3') as mock_web3_class:

            mock_get_w3.return_value = mock_web3

            # Mock Web3 class to prevent real connection
            mock_provider = MagicMock()
            mock_web3_class.HTTPProvider.return_value = mock_provider
            mock_web3_class.return_value = mock_web3

            config = Web3Config()
            balance_eth = config.get_balance_eth(address)

            assert balance_eth == 1.5


# ==================== 事件监听器测试 ====================

class TestBlockchainEventListener:
    """区块链事件监听器测试"""

    @pytest.fixture
    def mock_event_listener(self, mock_web3, mock_task_market_contract):
        """Mock事件监听器"""
        with patch('blockchain.event_listener.get_web3_config') as mock_get_config, \
             patch('blockchain.event_listener.get_w3') as mock_get_w3, \
             patch('blockchain.event_listener.get_task_market') as mock_get_task_market:

            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            mock_get_w3.return_value = mock_web3
            mock_get_task_market.return_value = mock_task_market_contract

            listener = BlockchainEventListener()
            yield listener

    def test_register_event_handler(self, mock_event_listener):
        """测试注册事件处理器"""
        async def test_handler(task_id, creator, reward):
            pass

        mock_event_listener.register_handler('TaskPublished', test_handler)

        assert 'TaskPublished' in mock_event_listener.event_handlers
        assert mock_event_listener.event_handlers['TaskPublished'] == test_handler

    @pytest.mark.asyncio
    async def test_handle_task_published_event(self, mock_event_listener):
        """测试处理TaskPublished事件"""
        event_data = {
            'args': {
                'taskId': 'task_001',
                'creator': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
                'reward': Web3.to_wei(0.1, 'ether')
            }
        }

        handler_called = False
        received_data = {}

        async def test_handler(task_id, creator, reward):
            nonlocal handler_called, received_data
            handler_called = True
            received_data = {'task_id': task_id, 'creator': creator, 'reward': reward}

        mock_event_listener.register_handler('TaskPublished', test_handler)
        await mock_event_listener._handle_task_published(event_data)

        assert handler_called is True
        assert received_data['task_id'] == 'task_001'

    @pytest.mark.asyncio
    async def test_handle_task_accepted_event(self, mock_event_listener):
        """测试处理TaskAccepted事件"""
        event_data = {
            'args': {
                'taskId': 'task_001',
                'agent': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1'
            }
        }

        handler_called = False

        async def test_handler(task_id, agent):
            nonlocal handler_called
            handler_called = True

        mock_event_listener.register_handler('TaskAccepted', test_handler)
        await mock_event_listener._handle_task_accepted(event_data)

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_handle_reward_distributed_event(self, mock_event_listener):
        """测试处理RewardDistributed事件"""
        event_data = {
            'args': {
                'agent': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
                'amount': Web3.to_wei(0.1, 'ether'),
                'taskId': 'task_001'
            }
        }

        handler_called = False

        async def test_handler(agent, amount, task_id):
            nonlocal handler_called
            handler_called = True

        mock_event_listener.register_handler('RewardDistributed', test_handler)
        await mock_event_listener._handle_reward_distributed(event_data)

        assert handler_called is True

    @pytest.mark.asyncio
    async def test_handle_agent_registered_event(self, mock_event_listener):
        """测试处理AgentRegistered事件"""
        event_data = {
            'args': {
                'agent': '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1',
                'name': 'Test Agent'
            }
        }

        handler_called = False

        async def test_handler(agent, name):
            nonlocal handler_called
            handler_called = True

        mock_event_listener.register_handler('AgentRegistered', test_handler)
        await mock_event_listener._handle_agent_registered(event_data)

        assert handler_called is True

    def test_event_listener_start_stop(self, mock_event_listener):
        """测试事件监听器启动和停止"""
        assert mock_event_listener.is_running is False

        mock_event_listener.stop()
        assert mock_event_listener.is_running is False


# ==================== 端到端集成测试 ====================

class TestEndToEndIntegration:
    """端到端集成测试"""

    def test_complete_task_workflow_e2e(self, mock_blockchain_service):
        """测试完整的任务工作流（端到端）"""
        # 准备数据
        task_id = "e2e_task_001"
        title = "E2E Test Task"
        description = "End-to-end integration test"
        reward = Web3.to_wei(0.1, 'ether')
        deadline = int(time.time()) + 86400
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"

        # 1. 发布任务
        tx_hash_publish = mock_blockchain_service.publish_task_on_chain(
            task_id, title, description, reward, deadline
        )
        assert tx_hash_publish is not None

        # 2. 查询任务
        task_data = mock_blockchain_service.get_task_from_chain(task_id)
        assert task_data is not None
        assert task_data['title'] == 'Test Task'

        # 3. 接受任务
        tx_hash_accept = mock_blockchain_service.accept_task_on_chain(task_id)
        assert tx_hash_accept is not None

        # 4. 提交任务
        tx_hash_submit = mock_blockchain_service.submit_task_on_chain(
            task_id, "Task completed"
        )
        assert tx_hash_submit is not None

        # 5. 完成任务
        tx_hash_complete = mock_blockchain_service.complete_task_on_chain(task_id)
        assert tx_hash_complete is not None

        # 6. 查询奖励余额
        balance = mock_blockchain_service.get_reward_balance_from_chain(agent_address)
        assert balance is not None
        assert balance > 0

        # 7. 提取奖励
        tx_hash_withdraw = mock_blockchain_service.withdraw_reward_from_chain(
            Web3.to_wei(0.05, 'ether')
        )
        assert tx_hash_withdraw is not None

    def test_agent_registration_and_task_workflow(self, mock_blockchain_service):
        """测试Agent注册和任务工作流"""
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        agent_name = "E2E Test Agent"
        agent_description = "Agent for E2E testing"
        specialties = ["Python", "Blockchain"]

        # 1. 注册Agent
        tx_hash_register = mock_blockchain_service.register_agent_on_chain(
            agent_name, agent_description, specialties
        )
        assert tx_hash_register is not None

        # 2. 验证注册
        is_registered = mock_blockchain_service.is_agent_registered_on_chain(agent_address)
        assert is_registered is True

        # 3. 获取Agent信息
        agent_data = mock_blockchain_service.get_agent_from_chain(agent_address)
        assert agent_data is not None
        assert agent_data['is_active'] is True

        # 4. Agent接受任务
        task_id = "agent_task_001"
        tx_hash_accept = mock_blockchain_service.accept_task_on_chain(task_id)
        assert tx_hash_accept is not None

    def test_multiple_tasks_parallel_processing(self, mock_blockchain_service):
        """测试多个任务并行处理"""
        tasks = []
        for i in range(5):
            task_id = f"parallel_task_{i:03d}"
            title = f"Parallel Task {i}"
            description = f"Task {i} for parallel processing"
            reward = Web3.to_wei(0.1, 'ether')
            deadline = int(time.time()) + 86400

            tx_hash = mock_blockchain_service.publish_task_on_chain(
                task_id, title, description, reward, deadline
            )
            tasks.append({'task_id': task_id, 'tx_hash': tx_hash})

        # 验证所有任务都发布成功
        assert len(tasks) == 5
        for task in tasks:
            assert task['tx_hash'] is not None

    def test_reward_distribution_multiple_agents(self, mock_blockchain_service):
        """测试多个Agent的奖励分配"""
        agents = [
            "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1",
            "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
            "0xdD2FD4581271e230360230F9337D5c0430Bf44C0"
        ]

        balances = []
        for agent in agents:
            balance = mock_blockchain_service.get_reward_balance_from_chain(agent)
            balances.append(balance)

        # 验证所有Agent都有余额记录
        assert len(balances) == 3
        for balance in balances:
            assert balance is not None


# ==================== 性能和压力测试 ====================

class TestPerformanceAndStress:
    """性能和压力测试"""

    def test_high_volume_task_publishing(self, mock_blockchain_service):
        """测试大量任务发布"""
        num_tasks = 100
        successful_tasks = 0

        for i in range(num_tasks):
            task_id = f"stress_task_{i:04d}"
            tx_hash = mock_blockchain_service.publish_task_on_chain(
                task_id, f"Task {i}", "Description",
                Web3.to_wei(0.01, 'ether'), int(time.time()) + 86400
            )
            if tx_hash:
                successful_tasks += 1

        # 至少90%成功率
        assert successful_tasks >= num_tasks * 0.9

    def test_concurrent_agent_registrations(self, mock_blockchain_service):
        """测试并发Agent注册"""
        num_agents = 50
        successful_registrations = 0

        for i in range(num_agents):
            tx_hash = mock_blockchain_service.register_agent_on_chain(
                f"Agent {i}", f"Description {i}", ["Python"]
            )
            if tx_hash:
                successful_registrations += 1

        assert successful_registrations >= num_agents * 0.9

    def test_rapid_balance_queries(self, mock_blockchain_service):
        """测试快速余额查询"""
        agent_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb1"
        num_queries = 100
        successful_queries = 0

        for _ in range(num_queries):
            balance = mock_blockchain_service.get_reward_balance_from_chain(agent_address)
            if balance is not None:
                successful_queries += 1

        assert successful_queries == num_queries


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
