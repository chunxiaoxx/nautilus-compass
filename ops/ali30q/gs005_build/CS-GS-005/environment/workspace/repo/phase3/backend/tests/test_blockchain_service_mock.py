"""
区块链服务Mock测试 - 提升覆盖率
使用Mock对象测试区块链服务，避免真实区块链连接
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain.blockchain_service import BlockchainService


class TestBlockchainServiceInit:
    """区块链服务初始化测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_init_success(self, mock_get_web3):
        """测试成功初始化"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        assert service.w3 == mock_web3

    @patch('blockchain.blockchain_service.get_web3')
    def test_init_connection_failed(self, mock_get_web3):
        """测试连接失败"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = False
        mock_get_web3.return_value = mock_web3

        with pytest.raises(Exception):
            BlockchainService()


class TestPublishTask:
    """发布任务到链上测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_publish_task_success(self, mock_get_web3):
        """测试成功发布任务"""
        # Mock Web3
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        # Mock contract
        mock_contract = Mock()
        mock_tx_hash = b'0x' + b'1' * 64
        mock_contract.functions.publishTask.return_value.transact.return_value = mock_tx_hash

        service = BlockchainService()
        service.task_market_contract = mock_contract

        # 发布任务
        result = service.publish_task(
            task_id="task_123",
            description="Test task",
            reward=100,
            deadline=int(datetime.now(timezone.utc).timestamp()) + 86400
        )

        assert result == mock_tx_hash.hex()
        mock_contract.functions.publishTask.assert_called_once()

    @patch('blockchain.blockchain_service.get_web3')
    def test_publish_task_no_contract(self, mock_get_web3):
        """测试合约未初始化"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        service.task_market_contract = None

        with pytest.raises(Exception):
            service.publish_task("task_123", "Test", 100, 123456)

    @patch('blockchain.blockchain_service.get_web3')
    def test_publish_task_invalid_reward(self, mock_get_web3):
        """测试无效奖励金额"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.task_market_contract = mock_contract

        with pytest.raises(ValueError):
            service.publish_task("task_123", "Test", -100, 123456)

    @patch('blockchain.blockchain_service.get_web3')
    def test_publish_task_past_deadline(self, mock_get_web3):
        """测试过期的截止日期"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.task_market_contract = mock_contract

        past_timestamp = int(datetime.now(timezone.utc).timestamp()) - 86400

        with pytest.raises(ValueError):
            service.publish_task("task_123", "Test", 100, past_timestamp)

    @patch('blockchain.blockchain_service.get_web3')
    def test_publish_task_transaction_failed(self, mock_get_web3):
        """测试交易失败"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_contract.functions.publishTask.return_value.transact.side_effect = Exception("Transaction failed")
        service.task_market_contract = mock_contract

        with pytest.raises(Exception):
            service.publish_task("task_123", "Test", 100, 123456)


class TestAcceptTask:
    """接受任务测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_accept_task_success(self, mock_get_web3):
        """测试成功接受任务"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_tx_hash = b'0x' + b'2' * 64
        mock_contract.functions.acceptTask.return_value.transact.return_value = mock_tx_hash
        service.task_market_contract = mock_contract

        result = service.accept_task("task_123", "0x1234567890123456789012345678901234567890")

        assert result == mock_tx_hash.hex()
        mock_contract.functions.acceptTask.assert_called_once()

    @patch('blockchain.blockchain_service.get_web3')
    def test_accept_task_invalid_address(self, mock_get_web3):
        """测试无效的Agent地址"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.task_market_contract = mock_contract

        with pytest.raises(ValueError):
            service.accept_task("task_123", "invalid_address")


