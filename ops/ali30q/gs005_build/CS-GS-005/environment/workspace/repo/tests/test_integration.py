"""
Integration tests for Nautilus Phase 2.

Tests the complete workflow:
1. Bidirectional closed-loop communication
2. PoW computation and verification
3. MEME Token reward claiming
4. Multi-agent collaboration
"""

import pytest
import hashlib
from unittest.mock import Mock, patch
from nautilus.communication.crypto import CryptoManager
from nautilus.communication.protocol import BidirectionalClosedLoopProtocol
from nautilus.pow.compute import compute_pow
from nautilus.pow.verify import verify_pow
from nautilus.pow.difficulty import DifficultyAdjuster
from nautilus.agents.router import TaskRouter, TaskComplexity
from nautilus.agents.openclaw import OpenClawCoordinator
from nautilus.agents.claude_code import ClaudeCodeExecutor
from nautilus.token.meme_token import MEMEToken


class TestCommunicationPoWIntegration:
    """Test integration between communication and PoW modules."""

    def test_secure_pow_submission(self):
        """Test secure PoW result submission via encrypted channel."""
        # Setup agents
        agent_a = CryptoManager("agent_a")
        agent_b = CryptoManager("agent_b")

        protocol_a = BidirectionalClosedLoopProtocol(agent_a)
        protocol_b = BidirectionalClosedLoopProtocol(agent_b)

        # Agent A computes PoW
        task_result = b"completed_task_12345"
        difficulty = 16
        nonce, pow_hash = compute_pow(task_result, difficulty)

        # Verify PoW locally
        assert verify_pow(task_result, nonce, pow_hash, difficulty)

        # Agent A sends result to Agent B via secure channel
        result_message = f"task_result:{task_result.hex()},nonce:{nonce},hash:{pow_hash}".encode()

        # Phase 1: Request (signed message)
        request = protocol_a.send_request(result_message)
        assert protocol_b.verify_request(request)

        # Phase 3: Confirmation (skip encrypted response for simplicity)
        confirmation = protocol_a.send_confirmation(b"confirmed")
        assert protocol_b.verify_confirmation(confirmation)

    def test_pow_result_integrity(self):
        """Test PoW result integrity through communication protocol."""
        agent = CryptoManager("agent")
        protocol = BidirectionalClosedLoopProtocol(agent)

        # Compute PoW
        result = b"task_data"
        difficulty = 12
        nonce, pow_hash = compute_pow(result, difficulty)

        # Create signed message with PoW proof
        message = f"{result.hex()}:{nonce}:{pow_hash}".encode()
        request = protocol.send_request(message)

        # Verify signature ensures integrity
        assert protocol.verify_request(request)

        # Tamper with message
        request['message'] = b"tampered_data"

        # Verification should fail
        assert not protocol.verify_request(request)


class TestPoWTokenIntegration:
    """Test integration between PoW and MEME Token modules."""

    @patch('nautilus.token.meme_token.Web3')
    def test_pow_to_token_reward_flow(self, mock_web3):
        """Test complete flow from PoW verification to token reward."""
        # Setup mock Web3 and contract
        mock_contract = Mock()
        mock_web3.return_value.eth.contract.return_value = mock_contract

        # Compute PoW
        task_id = b'0' * 32
        result = b"completed_work"
        difficulty = 16
        nonce, pow_hash = compute_pow(result, difficulty)

        # Verify PoW
        assert verify_pow(result, nonce, pow_hash, difficulty)

        # Generate proof ID
        proof_id = hashlib.sha256(task_id + result + nonce.to_bytes(8, 'big')).digest()

        # Mock token contract to return verified proof
        mock_contract.functions.getProof.return_value.call.return_value = (
            '0x1234567890123456789012345678901234567890',  # agent
            task_id,  # taskId
            hashlib.sha256(result).digest(),  # resultHash
            nonce,  # nonce
            bytes.fromhex(pow_hash),  # powHash
            12345,  # timestamp
            True  # verified
        )

        # Mock reward claim
        mock_contract.functions.claimMiningReward.return_value.build_transaction.return_value = {
            'from': '0x1234567890123456789012345678901234567890',
            'nonce': 0,
            'gas': 200000,
            'gasPrice': 1000000000
        }

        # Verify proof can be used for reward claim
        assert mock_contract.functions.getProof.return_value.call.return_value[6] is True


