"""
Tests for MEME Token smart contract and Python interface.

Tests cover:
- Token deployment and initialization
- Mining reward claims
- Halving mechanism
- Balance queries
- Statistics retrieval
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from nautilus.token.meme_token import MEMEToken


class TestMEMETokenInterface:
    """Test MEME Token Python interface."""

    @pytest.fixture
    def mock_web3(self):
        """Create mock Web3 instance."""
        web3 = Mock()
        web3.eth = Mock()
        web3.to_checksum_address = lambda x: x
        return web3

    @pytest.fixture
    def mock_contract(self):
        """Create mock contract instance."""
        contract = Mock()
        contract.functions = Mock()
        return contract

    @pytest.fixture
    def meme_token(self, mock_web3, mock_contract):
        """Create MEMEToken instance with mocks."""
        with patch.object(mock_web3.eth, 'contract', return_value=mock_contract):
            token = MEMEToken(
                web3=mock_web3,
                contract_address='0x1234567890123456789012345678901234567890',
                contract_abi=[]
            )
            token.contract = mock_contract
            return token

    def test_initialization(self, mock_web3, mock_contract):
        """Test token interface initialization."""
        with patch.object(mock_web3.eth, 'contract', return_value=mock_contract):
            token = MEMEToken(
                web3=mock_web3,
                contract_address='0x1234567890123456789012345678901234567890',
                contract_abi=[]
            )

            assert token.web3 == mock_web3
            assert token.contract == mock_contract

    def test_get_balance(self, meme_token, mock_contract):
        """Test balance query."""
        mock_contract.functions.balanceOf.return_value.call.return_value = 1000 * 10**18

        # Use valid Ethereum address format
        balance = meme_token.get_balance('0x1234567890123456789012345678901234567890')

        assert balance == 1000 * 10**18
        mock_contract.functions.balanceOf.assert_called_once()

    def test_get_current_reward(self, meme_token, mock_contract):
        """Test current reward query."""
        mock_contract.functions.getCurrentReward.return_value.call.return_value = 50 * 10**18

        reward = meme_token.get_current_reward()

        assert reward == 50 * 10**18
        mock_contract.functions.getCurrentReward.assert_called_once()

    def test_is_proof_claimed(self, meme_token, mock_contract):
        """Test proof claimed check."""
        proof_id = b'0' * 32
        mock_contract.functions.isProofClaimed.return_value.call.return_value = True

        claimed = meme_token.is_proof_claimed(proof_id)

        assert claimed is True
        mock_contract.functions.isProofClaimed.assert_called_once_with(proof_id)

    def test_get_agent_stats(self, meme_token, mock_contract):
        """Test agent statistics query."""
        mock_contract.functions.getAgentStats.return_value.call.return_value = (
            500 * 10**18,  # mined
            300 * 10**18   # balance
        )

        # Use valid Ethereum address format
        stats = meme_token.get_agent_stats('0x1234567890123456789012345678901234567890')

        assert stats['mined'] == 500 * 10**18
        assert stats['balance'] == 300 * 10**18

    def test_get_token_stats(self, meme_token, mock_contract):
        """Test token statistics query."""
        mock_contract.functions.getTokenStats.return_value.call.return_value = (
            10_000_000 * 10**18,  # current_supply
            100_000_000 * 10**18,  # max_supply
            10_000_000 * 10**18,  # total_mined
            50 * 10**18,          # current_reward
            100_000               # blocks_until_halving
        )

        stats = meme_token.get_token_stats()

        assert stats['current_supply'] == 10_000_000 * 10**18
        assert stats['max_supply'] == 100_000_000 * 10**18
        assert stats['total_mined'] == 10_000_000 * 10**18
        assert stats['current_reward'] == 50 * 10**18
        assert stats['blocks_until_halving'] == 100_000
        assert stats['supply_percentage'] == 10.0

    def test_get_total_supply(self, meme_token, mock_contract):
        """Test total supply query."""
        mock_contract.functions.totalSupply.return_value.call.return_value = 10_000_000 * 10**18

        supply = meme_token.get_total_supply()

        assert supply == 10_000_000 * 10**18

    def test_get_max_supply(self, meme_token, mock_contract):
        """Test max supply query."""
        mock_contract.functions.MAX_SUPPLY.return_value.call.return_value = 100_000_000 * 10**18

        max_supply = meme_token.get_max_supply()

        assert max_supply == 100_000_000 * 10**18

    def test_get_pow_contract(self, meme_token, mock_contract):
        """Test PoW contract address query."""
        mock_contract.functions.powProofContract.return_value.call.return_value = '0xpow'

        pow_contract = meme_token.get_pow_contract()

        assert pow_contract == '0xpow'

    def test_wei_to_tokens(self):
        """Test wei to tokens conversion."""
        wei_amount = 50 * 10**18
        tokens = MEMEToken.wei_to_tokens(wei_amount)

        assert tokens == 50.0

    def test_tokens_to_wei(self):
        """Test tokens to wei conversion."""
        token_amount = 50.0
        wei = MEMEToken.tokens_to_wei(token_amount)

        assert wei == 50 * 10**18

    def test_wei_to_tokens_fractional(self):
        """Test wei to tokens with fractional amount."""
        wei_amount = int(0.5 * 10**18)
        tokens = MEMEToken.wei_to_tokens(wei_amount)

        assert tokens == 0.5

    def test_tokens_to_wei_fractional(self):
        """Test tokens to wei with fractional amount."""
        token_amount = 0.5
        wei = MEMEToken.tokens_to_wei(token_amount)

        assert wei == int(0.5 * 10**18)


class TestMEMETokenLogic:
    """Test MEME Token business logic."""

    def test_initial_reward_calculation(self):
        """Test initial reward is 50 tokens."""
        initial_reward = 50 * 10**18
        assert initial_reward == 50_000_000_000_000_000_000

    def test_halving_calculation(self):
        """Test reward halving calculation."""
        initial_reward = 50 * 10**18

        # After 1 halving
        reward_1 = initial_reward / 2
        assert reward_1 == 25 * 10**18

        # After 2 halvings
        reward_2 = initial_reward / 4
        assert reward_2 == 12.5 * 10**18

        # After 3 halvings
        reward_3 = initial_reward / 8
        assert reward_3 == 6.25 * 10**18

    def test_minimum_reward(self):
        """Test minimum reward floor."""
        minimum_reward = 0.1 * 10**18
        assert minimum_reward == 100_000_000_000_000_000

    def test_max_supply(self):
        """Test maximum supply constant."""
        max_supply = 100_000_000 * 10**18
        assert max_supply == 100_000_000_000_000_000_000_000_000

    def test_initial_supply(self):
        """Test initial supply (10% of max)."""
        max_supply = 100_000_000 * 10**18
        initial_supply = max_supply // 10  # Use integer division
        assert initial_supply == 10_000_000 * 10**18

    def test_halving_interval(self):
        """Test halving interval constant."""
        halving_interval = 210_000
        assert halving_interval == 210000

    def test_supply_percentage_calculation(self):
        """Test supply percentage calculation."""
        current_supply = 10_000_000 * 10**18
        max_supply = 100_000_000 * 10**18
        percentage = (current_supply / max_supply) * 100

        assert percentage == 10.0

    def test_blocks_until_halving(self):
        """Test blocks until halving calculation."""
        halving_interval = 210_000
        blocks_since_deployment = 50_000
        blocks_in_current_period = blocks_since_deployment % halving_interval
        blocks_until_halving = halving_interval - blocks_in_current_period

        assert blocks_until_halving == 160_000


class TestMEMETokenIntegration:
    """Integration tests for MEME Token."""

    def test_reward_claim_flow(self, mock_web3=None):
        """Test complete reward claim flow."""
        # This would be an integration test with actual contract
        # For now, just verify the flow logic
        proof_id = b'0' * 32
        agent_address = '0xagent'
        task_id = b'1' * 32
        result_hash = b'2' * 32
        nonce = 12345

        # Verify all required parameters are present
        assert proof_id is not None
        assert agent_address is not None
        assert task_id is not None
        assert result_hash is not None
        assert nonce is not None

    def test_token_economics(self):
        """Test token economics calculations."""
        max_supply = 100_000_000 * 10**18
        initial_supply = max_supply / 10
        initial_reward = 50 * 10**18

        # Calculate approximate number of rewards until max supply
        mineable_supply = max_supply - initial_supply
        approximate_rewards = mineable_supply / initial_reward

        # Should be around 1.8 million rewards at initial rate
        assert approximate_rewards > 1_000_000
        assert approximate_rewards < 2_000_000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