class TestSubmitTask:
    """提交任务测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_submit_task_success(self, mock_get_web3):
        """测试成功提交任务"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_tx_hash = b'0x' + b'3' * 64
        mock_contract.functions.submitTask.return_value.transact.return_value = mock_tx_hash
        service.task_market_contract = mock_contract

        result = service.submit_task("task_123", "https://github.com/example/pr/123")

        assert result == mock_tx_hash.hex()
        mock_contract.functions.submitTask.assert_called_once()

    @patch('blockchain.blockchain_service.get_web3')
    def test_submit_task_empty_proof(self, mock_get_web3):
        """测试空证明"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.task_market_contract = mock_contract

        with pytest.raises(ValueError):
            service.submit_task("task_123", "")


class TestCompleteTask:
    """完成任务测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_complete_task_success(self, mock_get_web3):
        """测试成功完成任务"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_tx_hash = b'0x' + b'4' * 64
        mock_contract.functions.completeTask.return_value.transact.return_value = mock_tx_hash
        service.task_market_contract = mock_contract

        result = service.complete_task("task_123")

        assert result == mock_tx_hash.hex()
        mock_contract.functions.completeTask.assert_called_once()


class TestGetTask:
    """获取任务信息测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_get_task_success(self, mock_get_web3):
        """测试成功获取任务"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()

        # Mock返回值
        mock_task_data = (
            "task_123",  # taskId
            "0x1234567890123456789012345678901234567890",  # creator
            "0xABCDEF1234567890123456789012345678901234",  # assignedAgent
            100,  # reward
            1234567890,  # deadline
            0  # status (0=Open)
        )
        mock_contract.functions.getTask.return_value.call.return_value = mock_task_data
        service.task_market_contract = mock_contract

        result = service.get_task("task_123")

        assert result["taskId"] == "task_123"
        assert result["reward"] == 100
        mock_contract.functions.getTask.assert_called_once_with("task_123")

    @patch('blockchain.blockchain_service.get_web3')
    def test_get_task_not_found(self, mock_get_web3):
        """测试任务不存在"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_contract.functions.getTask.return_value.call.side_effect = Exception("Task not found")
        service.task_market_contract = mock_contract

        with pytest.raises(Exception):
            service.get_task("nonexistent_task")


class TestRegisterAgent:
    """注册Agent测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_register_agent_success(self, mock_get_web3):
        """测试成功注册Agent"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_tx_hash = b'0x' + b'5' * 64
        mock_contract.functions.registerAgent.return_value.transact.return_value = mock_tx_hash
        service.agent_registry_contract = mock_contract

        result = service.register_agent(
            "TestAgent",
            "0x1234567890123456789012345678901234567890",
            ["capability1", "capability2"]
        )

        assert result == mock_tx_hash.hex()
        mock_contract.functions.registerAgent.assert_called_once()

    @patch('blockchain.blockchain_service.get_web3')
    def test_register_agent_empty_name(self, mock_get_web3):
        """测试空Agent名称"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.agent_registry_contract = mock_contract

        with pytest.raises(ValueError):
            service.register_agent("", "0x1234567890123456789012345678901234567890", [])

    @patch('blockchain.blockchain_service.get_web3')
    def test_register_agent_invalid_wallet(self, mock_get_web3):
        """测试无效钱包地址"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.agent_registry_contract = mock_contract

        with pytest.raises(ValueError):
            service.register_agent("TestAgent", "invalid", [])


class TestGetRewardBalance:
    """获取奖励余额测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_get_reward_balance_success(self, mock_get_web3):
        """测试成功获取余额"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_contract.functions.getBalance.return_value.call.return_value = 1000
        service.reward_pool_contract = mock_contract

        result = service.get_reward_balance("0x1234567890123456789012345678901234567890")

        assert result == 1000
        mock_contract.functions.getBalance.assert_called_once()

    @patch('blockchain.blockchain_service.get_web3')
    def test_get_reward_balance_zero(self, mock_get_web3):
        """测试零余额"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_contract.functions.getBalance.return_value.call.return_value = 0
        service.reward_pool_contract = mock_contract

        result = service.get_reward_balance("0x1234567890123456789012345678901234567890")

        assert result == 0


class TestWithdrawReward:
    """提取奖励测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_withdraw_reward_success(self, mock_get_web3):
        """测试成功提取奖励"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_tx_hash = b'0x' + b'6' * 64
        mock_contract.functions.withdraw.return_value.transact.return_value = mock_tx_hash
        service.reward_pool_contract = mock_contract

        result = service.withdraw_reward(100)

        assert result == mock_tx_hash.hex()
        mock_contract.functions.withdraw.assert_called_once_with(100)

    @patch('blockchain.blockchain_service.get_web3')
    def test_withdraw_reward_negative_amount(self, mock_get_web3):
        """测试负数金额"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.reward_pool_contract = mock_contract

        with pytest.raises(ValueError):
            service.withdraw_reward(-100)

    @patch('blockchain.blockchain_service.get_web3')
    def test_withdraw_reward_zero_amount(self, mock_get_web3):
        """测试零金额"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.reward_pool_contract = mock_contract

        with pytest.raises(ValueError):
            service.withdraw_reward(0)


class TestGasEstimation:
    """Gas估算测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_estimate_gas_publish_task(self, mock_get_web3):
        """测试估算发布任务的Gas"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.estimate_gas.return_value = 50000
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.task_market_contract = mock_contract

        result = service.estimate_gas_for_publish_task(
            "task_123",
            "Test task",
            100,
            123456
        )

        assert result > 0

    @patch('blockchain.blockchain_service.get_web3')
    def test_estimate_gas_accept_task(self, mock_get_web3):
        """测试估算接受任务的Gas"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.estimate_gas.return_value = 30000
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        service.task_market_contract = mock_contract

        result = service.estimate_gas_for_accept_task("task_123")

        assert result > 0


