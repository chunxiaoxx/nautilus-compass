"""
Blockchain service layer for ERC20 (USDC/USDT) payments on Base.

Provides high-level API for task publishing, reward distribution, and withdrawal.
"""
import logging
from typing import Optional, Dict, Any
from web3 import Web3

from blockchain.web3_config import get_web3_config, get_w3

logger = logging.getLogger(__name__)

# USDC/USDT have 6 decimals
TOKEN_DECIMALS = 6


def to_token_units(amount: float) -> int:
    """Convert human-readable amount (e.g. 10.5) to token units (10500000)."""
    return int(amount * 10**TOKEN_DECIMALS)


def from_token_units(raw: int) -> float:
    """Convert token units to human-readable amount."""
    return raw / 10**TOKEN_DECIMALS


class BlockchainService:
    """Blockchain service for ERC20 task payments on Base."""

    def __init__(self):
        self.config = get_web3_config()
        self.w3 = get_w3()

    # --- Task Operations ---

    async def publish_task_on_chain(
        self,
        description: str,
        input_data: str,
        expected_output: str,
        reward_amount: float,
        token: str = "usdc",
        task_type: int = 1,  # DATA
        timeout: int = 3600,
    ) -> Optional[str]:
        """
        Publish a task with ERC20 payment.

        1. Approve TaskContract to spend `reward_amount` tokens
        2. Call publishTask which transfers tokens to contract

        Returns tx_hash or None.
        """
        tc = self.config.task_contract
        if not tc:
            logger.warning("TaskContract not loaded")
            return None

        account = self.config.get_account_address()
        if not account:
            logger.error("No account configured")
            return None

        token_address = self.config.get_token_address(token)
        if not token_address:
            logger.error(f"Token {token} not supported on {self.config.network_name}")
            return None

        token_contract = self.config.get_token_contract(token)
        reward_raw = to_token_units(reward_amount)

        try:
            nonce = self.w3.eth.get_transaction_count(account)

            # Step 1: Approve
            approve_tx = token_contract.functions.approve(
                tc.address, reward_raw
            ).build_transaction({
                "from": account,
                "nonce": nonce,
                "chainId": self.config.chain_id,
            })
            approve_hash = self._sign_and_send(approve_tx)
            self.w3.eth.wait_for_transaction_receipt(approve_hash, timeout=60)
            logger.info(f"Approved {reward_amount} {token.upper()}, tx: {approve_hash}")

            # Step 2: Publish task
            nonce += 1
            publish_tx = tc.functions.publishTask(
                description, input_data, expected_output,
                reward_raw, Web3.to_checksum_address(token_address),
                task_type, timeout
            ).build_transaction({
                "from": account,
                "nonce": nonce,
                "chainId": self.config.chain_id,
            })
            publish_hash = self._sign_and_send(publish_tx)
            receipt = self.w3.eth.wait_for_transaction_receipt(publish_hash, timeout=60)

            if receipt["status"] == 1:
                logger.info(f"Task published, reward: {reward_amount} {token.upper()}, tx: {publish_hash}")
                return publish_hash
            else:
                logger.error(f"publishTask reverted, tx: {publish_hash}")
                return None

        except Exception as e:
            logger.error(f"Failed to publish task: {e}")
            return None

    async def complete_task_on_chain(self, task_id: int) -> Optional[str]:
        """Complete a verified task, releasing ERC20 to agent via RewardContract."""
        tc = self.config.task_contract
        if not tc:
            return None

        account = self.config.get_account_address()
        if not account:
            return None

        try:
            tx = tc.functions.completeTask(task_id).build_transaction({
                "from": account,
                "nonce": self.w3.eth.get_transaction_count(account),
                "chainId": self.config.chain_id,
            })
            tx_hash = self._sign_and_send(tx)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt["status"] == 1:
                logger.info(f"Task {task_id} completed, tx: {tx_hash}")
                return tx_hash
            return None

        except Exception as e:
            logger.error(f"Failed to complete task {task_id}: {e}")
            return None

    async def verify_task_on_chain(self, task_id: int, is_valid: bool) -> Optional[str]:
        """Verify a submitted task result (only verification engine can call this)."""
        tc = self.config.task_contract
        if not tc:
            return None

        account = self.config.get_account_address()
        try:
            tx = tc.functions.verifyResult(task_id, is_valid).build_transaction({
                "from": account,
                "nonce": self.w3.eth.get_transaction_count(account),
                "chainId": self.config.chain_id,
            })
            tx_hash = self._sign_and_send(tx)
            self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            logger.info(f"Task {task_id} verified (valid={is_valid}), tx: {tx_hash}")
            return tx_hash
        except Exception as e:
            logger.error(f"Failed to verify task {task_id}: {e}")
            return None

    # --- Reward Operations ---

    def get_reward_balance(self, agent_address: str, token: str = "usdc") -> float:
        """Get agent's accumulated reward balance in RewardContract."""
        rc = self.config.reward_contract
        if not rc:
            return 0.0

        token_address = self.config.get_token_address(token)
        if not token_address:
            return 0.0

        try:
            raw = rc.functions.getBalance(
                Web3.to_checksum_address(agent_address),
                Web3.to_checksum_address(token_address),
            ).call()
            return from_token_units(raw)
        except Exception as e:
            logger.error(f"Failed to get reward balance: {e}")
            return 0.0

    async def withdraw_reward(self, token: str = "usdc") -> Optional[str]:
        """Withdraw all accumulated rewards for a token."""
        rc = self.config.reward_contract
        if not rc:
            return None

        account = self.config.get_account_address()
        token_address = self.config.get_token_address(token)
        if not account or not token_address:
            return None

        try:
            tx = rc.functions.withdrawReward(
                Web3.to_checksum_address(token_address)
            ).build_transaction({
                "from": account,
                "nonce": self.w3.eth.get_transaction_count(account),
                "chainId": self.config.chain_id,
            })
            tx_hash = self._sign_and_send(tx)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt["status"] == 1:
                logger.info(f"Reward withdrawn ({token.upper()}), tx: {tx_hash}")
                return tx_hash
            return None

        except Exception as e:
            logger.error(f"Failed to withdraw reward: {e}")
            return None

    # --- Query Operations ---

    def get_task_from_chain(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task details from TaskContract."""
        tc = self.config.task_contract
        if not tc:
            return None

        try:
            t = tc.functions.getTask(task_id).call()
            return {
                "task_id": t[0],
                "publisher": t[1],
                "description": t[2],
                "input_data": t[3],
                "expected_output": t[4],
                "reward": from_token_units(t[5]),
                "payment_token": t[6],
                "task_type": t[7],
                "status": t[8],
                "agent": t[9],
                "result": t[10],
            }
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None

    def get_wallet_summary(self, address: str) -> Dict[str, Any]:
        """Get wallet summary: ETH + USDC + USDT balances + reward balance."""
        return {
            "address": address,
            "eth_balance": self.config.get_eth_balance(address),
            "usdc_balance": self.config.get_usdc_balance(address),
            "usdt_balance": self.config.get_usdt_balance(address),
            "reward_usdc": self.get_reward_balance(address, "usdc"),
            "reward_usdt": self.get_reward_balance(address, "usdt"),
            "network": self.config.network_name,
            "chain_id": self.config.chain_id,
        }

    # --- Internal ---

    def _sign_and_send(self, tx: dict) -> str:
        """Sign and send a transaction. Returns tx hash hex."""
        from blockchain.web3_config import BLOCKCHAIN_PRIVATE_KEY
        if not BLOCKCHAIN_PRIVATE_KEY:
            raise ValueError("BLOCKCHAIN_PRIVATE_KEY not set")

        signed = self.w3.eth.account.sign_transaction(tx, BLOCKCHAIN_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        return tx_hash.hex()


# Singleton
_service: Optional[BlockchainService] = None


def get_blockchain_service() -> BlockchainService:
    global _service
    if _service is None:
        _service = BlockchainService()
    return _service
