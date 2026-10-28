"""
Gas费用分担机制测试
测试任务发布者和执行者1:1分担Gas费用
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from blockchain.blockchain_service import BlockchainService


class TestGasCalculation:
    """测试Gas计算功能"""

    def test_get_transaction_gas_used(self):
        """测试获取交易Gas使用情况"""
        # Mock Web3 instance
        mock_w3 = Mock()

        # Mock transaction receipt
        mock_receipt = {
            'gasUsed': 100000,
            'transactionHash': '0x123'
        }

        # Mock transaction
        mock_transaction = {
            'gasPrice': 20000000000,  # 20 Gwei
            'hash': '0x123'
        }

        mock_w3.eth.get_transaction_receipt.return_value = mock_receipt
        mock_w3.eth.get_transaction.return_value = mock_transaction

        with patch('blockchain.blockchain_service.get_w3', return_value=mock_w3), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            service.w3 = mock_w3

            result = service.get_transaction_gas_used('0x123')

            assert result is not None
            assert result['gas_used'] == 100000
            assert result['gas_price'] == 20000000000
            assert result['gas_cost'] == 2000000000000000  # 100000 * 20 Gwei

    def test_calculate_gas_split(self):
        """测试Gas费用分担计算（50%）"""
        with patch('blockchain.blockchain_service.get_w3'), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()

            total_gas_cost = 2000000000000000  # 0.002 ETH
            gas_split = service.calculate_gas_split(total_gas_cost)

            assert gas_split == 1000000000000000  # 50% = 0.001 ETH

    def test_calculate_gas_split_odd_number(self):
        """测试奇数Gas费用分担计算"""
        with patch('blockchain.blockchain_service.get_w3'), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()

            total_gas_cost = 1000000000000001  # Odd number
            gas_split = service.calculate_gas_split(total_gas_cost)

            # Integer division, agent pays slightly less
            assert gas_split == 500000000000000

    def test_calculate_task_total_gas(self):
        """测试计算任务总Gas费用"""
        mock_w3 = Mock()

        # Mock multiple transactions
        tx_hashes = ['0x123', '0x456', '0x789']

        gas_info_list = [
            {'gas_used': 100000, 'gas_price': 20000000000, 'gas_cost': 2000000000000000},
            {'gas_used': 50000, 'gas_price': 20000000000, 'gas_cost': 1000000000000000},
            {'gas_used': 75000, 'gas_price': 20000000000, 'gas_cost': 1500000000000000}
        ]

        with patch('blockchain.blockchain_service.get_w3', return_value=mock_w3), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            service.w3 = mock_w3

            # Mock get_transaction_gas_used to return different values
            service.get_transaction_gas_used = Mock(side_effect=gas_info_list)

            result = service.calculate_task_total_gas(tx_hashes)

            assert result is not None
            assert result['total_gas_used'] == 225000  # 100000 + 50000 + 75000
            assert result['total_gas_cost'] == 4500000000000000  # Sum of all costs
            assert result['gas_split'] == 2250000000000000  # 50% of total

    def test_calculate_task_total_gas_with_none_hashes(self):
        """测试包含None的交易哈希列表"""
        mock_w3 = Mock()

        tx_hashes = ['0x123', None, '0x789', None]

        gas_info_list = [
            {'gas_used': 100000, 'gas_price': 20000000000, 'gas_cost': 2000000000000000},
            {'gas_used': 75000, 'gas_price': 20000000000, 'gas_cost': 1500000000000000}
        ]

        with patch('blockchain.blockchain_service.get_w3', return_value=mock_w3), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            service.w3 = mock_w3

            call_count = 0
            def mock_get_gas(tx_hash):
                nonlocal call_count
                if tx_hash is None:
                    return None
                result = gas_info_list[call_count]
                call_count += 1
                return result

            service.get_transaction_gas_used = Mock(side_effect=mock_get_gas)

            result = service.calculate_task_total_gas(tx_hashes)

            assert result is not None
            assert result['total_gas_used'] == 175000
            assert result['total_gas_cost'] == 3500000000000000

    def test_get_transaction_gas_used_receipt_not_found(self):
        """测试交易回执未找到的情况"""
        mock_w3 = Mock()
        mock_w3.eth.get_transaction_receipt.return_value = None

        with patch('blockchain.blockchain_service.get_w3', return_value=mock_w3), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            service.w3 = mock_w3

            result = service.get_transaction_gas_used('0x123')

            assert result is None

    def test_get_transaction_gas_used_transaction_not_found(self):
        """测试交易未找到的情况"""
        mock_w3 = Mock()
        mock_receipt = {'gasUsed': 100000}
        mock_w3.eth.get_transaction_receipt.return_value = mock_receipt
        mock_w3.eth.get_transaction.return_value = None

        with patch('blockchain.blockchain_service.get_w3', return_value=mock_w3), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            service.w3 = mock_w3

            result = service.get_transaction_gas_used('0x123')

            assert result is None

    def test_calculate_task_total_gas_exception(self):
        """测试计算Gas时发生异常"""
        mock_w3 = Mock()

        with patch('blockchain.blockchain_service.get_w3', return_value=mock_w3), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            service.w3 = mock_w3

            # Mock to raise exception
            service.get_transaction_gas_used = Mock(side_effect=Exception("Network error"))

            result = service.calculate_task_total_gas(['0x123'])

            assert result is None


class TestGasFeeSharingIntegration:
    """测试Gas费用分担集成功能"""

    def test_gas_calculation_in_task_completion(self):
        """测试任务完成时的Gas计算"""
        # This would be an integration test with the actual API
        # For now, we test the logic flow

        # Simulate task completion scenario
        reward = 10000000000000000  # 0.01 ETH
        total_gas_cost = 2000000000000000  # 0.002 ETH

        with patch('blockchain.blockchain_service.get_w3'), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            gas_split = service.calculate_gas_split(total_gas_cost)

            # Agent's actual reward after gas deduction
            actual_reward = reward - gas_split

            assert gas_split == 1000000000000000  # 0.001 ETH (50%)
            assert actual_reward == 9000000000000000  # 0.009 ETH

    def test_gas_split_larger_than_reward(self):
        """测试Gas费用超过奖励的情况"""
        reward = 1000000000000000  # 0.001 ETH
        total_gas_cost = 3000000000000000  # 0.003 ETH

        with patch('blockchain.blockchain_service.get_w3'), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            gas_split = service.calculate_gas_split(total_gas_cost)

            # Agent's actual reward would be negative
            actual_reward = reward - gas_split

            assert gas_split == 1500000000000000  # 0.0015 ETH (50%)
            assert actual_reward < 0  # Agent would lose money
            # In production, this should be handled with validation

    def test_multiple_transactions_gas_accumulation(self):
        """测试多个交易的Gas累积"""
        mock_w3 = Mock()

        # Simulate 4 transactions: publish, accept, submit, complete
        tx_hashes = [
            '0xpublish',
            '0xaccept',
            '0xsubmit',
            '0xcomplete'
        ]

        gas_costs = [
            500000000000000,   # Publish: 0.0005 ETH
            200000000000000,   # Accept: 0.0002 ETH
            200000000000000,   # Submit: 0.0002 ETH
            300000000000000    # Complete: 0.0003 ETH
        ]

        with patch('blockchain.blockchain_service.get_w3', return_value=mock_w3), \
             patch('blockchain.blockchain_service.get_web3_config'):
            service = BlockchainService()
            service.w3 = mock_w3

            gas_info_list = [
                {'gas_used': 25000, 'gas_price': 20000000000, 'gas_cost': cost}
                for cost in gas_costs
            ]

            service.get_transaction_gas_used = Mock(side_effect=gas_info_list)

            result = service.calculate_task_total_gas(tx_hashes)

            total_cost = sum(gas_costs)
            assert result['total_gas_cost'] == total_cost
            assert result['gas_split'] == total_cost // 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
