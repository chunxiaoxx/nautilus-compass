"""
MEME Token Python interface for Nautilus project.

Provides Python interface to interact with MEMEToken smart contract.
"""

from typing import Dict, Tuple, Optional
from web3 import Web3
from eth_account import Account


class MEMEToken:
    """
    Python interface for MEMEToken smart contract.

    Handles:
    - Mining reward claims
    - Token balance queries
    - Statistics retrieval
    """

    def __init__(
        self,
        web3: Web3,
        contract_address: str,
        contract_abi: list
    ):
        """
        Initialize MEME Token interface.

        Args:
            web3: Web3 instance
            contract_address: Deployed contract address
            contract_abi: Contract ABI
        """
        self.web3 = web3
        self.contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=contract_abi
        )

    def claim_mining_reward(
        self,
        proof_id: bytes,
        agent_address: str,
        task_id: bytes,
        result_hash: bytes,
        nonce: int,
        private_key: str
    ) -> Dict:
        """
        Claim mining reward for verified PoW proof.

        Args:
            proof_id: Proof ID (32 bytes)
            agent_address: Agent address
            task_id: Task ID (32 bytes)
            result_hash: Result hash (32 bytes)
            nonce: PoW nonce
            private_key: Private key for signing transaction

        Returns:
            Transaction receipt
        """
        account = Account.from_key(private_key)

        # Build transaction
        tx = self.contract.functions.claimMiningReward(
            proof_id,
            Web3.to_checksum_address(agent_address),
            task_id,
            result_hash,
            nonce
        ).build_transaction({
            'from': account.address,
            'nonce': self.web3.eth.get_transaction_count(account.address),
            'gas': 200000,
            'gasPrice': self.web3.eth.gas_price
        })

        # Sign and send transaction
        signed_tx = account.sign_transaction(tx)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        # Wait for receipt
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            'tx_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber'],
            'gas_used': receipt['gasUsed'],
            'status': receipt['status']
        }

    def get_balance(self, address: str) -> int:
        """
        Get token balance for address.

        Args:
            address: Ethereum address

        Returns:
            Token balance in wei
        """
        return self.contract.functions.balanceOf(
            Web3.to_checksum_address(address)
        ).call()

    def get_current_reward(self) -> int:
        """
        Get current mining reward.

        Returns:
            Current reward in wei
        """
        return self.contract.functions.getCurrentReward().call()

    def is_proof_claimed(self, proof_id: bytes) -> bool:
        """
        Check if proof has been claimed.

        Args:
            proof_id: Proof ID (32 bytes)

        Returns:
            True if claimed, False otherwise
        """
        return self.contract.functions.isProofClaimed(proof_id).call()

    def get_agent_stats(self, agent_address: str) -> Dict:
        """
        Get agent mining statistics.

        Args:
            agent_address: Agent address

        Returns:
            Dictionary with mined and balance
        """
        mined, balance = self.contract.functions.getAgentStats(
            Web3.to_checksum_address(agent_address)
        ).call()

        return {
            'mined': mined,
            'balance': balance
        }

    def get_token_stats(self) -> Dict:
        """
        Get token statistics.

        Returns:
            Dictionary with token statistics
        """
        (
            current_supply,
            max_supply,
            total_mined,
            current_reward,
            blocks_until_halving
        ) = self.contract.functions.getTokenStats().call()

        return {
            'current_supply': current_supply,
            'max_supply': max_supply,
            'total_mined': total_mined,
            'current_reward': current_reward,
            'blocks_until_halving': blocks_until_halving,
            'supply_percentage': (current_supply / max_supply) * 100
        }

    def get_total_supply(self) -> int:
        """
        Get total token supply.

        Returns:
            Total supply in wei
        """
        return self.contract.functions.totalSupply().call()

    def get_max_supply(self) -> int:
        """
        Get maximum token supply.

        Returns:
            Max supply in wei
        """
        return self.contract.functions.MAX_SUPPLY().call()

    def get_pow_contract(self) -> str:
        """
        Get PoW Proof contract address.

        Returns:
            Contract address
        """
        return self.contract.functions.powProofContract().call()

    @staticmethod
    def wei_to_tokens(wei_amount: int) -> float:
        """
        Convert wei to token amount.

        Args:
            wei_amount: Amount in wei

        Returns:
            Amount in tokens
        """
        return wei_amount / 10**18

    @staticmethod
    def tokens_to_wei(token_amount: float) -> int:
        """
        Convert token amount to wei.

        Args:
            token_amount: Amount in tokens

        Returns:
            Amount in wei
        """
        return int(token_amount * 10**18)
