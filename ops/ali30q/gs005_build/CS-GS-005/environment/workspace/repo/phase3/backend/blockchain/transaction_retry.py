"""
交易重试机制
提供智能的交易重试策略，处理交易失败、Gas不足等问题
"""
import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from web3 import Web3
from web3.exceptions import ContractLogicError, TimeExhausted
from eth_account.datastructures import SignedTransaction

from blockchain.web3_config import get_web3_config, get_w3

logger = logging.getLogger(__name__)


class TransactionRetryConfig:
    """交易重试配置"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 2.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
        gas_price_increase_factor: float = 1.1,
        timeout: int = 120
    ):
        """
        初始化重试配置

        Args:
            max_retries: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            backoff_factor: 退避因子
            gas_price_increase_factor: Gas价格增长因子
            timeout: 交易超时时间（秒）
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.gas_price_increase_factor = gas_price_increase_factor
        self.timeout = timeout


class TransactionRetryManager:
    """交易重试管理器"""

    def __init__(self, config: Optional[TransactionRetryConfig] = None):
        """
        初始化重试管理器

        Args:
            config: 重试配置，如果为None则使用默认配置
        """
        self.config = config or TransactionRetryConfig()
        self.web3_config = get_web3_config()
        self.w3 = get_w3()

    async def execute_with_retry(
        self,
        transaction_builder: Callable[[], Dict[str, Any]],
        operation_name: str = "Transaction"
    ) -> Optional[str]:
        """
        执行交易并在失败时重试（异步版本）

        Args:
            transaction_builder: 构建交易的函数
            operation_name: 操作名称（用于日志）

        Returns:
            交易哈希，如果失败返回None
        """
        retry_count = 0
        delay = self.config.initial_delay
        last_error = None

        while retry_count <= self.config.max_retries:
            try:
                # 构建交易
                transaction = transaction_builder()

                # 如果是重试，增加Gas价格
                if retry_count > 0:
                    gas_price_multiplier = self.config.gas_price_increase_factor ** retry_count
                    transaction['gasPrice'] = int(transaction['gasPrice'] * gas_price_multiplier)
                    logger.info(
                        f"{operation_name} retry {retry_count}: "
                        f"Increased gas price to {self.w3.from_wei(transaction['gasPrice'], 'gwei')} Gwei"
                    )

                # 发送交易
                tx_hash = self._send_transaction(transaction)

                if tx_hash:
                    logger.info(f"{operation_name} successful: {tx_hash}")
                    return tx_hash

            except ContractLogicError as e:
                # 合约逻辑错误，不重试
                logger.error(f"{operation_name} contract logic error: {e}")
                return None

            except TimeExhausted as e:
                # 超时错误，可以重试
                last_error = e
                logger.warning(f"{operation_name} timeout (attempt {retry_count + 1}): {e}")

            except ValueError as e:
                # Gas不足或其他值错误
                error_msg = str(e)
                last_error = e

                if "insufficient funds" in error_msg.lower():
                    logger.error(f"{operation_name} insufficient funds: {e}")
                    return None
                elif "gas" in error_msg.lower():
                    logger.warning(f"{operation_name} gas error (attempt {retry_count + 1}): {e}")
                else:
                    logger.error(f"{operation_name} value error: {e}")
                    return None

            except Exception as e:
                # 其他错误
                last_error = e
                logger.warning(f"{operation_name} error (attempt {retry_count + 1}): {e}")

            # 如果还有重试机会，等待后重试
            if retry_count < self.config.max_retries:
                logger.info(f"Retrying {operation_name} in {delay} seconds...")
                await asyncio.sleep(delay)  # Non-blocking async sleep
                delay = min(delay * self.config.backoff_factor, self.config.max_delay)
                retry_count += 1
            else:
                break

        # 所有重试都失败
        logger.error(
            f"{operation_name} failed after {self.config.max_retries} retries. "
            f"Last error: {last_error}"
        )
        return None

    def _send_transaction(self, transaction: Dict[str, Any]) -> Optional[str]:
        """
        发送交易并等待确认

        Args:
            transaction: 交易字典

        Returns:
            交易哈希，如果失败返回None
        """
        try:
            # 发送交易
            tx_hash = self.web3_config.send_transaction(transaction)

            # 等待交易确认
            receipt = self.web3_config.wait_for_transaction(
                tx_hash,
                timeout=self.config.timeout
            )

            # 检查交易状态
            if receipt.get('status') == 1:
                return tx_hash
            else:
                logger.error(f"Transaction failed: {tx_hash}")
                return None

        except Exception as e:
            logger.error(f"Failed to send transaction: {e}")
            raise

    def estimate_gas_with_buffer(
        self,
        transaction: Dict[str, Any],
        buffer_percent: float = 20.0
    ) -> int:
        """
        估算Gas并添加缓冲

        Args:
            transaction: 交易字典
            buffer_percent: 缓冲百分比

        Returns:
            估算的Gas限制
        """
        try:
            estimated_gas = self.w3.eth.estimate_gas(transaction)
            gas_with_buffer = int(estimated_gas * (1 + buffer_percent / 100))

            logger.info(
                f"Gas estimation: {estimated_gas} "
                f"(with {buffer_percent}% buffer: {gas_with_buffer})"
            )

            return gas_with_buffer

        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}, using default")
            return 500000  # 默认Gas限制

    def get_optimal_gas_price(self, priority: str = "standard") -> int:
        """
        获取最优Gas价格

        Args:
            priority: 优先级 ("low", "standard", "high")

        Returns:
            Gas价格（Wei）
        """
        try:
            base_gas_price = self.w3.eth.gas_price

            # 根据优先级调整
            multipliers = {
                "low": 0.9,
                "standard": 1.0,
                "high": 1.2
            }

            multiplier = multipliers.get(priority, 1.0)
            optimal_price = int(base_gas_price * multiplier)

            logger.info(
                f"Optimal gas price ({priority}): "
                f"{self.w3.from_wei(optimal_price, 'gwei')} Gwei"
            )

            return optimal_price

        except Exception as e:
            logger.error(f"Failed to get optimal gas price: {e}")
            return self.w3.eth.gas_price

    def check_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """
        检查交易状态

        Args:
            tx_hash: 交易哈希

        Returns:
            交易状态信息
        """
        try:
            # 获取交易回执
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)

            # 获取交易详情
            transaction = self.w3.eth.get_transaction(tx_hash)

            status_info = {
                'status': 'success' if receipt['status'] == 1 else 'failed',
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'gas_price': transaction['gasPrice'],
                'total_cost': receipt['gasUsed'] * transaction['gasPrice'],
                'confirmations': self.w3.eth.block_number - receipt['blockNumber']
            }

            return status_info

        except Exception as e:
            logger.error(f"Failed to check transaction status: {e}")
            return {'status': 'unknown', 'error': str(e)}

    def cancel_transaction(
        self,
        nonce: int,
        gas_price_multiplier: float = 1.5
    ) -> Optional[str]:
        """
        取消待处理的交易（通过发送相同nonce的空交易）

        Args:
            nonce: 要取消的交易的nonce
            gas_price_multiplier: Gas价格倍数（必须高于原交易）

        Returns:
            取消交易的哈希，如果失败返回None
        """
        try:
            account = self.web3_config.get_account()
            if not account:
                logger.error("No account configured")
                return None

            # 获取当前Gas价格并增加
            current_gas_price = self.w3.eth.gas_price
            cancel_gas_price = int(current_gas_price * gas_price_multiplier)

            # 构建取消交易（发送0 ETH给自己）
            cancel_transaction = {
                'from': account,
                'to': account,
                'value': 0,
                'gas': 21000,  # 最小Gas
                'gasPrice': cancel_gas_price,
                'nonce': nonce
            }

            # 发送取消交易
            tx_hash = self.web3_config.send_transaction(cancel_transaction)

            logger.info(f"Cancel transaction sent: {tx_hash} (nonce: {nonce})")
            return tx_hash

        except Exception as e:
            logger.error(f"Failed to cancel transaction: {e}")
            return None


# 全局重试管理器实例
_retry_manager: Optional[TransactionRetryManager] = None


def get_retry_manager() -> TransactionRetryManager:
    """获取重试管理器实例（单例）"""
    global _retry_manager

    if _retry_manager is None:
        _retry_manager = TransactionRetryManager()

    return _retry_manager


def execute_transaction_with_retry(
    transaction_builder: Callable[[], Dict[str, Any]],
    operation_name: str = "Transaction",
    config: Optional[TransactionRetryConfig] = None
) -> Optional[str]:
    """
    便捷函数：执行交易并在失败时重试

    Args:
        transaction_builder: 构建交易的函数
        operation_name: 操作名称
        config: 重试配置

    Returns:
        交易哈希，如果失败返回None
    """
    if config:
        manager = TransactionRetryManager(config)
    else:
        manager = get_retry_manager()

    return manager.execute_with_retry(transaction_builder, operation_name)