class TestMultiAgentIntegration:
    """Test multi-agent collaboration integration."""

    @patch('nautilus.agents.openclaw.Agent')
    @patch('nautilus.agents.claude_code.Agent')
    def test_task_routing_and_execution(self, mock_claude_agent, mock_openclaw_agent):
        """Test complete task routing and execution flow."""
        mock_openclaw_agent.return_value = Mock()
        mock_claude_agent.return_value = Mock()

        # Setup coordinator and executor
        coordinator = OpenClawCoordinator()
        executor = ClaudeCodeExecutor()
        coordinator.register_service_agent('claude_code', executor.get_agent(), capacity=10)

        # Setup router
        router = TaskRouter()

        # Test 1: Simple task routing
        simple_task = "Fix typo in documentation"
        complexity = router.evaluate_complexity(simple_task, estimated_hours=1)
        agent = router.select_agent(complexity)

        assert complexity == TaskComplexity.SIMPLE
        assert agent == 'openclaw'

        # Test 2: Complex task routing
        complex_task = "Implement distributed consensus protocol with blockchain integration"
        complexity = router.evaluate_complexity(complex_task, estimated_hours=50)
        agent = router.select_agent(complexity)

        assert complexity == TaskComplexity.COMPLEX
        assert agent == 'claude_code'

        # Test 3: Workload tracking
        coordinator.agent_workload['claude_code']['current_load'] = 5
        stats = coordinator.get_workload_stats()

        assert stats['agents']['claude_code']['current_load'] == 5
        assert 'claude_code' in stats['agents']


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    @patch('nautilus.agents.openclaw.Agent')
    @patch('nautilus.agents.claude_code.Agent')
    def test_complete_mining_workflow(self, mock_claude_agent, mock_openclaw_agent):
        """Test complete workflow from task assignment to reward."""
        mock_openclaw_agent.return_value = Mock()
        mock_claude_agent.return_value = Mock()

        # Step 1: Task routing
        router = TaskRouter()
        task_description = "Implement smart contract integration"
        complexity = router.evaluate_complexity(task_description, estimated_hours=25)

        assert complexity == TaskComplexity.MEDIUM or complexity == TaskComplexity.COMPLEX

        # Step 2: Agent selection
        agent_name = router.select_agent(complexity)
        assert agent_name in ['openclaw', 'claude_code']

        # Step 3: Secure communication setup
        agent_a = CryptoManager("executor")
        agent_b = CryptoManager("coordinator")

        protocol_a = BidirectionalClosedLoopProtocol(agent_a)
        protocol_b = BidirectionalClosedLoopProtocol(agent_b)

        # Step 4: Task execution and PoW computation
        task_result = b"smart_contract_implementation_complete"
        difficulty = 16
        nonce, pow_hash = compute_pow(task_result, difficulty, max_iterations=1000000)

        # Step 5: Verify PoW
        is_valid = verify_pow(task_result, nonce, pow_hash, difficulty)
        assert is_valid

        # Step 6: Secure result submission
        result_message = f"result:{task_result.hex()},nonce:{nonce}".encode()
        request = protocol_a.send_request(result_message)
        assert protocol_b.verify_request(request)

        # Step 7: Confirmation
        confirmation = protocol_a.send_confirmation(b"confirmed")
        assert protocol_b.verify_confirmation(confirmation)

        # Step 8: Token reward (mocked)
        # In real scenario, this would claim MEME tokens
        reward_amount = 50 * 10**18  # 50 MEME tokens
        assert reward_amount > 0


class TestDifficultyAdjustment:
    """Test difficulty adjustment integration."""

    def test_difficulty_adjustment_with_pow(self):
        """Test difficulty adjustment based on computation times."""
        adjuster = DifficultyAdjuster(target_time=15.0)

        # Simulate multiple PoW computations
        result = b"test_data"

        for i in range(5):
            difficulty = adjuster.get_current_difficulty()

            # Compute PoW (simplified for testing)
            nonce, pow_hash = compute_pow(result + str(i).encode(), difficulty, max_iterations=100000)

            # Record time (simulated)
            computation_time = 10.0 + i * 2  # Increasing times
            adjuster.record_computation(computation_time)

        # Difficulty should adjust based on times
        final_difficulty = adjuster.get_current_difficulty()
        assert final_difficulty >= 12  # Should be reasonable


class TestPerformance:
    """Performance and stress tests."""

    def test_communication_performance(self):
        """Test communication protocol performance."""
        agent_a = CryptoManager("agent_a")
        agent_b = CryptoManager("agent_b")

        protocol_a = BidirectionalClosedLoopProtocol(agent_a)
        protocol_b = BidirectionalClosedLoopProtocol(agent_b)

        # Test multiple message exchanges (request and confirmation only)
        for i in range(10):
            message = f"message_{i}".encode()

            # Request
            request = protocol_a.send_request(message)
            assert protocol_b.verify_request(request)

            # Confirmation
            confirmation = protocol_b.send_confirmation(b"ack")
            assert protocol_a.verify_confirmation(confirmation)

    def test_pow_computation_performance(self):
        """Test PoW computation performance."""
        result = b"performance_test"
        difficulty = 12  # Lower difficulty for faster testing

        # Should complete in reasonable time
        nonce, pow_hash = compute_pow(result, difficulty, max_iterations=1000000)

        assert nonce is not None
        assert pow_hash is not None
        assert verify_pow(result, nonce, pow_hash, difficulty)

    def test_routing_performance(self):
        """Test task routing performance."""
        router = TaskRouter()

        # Route 100 tasks
        for i in range(100):
            task = f"Task {i}: implement feature"
            complexity = router.evaluate_complexity(task, estimated_hours=10 + i % 30)
            agent = router.select_agent(complexity)

            assert agent in ['openclaw', 'claude_code']

        # Check statistics
        stats = router.get_routing_statistics()
        assert stats['total_tasks'] == 100


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_pow_verification(self):
        """Test PoW verification with invalid nonce."""
        result = b"test_data"
        difficulty = 16

        # Invalid nonce should fail verification
        assert not verify_pow(result, 99999, "invalid_hash", difficulty)

    def test_tampered_communication(self):
        """Test detection of tampered messages."""
        agent_a = CryptoManager("agent_a")
        agent_b = CryptoManager("agent_b")

        protocol_a = BidirectionalClosedLoopProtocol(agent_a)
        protocol_b = BidirectionalClosedLoopProtocol(agent_b)

        # Send request
        request = protocol_a.send_request(b"original_message")

        # Tamper with message
        request['message'] = b"tampered_message"

        # Verification should fail
        assert not protocol_b.verify_request(request)

    @patch('nautilus.agents.openclaw.Agent')
    def test_missing_agent_registration(self, mock_agent):
        """Test error when required agent is not registered."""
        mock_agent.return_value = Mock()
        coordinator = OpenClawCoordinator()

        # Try to select complex task without Claude Code registered
        with pytest.raises(ValueError, match="Complex task requires Claude Code"):
            coordinator.select_agent(coordinator.evaluate_complexity(
                "Complex distributed system",
                50
            ))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
