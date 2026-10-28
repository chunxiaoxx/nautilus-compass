"""Tests for NautilusTokenService."""
import pytest
from unittest.mock import MagicMock, patch


def test_reward_table_covers_all_task_types():
    """Every AcademicTaskType should have a reward entry."""
    from services.nautilus_token import TASK_TYPE_REWARDS
    known_types = [
        "physics_simulation", "pde_simulation", "ode_simulation",
        "ml_training", "monte_carlo", "jc_constitutive", "thmc_coupling",
        "curve_fitting", "statistical_analysis", "data_visualization",
        "general_computation",
    ]
    for t in known_types:
        assert t in TASK_TYPE_REWARDS, f"Missing reward for {t}"
        assert TASK_TYPE_REWARDS[t] > 0


def test_reward_amounts_are_tiered():
    """High-complexity tasks should earn more than low-complexity."""
    from services.nautilus_token import TASK_TYPE_REWARDS
    assert TASK_TYPE_REWARDS["physics_simulation"] > TASK_TYPE_REWARDS["curve_fitting"]
    assert TASK_TYPE_REWARDS["curve_fitting"] > TASK_TYPE_REWARDS["general_computation"]


@pytest.mark.asyncio
async def test_mint_returns_none_when_no_nau_contract():
    """mint_task_reward returns None silently when NAU contract not loaded."""
    mock_cfg = MagicMock()
    mock_cfg.nau_contract = None
    with patch("services.nautilus_token.get_web3_config", return_value=mock_cfg):
        from services.nautilus_token import NautilusTokenService
        result = await NautilusTokenService.mint_task_reward(
            agent_wallet="0xabc", task_type="general_computation"
        )
        assert result is None


@pytest.mark.asyncio
async def test_mint_returns_none_when_no_wallet():
    """mint_task_reward returns None when agent_wallet is empty."""
    from services.nautilus_token import NautilusTokenService
    result = await NautilusTokenService.mint_task_reward(
        agent_wallet="", task_type="general_computation"
    )
    assert result is None


@pytest.mark.asyncio
async def test_mint_returns_none_when_no_private_key():
    """mint_task_reward returns None when BLOCKCHAIN_PRIVATE_KEY is empty."""
    mock_cfg = MagicMock()
    mock_cfg.nau_contract = MagicMock()  # contract exists
    with patch("services.nautilus_token.get_web3_config", return_value=mock_cfg), \
         patch("services.nautilus_token.BLOCKCHAIN_PRIVATE_KEY", ""):
        from services.nautilus_token import NautilusTokenService
        result = await NautilusTokenService.mint_task_reward(
            agent_wallet="0x1234567890abcdef1234567890abcdef12345678",
            task_type="general_computation",
        )
        assert result is None


# ---------------------------------------------------------------------------
# mint_collaborative_reward
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_collaborative_mint_empty_coordinator_returns_empty():
    """Empty coordinator wallet returns empty list immediately."""
    from services.nautilus_token import NautilusTokenService
    result = await NautilusTokenService.mint_collaborative_reward(
        coordinator_wallet="",
        researcher_wallets=["0xabc"],
        task_type="research_synthesis",
    )
    assert result == []


@pytest.mark.asyncio
async def test_collaborative_mint_no_researchers_falls_back_to_single_no_contract():
    """No researcher wallets + no contract → falls back to single mint → empty."""
    mock_cfg = MagicMock()
    mock_cfg.nau_contract = None
    with patch("services.nautilus_token.get_web3_config", return_value=mock_cfg):
        from services.nautilus_token import NautilusTokenService
        result = await NautilusTokenService.mint_collaborative_reward(
            coordinator_wallet="0x1234567890abcdef1234567890abcdef12345678",
            researcher_wallets=[],
            task_type="research_synthesis",
        )
        # mint_task_reward returns None (no contract), so list is empty
        assert result == []


@pytest.mark.asyncio
async def test_collaborative_mint_with_researchers_no_contract_returns_empty():
    """With researchers but no contract/key configured → returns empty list."""
    mock_cfg = MagicMock()
    mock_cfg.nau_contract = None
    with patch("services.nautilus_token.get_web3_config", return_value=mock_cfg):
        from services.nautilus_token import NautilusTokenService
        result = await NautilusTokenService.mint_collaborative_reward(
            coordinator_wallet="0x1234567890abcdef1234567890abcdef12345678",
            researcher_wallets=["0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"],
            task_type="research_synthesis",
        )
        assert result == []


@pytest.mark.asyncio
async def test_collaborative_mint_with_researchers_no_private_key_returns_empty():
    """Researchers present, contract present, but no private key → empty."""
    mock_cfg = MagicMock()
    mock_cfg.nau_contract = MagicMock()
    with patch("services.nautilus_token.get_web3_config", return_value=mock_cfg), \
         patch("services.nautilus_token.BLOCKCHAIN_PRIVATE_KEY", ""):
        from services.nautilus_token import NautilusTokenService
        result = await NautilusTokenService.mint_collaborative_reward(
            coordinator_wallet="0x1234567890abcdef1234567890abcdef12345678",
            researcher_wallets=["0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"],
            task_type="research_synthesis",
        )
        assert result == []


def test_collaborative_reward_distribution_proportions():
    """Coordinator gets 40%, researchers split 60% — verify arithmetic."""
    from services.nautilus_token import TASK_TYPE_REWARDS
    total_nau = TASK_TYPE_REWARDS["research_synthesis"]  # 8
    coordinator_nau = max(1, int(total_nau * 0.4))  # 3
    researcher_total = total_nau - coordinator_nau    # 5
    n_researchers = 2
    per_researcher = max(1, researcher_total // n_researchers)  # 2

    # Coordinator share is less than half
    assert coordinator_nau < total_nau // 2 + 1
    # Per-researcher share is positive
    assert per_researcher >= 1
    # Total distributed does not exceed total_nau
    distributed = coordinator_nau + per_researcher * n_researchers
    assert distributed <= total_nau