class TestTransactionReceipt:
    """交易收据测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_get_transaction_receipt_success(self, mock_get_web3):
        """测试成功获取交易收据"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True

        mock_receipt = {
            'transactionHash': '0x123',
            'blockNumber': 12345,
            'gasUsed': 50000,
            'status': 1
        }
        mock_web3.eth.get_transaction_receipt.return_value = mock_receipt
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        result = service.get_transaction_receipt('0x123')

        assert result['status'] == 1
        assert result['gasUsed'] == 50000

    @patch('blockchain.blockchain_service.get_web3')
    def test_get_transaction_receipt_not_found(self, mock_get_web3):
        """测试交易收据不存在"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_web3.eth.get_transaction_receipt.return_value = None
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        result = service.get_transaction_receipt('0x999')

        assert result is None

    @patch('blockchain.blockchain_service.get_web3')
    def test_get_transaction_receipt_failed(self, mock_get_web3):
        """测试失败的交易"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True

        mock_receipt = {
            'transactionHash': '0x123',
            'blockNumber': 12345,
            'gasUsed': 50000,
            'status': 0  # 失败
        }
        mock_web3.eth.get_transaction_receipt.return_value = mock_receipt
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        result = service.get_transaction_receipt('0x123')

        assert result['status'] == 0


class TestConnectionHandling:
    """连接处理测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_check_connection_success(self, mock_get_web3):
        """测试检查连接成功"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        assert service.is_connected() == True

    @patch('blockchain.blockchain_service.get_web3')
    def test_check_connection_failed(self, mock_get_web3):
        """测试检查连接失败"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = False
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        assert service.is_connected() == False

    @patch('blockchain.blockchain_service.get_web3')
    def test_reconnect(self, mock_get_web3):
        """测试重新连接"""
        mock_web3 = Mock()
        mock_web3.is_connected.side_effect = [False, True]
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        # 第一次连接失败，重连后成功
        service.reconnect()
        assert service.is_connected() == True


class TestErrorHandling:
    """错误处理测试"""

    @patch('blockchain.blockchain_service.get_web3')
    def test_handle_insufficient_funds(self, mock_get_web3):
        """测试处理资金不足错误"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_contract.functions.publishTask.return_value.transact.side_effect = \
            Exception("insufficient funds for gas * price + value")
        service.task_market_contract = mock_contract

        with pytest.raises(Exception) as exc_info:
            service.publish_task("task_123", "Test", 100, 123456)

        assert "insufficient funds" in str(exc_info.value)

    @patch('blockchain.blockchain_service.get_web3')
    def test_handle_nonce_too_low(self, mock_get_web3):
        """测试处理nonce过低错误"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_contract.functions.publishTask.return_value.transact.side_effect = \
            Exception("nonce too low")
        service.task_market_contract = mock_contract

        with pytest.raises(Exception) as exc_info:
            service.publish_task("task_123", "Test", 100, 123456)

        assert "nonce too low" in str(exc_info.value)

    @patch('blockchain.blockchain_service.get_web3')
    def test_handle_contract_revert(self, mock_get_web3):
        """测试处理合约回滚错误"""
        mock_web3 = Mock()
        mock_web3.is_connected.return_value = True
        mock_get_web3.return_value = mock_web3

        service = BlockchainService()
        mock_contract = Mock()
        mock_contract.functions.publishTask.return_value.transact.side_effect = \
            Exception("execution reverted")
        service.task_market_contract = mock_contract

        with pytest.raises(Exception) as exc_info:
            service.publish_task("task_123", "Test", 100, 123456)

        assert "reverted" in str(exc_info.value)
