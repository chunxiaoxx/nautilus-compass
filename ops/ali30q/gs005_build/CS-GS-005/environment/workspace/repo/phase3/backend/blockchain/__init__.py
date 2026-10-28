"""
Blockchain integration module.
Provides Web3 connection, smart contract interaction, and ERC20 payment support.
"""
from blockchain.web3_config import (
    Web3Config,
    get_web3_config,
    init_web3,
    get_w3,
    get_task_market,
    get_reward_pool,
    get_agent_registry,
)

from blockchain.blockchain_service import (
    BlockchainService,
    get_blockchain_service,
    to_token_units,
    from_token_units,
)

# Optional imports (may fail if dependencies not installed)
try:
    from blockchain.event_listener import (
        BlockchainEventListener,
        EventCache,
        get_event_listener,
        start_event_listener,
        stop_event_listener,
    )
except ImportError:
    pass

try:
    from blockchain.transaction_retry import (
        TransactionRetryManager,
        TransactionRetryConfig,
        get_retry_manager,
        execute_transaction_with_retry,
    )
except ImportError:
    pass

try:
    from blockchain.monitoring import (
        BlockchainMonitor,
        TransactionMetrics,
        GasMetrics,
        ConnectionMetrics,
        get_monitor,
    )
except ImportError:
    pass

__all__ = [
    "Web3Config",
    "get_web3_config",
    "init_web3",
    "get_w3",
    "get_task_market",
    "get_reward_pool",
    "get_agent_registry",
    "BlockchainService",
    "get_blockchain_service",
    "to_token_units",
    "from_token_units",
]
