"""
NautilusToken (NAU) mint service.

Proof of Useful Work: agents earn NAU by completing real computational tasks.
Mint is non-blocking — failures are logged but never raise exceptions to callers.
"""
import logging
import os
from datetime import datetime
from typing import Optional

import redis as redis_lib
from blockchain.web3_config import get_web3_config, get_w3, BLOCKCHAIN_PRIVATE_KEY
from web3 import Web3

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

logger = logging.getLogger(__name__)

# NAU reward per task type (in whole NAU units, converted to wei on send)
TASK_TYPE_REWARDS: dict[str, int] = {
    "physics_simulation": 10,
    "pde_simulation": 10,
    "ode_simulation": 5,
    "ml_training": 5,
    "monte_carlo": 5,
    "jc_constitutive": 5,
    "thmc_coupling": 5,
    "curve_fitting": 3,
    "statistical_analysis": 3,
    "data_visualization": 1,
    "general_computation": 1,
    # DeerFlow research pipeline (multi-agent, higher value)
    "research_synthesis": 8,
    # Platform self-improvement (sandbox-promoted proposals)
    "platform_improvement": 15,
    # Multimodal task types
    "image_analysis": 2,
    "audio_transcription": 3,
    "tts_generation": 1,
    "document_analysis": 3,
    "image_generation": 2,
}

_NAU_DECIMALS = 18


class NautilusTokenService:
    """Handles NAU token minting for Proof of Useful Work rewards."""

    @staticmethod
    async def mint_task_reward(
        agent_wallet: str,
        task_type: str,
    ) -> Optional[str]:
        """
        Mint NAU to agent wallet on task completion.

        Returns tx_hash hex string on success, None on any failure.
        Never raises — callers should not depend on this succeeding.
        """
        if not agent_wallet:
            return None

        cfg = get_web3_config()
        if not cfg.nau_contract:
            logger.debug("NAU contract not loaded, skipping mint")
            return None

        if not BLOCKCHAIN_PRIVATE_KEY:
            logger.debug("BLOCKCHAIN_PRIVATE_KEY not set, skipping mint")
            return None

        nau_amount = TASK_TYPE_REWARDS.get(task_type, 1)
        amount_wei = nau_amount * (10 ** _NAU_DECIMALS)

        try:
            w3 = get_w3()
            account = cfg.get_account_address()
            if not account:
                logger.warning("Cannot derive account address from private key")
                return None

            checksum_wallet = Web3.to_checksum_address(agent_wallet)
            nonce = w3.eth.get_transaction_count(account)

            tx = cfg.nau_contract.functions.mintForTask(
                checksum_wallet,
                amount_wei,
                task_type,
            ).build_transaction({
                "from": account,
                "nonce": nonce,
                "chainId": cfg.chain_id,
            })

            signed = w3.eth.account.sign_transaction(tx, BLOCKCHAIN_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(
                "Minted %d NAU to %s for %s task, tx: %s",
                nau_amount, agent_wallet, task_type, tx_hash_hex,
            )
            try:
                r = redis_lib.from_url(REDIS_URL, decode_responses=True)
                today = datetime.utcnow().strftime("%Y-%m-%d")
                r.incrbyfloat(f"nau:minted_today:{today}", nau_amount)
                r.expire(f"nau:minted_today:{today}", 86400 * 7)
            except Exception:
                pass  # Redis 不可用时静默

            # Bridge E.5: NAU reward → Reputation update
            try:
                from services.reputation import update_reputation_on_reward
                update_reputation_on_reward(agent_wallet, nau_amount, task_type)
            except Exception:
                pass  # Reputation failure must never block mint

            return tx_hash_hex

        except Exception as e:
            logger.warning("NAU mint failed for %s (%s): %s", agent_wallet, task_type, e)
            try:
                r = redis_lib.from_url(REDIS_URL, decode_responses=True)
                today = datetime.utcnow().strftime("%Y-%m-%d")
                r.incr(f"nau:mint_failures:{today}")
                r.expire(f"nau:mint_failures:{today}", 86400 * 7)
            except Exception:
                pass  # Redis 不可用时静默
            return None

    @staticmethod
    async def mint_collaborative_reward(
        coordinator_wallet: str,
        researcher_wallets: list[str],
        task_type: str,
    ) -> list[str]:
        """
        Mint NAU for a collaborative DeerFlow task.

        Distribution: Coordinator 40%, Researchers split 60% equally.
        Returns list of tx_hashes (one per participant).
        Falls back to single mint to coordinator if no researchers.
        """
        if not coordinator_wallet:
            return []

        total_nau = TASK_TYPE_REWARDS.get(task_type, 1)
        tx_hashes = []

        if not researcher_wallets:
            # No collaborators — single mint
            tx = await NautilusTokenService.mint_task_reward(coordinator_wallet, task_type)
            return [tx] if tx else []

        # Coordinator gets 40%
        coordinator_nau = max(1, int(total_nau * 0.4))
        # Researchers split 60% equally
        researcher_total = total_nau - coordinator_nau
        per_researcher = max(1, researcher_total // len(researcher_wallets))

        cfg = get_web3_config()
        if not cfg.nau_contract or not BLOCKCHAIN_PRIVATE_KEY:
            logger.debug("NAU contract/key not configured, skipping collaborative mint")
            return []

        w3 = get_w3()
        account = cfg.get_account_address()
        if not account:
            return []

        participants = (
            [(coordinator_wallet, coordinator_nau, "coordinator")] +
            [(w, per_researcher, f"researcher_{i}") for i, w in enumerate(researcher_wallets)]
        )

        for wallet, nau_amount, role in participants:
            if not wallet:
                continue
            try:
                amount_wei = nau_amount * (10 ** _NAU_DECIMALS)
                nonce = w3.eth.get_transaction_count(account) + len(tx_hashes)
                tx = cfg.nau_contract.functions.mintForTask(
                    Web3.to_checksum_address(wallet),
                    amount_wei,
                    f"{task_type}:{role}",
                ).build_transaction({
                    "from": account,
                    "nonce": nonce,
                    "chainId": cfg.chain_id,
                })
                signed = w3.eth.account.sign_transaction(tx, BLOCKCHAIN_PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                tx_hashes.append(tx_hash.hex())
                logger.info("Minted %d NAU to %s (%s), tx: %s",
                            nau_amount, wallet, role, tx_hash.hex())
                try:
                    r = redis_lib.from_url(REDIS_URL, decode_responses=True)
                    today = datetime.utcnow().strftime("%Y-%m-%d")
                    r.incrbyfloat(f"nau:minted_today:{today}", nau_amount)
                    r.expire(f"nau:minted_today:{today}", 86400 * 7)
                except Exception:
                    pass
            except Exception as e:
                logger.warning("Collaborative mint failed for %s (%s): %s", wallet, role, e)
                try:
                    r = redis_lib.from_url(REDIS_URL, decode_responses=True)
                    today = datetime.utcnow().strftime("%Y-%m-%d")
                    r.incr(f"nau:mint_failures:{today}")
                    r.expire(f"nau:mint_failures:{today}", 86400 * 7)
                except Exception:
                    pass

        return tx_hashes
