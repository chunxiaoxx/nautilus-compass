"""
区块链事件监听器
监听智能合约事件并同步到数据库
支持重连机制、错误处理和事件缓存
"""
import asyncio
import logging
from typing import Optional, Callable, Dict, Any, List
from collections import deque
from datetime import datetime
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import BlockNotFound

from blockchain.web3_config import (
    get_web3_config,
    get_w3,
    get_task_market,
    get_reward_pool,
    get_agent_registry
)

logger = logging.getLogger(__name__)


class EventCache:
    """事件缓存"""

    def __init__(self, max_size: int = 1000):
        """
        初始化事件缓存

        Args:
            max_size: 最大缓存大小
        """
        self.cache: deque = deque(maxlen=max_size)
        self.processed_events: set = set()  # 已处理事件的哈希

    def add_event(self, event: Dict[str, Any]) -> bool:
        """
        添加事件到缓存

        Args:
            event: 事件数据

        Returns:
            是否成功添加（如果事件已存在则返回False）
        """
        event_hash = self._get_event_hash(event)

        if event_hash in self.processed_events:
            return False

        self.cache.append({
            'event': event,
            'timestamp': datetime.now(),
            'hash': event_hash
        })
        self.processed_events.add(event_hash)

        # 清理旧的哈希记录
        if len(self.processed_events) > self.cache.maxlen * 2:
            self._cleanup_old_hashes()

        return True

    def _get_event_hash(self, event: Dict[str, Any]) -> str:
        """生成事件哈希"""
        try:
            tx_hash = event.get('transactionHash', '').hex() if hasattr(event.get('transactionHash', ''), 'hex') else str(event.get('transactionHash', ''))
            log_index = event.get('logIndex', 0)
            return f"{tx_hash}_{log_index}"
        except Exception:
            return str(hash(str(event)))

    def _cleanup_old_hashes(self):
        """清理旧的哈希记录"""
        current_hashes = {item['hash'] for item in self.cache}
        self.processed_events = current_hashes

    def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """获取最近的事件"""
        return list(self.cache)[-count:]


class BlockchainEventListener:
    """区块链事件监听器（增强版）"""

    def __init__(
        self,
        reconnect_delay: int = 5,
        max_reconnect_attempts: int = 10,
        poll_interval: int = 15,
        max_block_range: int = 1000
    ):
        """
        初始化事件监听器

        Args:
            reconnect_delay: 重连延迟（秒）
            max_reconnect_attempts: 最大重连次数
            poll_interval: 轮询间隔（秒）
            max_block_range: 最大区块范围
        """
        self.config = get_web3_config()
        self.w3 = get_w3()
        self.is_running = False
        self.event_handlers = {}

        # 重连配置
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_count = 0

        # 轮询配置
        self.poll_interval = poll_interval
        self.max_block_range = max_block_range

        # 事件缓存
        self.event_cache = EventCache()

        # 错误统计
        self.error_count = 0
        self.last_error_time = None

        # 区块追踪
        self.last_processed_blocks = {
            'task_market': None,
            'reward_pool': None,
            'agent_registry': None
        }

    def register_handler(self, event_name: str, handler: Callable):
        """
        注册事件处理器

        Args:
            event_name: 事件名称
            handler: 处理函数
        """
        self.event_handlers[event_name] = handler
        logger.info(f"Registered handler for event: {event_name}")

    async def _ensure_connection(self) -> bool:
        """
        确保Web3连接正常

        Returns:
            连接是否正常
        """
        try:
            if not self.w3.is_connected():
                logger.warning("Web3 connection lost, attempting to reconnect...")

                for attempt in range(self.max_reconnect_attempts):
                    try:
                        # 重新初始化连接
                        self.config._initialize_connection()
                        self.w3 = get_w3()

                        if self.w3.is_connected():
                            logger.info(f"Reconnected successfully (attempt {attempt + 1})")
                            self.reconnect_count = 0
                            return True

                    except Exception as e:
                        logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")

                    await asyncio.sleep(self.reconnect_delay)

                logger.error("Failed to reconnect after maximum attempts")
                return False

            return True

        except Exception as e:
            logger.error(f"Connection check failed: {e}")
            return False

    def _get_safe_block_range(self, contract_name: str) -> tuple:
        """
        获取安全的区块范围

        Args:
            contract_name: 合约名称

        Returns:
            (from_block, to_block)
        """
        try:
            current_block = self.w3.eth.block_number
            last_block = self.last_processed_blocks.get(contract_name)

            if last_block is None:
                # 首次运行，从当前区块开始
                from_block = current_block
            else:
                from_block = last_block + 1

            # 限制区块范围
            if current_block - from_block > self.max_block_range:
                to_block = from_block + self.max_block_range
            else:
                to_block = current_block

            return from_block, to_block

        except Exception as e:
            logger.error(f"Failed to get block range: {e}")
            return None, None

    def _update_last_processed_block(self, contract_name: str, block_number: int):
        """更新最后处理的区块"""
        self.last_processed_blocks[contract_name] = block_number

    async def listen_task_market_events(self):
        """监听TaskMarket合约事件（增强版）"""
        task_market = get_task_market()
        if not task_market:
            logger.warning("TaskMarket contract not loaded, skipping event listening")
            return

        logger.info("Starting TaskMarket event listener...")

        while self.is_running:
            try:
                # 确保连接正常
                if not await self._ensure_connection():
                    await asyncio.sleep(self.reconnect_delay)
                    continue

                # 获取安全的区块范围
                from_block, to_block = self._get_safe_block_range('task_market')
                if from_block is None or to_block is None:
                    await asyncio.sleep(self.poll_interval)
                    continue

                # 如果没有新区块，跳过
                if from_block > to_block:
                    await asyncio.sleep(self.poll_interval)
                    continue

                logger.debug(f"Scanning TaskMarket events from block {from_block} to {to_block}")

                # 监听各种事件
                await self._process_events(
                    task_market.events.TaskPublished,
                    from_block,
                    to_block,
                    self._handle_task_published
                )

                await self._process_events(
                    task_market.events.TaskAccepted,
                    from_block,
                    to_block,
                    self._handle_task_accepted
                )

                await self._process_events(
                    task_market.events.TaskSubmitted,
                    from_block,
                    to_block,
                    self._handle_task_submitted
                )

                await self._process_events(
                    task_market.events.TaskCompleted,
                    from_block,
                    to_block,
                    self._handle_task_completed
                )

                # 更新最后处理的区块
                self._update_last_processed_block('task_market', to_block)

                # 等待下一次轮询
                await asyncio.sleep(self.poll_interval)

            except BlockNotFound as e:
                logger.warning(f"Block not found in TaskMarket listener: {e}")
                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                self.error_count += 1
                self.last_error_time = datetime.now()
                logger.error(f"Error listening to TaskMarket events: {e}")
                await asyncio.sleep(self.reconnect_delay)

    async def listen_reward_pool_events(self):
        """监听RewardPool合约事件（增强版）"""
        reward_pool = get_reward_pool()
        if not reward_pool:
            logger.warning("RewardPool contract not loaded, skipping event listening")
            return

        logger.info("Starting RewardPool event listener...")

        while self.is_running:
            try:
                if not await self._ensure_connection():
                    await asyncio.sleep(self.reconnect_delay)
                    continue

                from_block, to_block = self._get_safe_block_range('reward_pool')
                if from_block is None or to_block is None:
                    await asyncio.sleep(self.poll_interval)
                    continue

                if from_block > to_block:
                    await asyncio.sleep(self.poll_interval)
                    continue

                logger.debug(f"Scanning RewardPool events from block {from_block} to {to_block}")

                await self._process_events(
                    reward_pool.events.RewardDistributed,
                    from_block,
                    to_block,
                    self._handle_reward_distributed
                )

                await self._process_events(
                    reward_pool.events.RewardWithdrawn,
                    from_block,
                    to_block,
                    self._handle_reward_withdrawn
                )

                self._update_last_processed_block('reward_pool', to_block)
                await asyncio.sleep(self.poll_interval)

            except BlockNotFound as e:
                logger.warning(f"Block not found in RewardPool listener: {e}")
                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                self.error_count += 1
                self.last_error_time = datetime.now()
                logger.error(f"Error listening to RewardPool events: {e}")
                await asyncio.sleep(self.reconnect_delay)

    async def listen_agent_registry_events(self):
        """监听AgentRegistry合约事件（增强版）"""
        agent_registry = get_agent_registry()
        if not agent_registry:
            logger.warning("AgentRegistry contract not loaded, skipping event listening")
            return

        logger.info("Starting AgentRegistry event listener...")

        while self.is_running:
            try:
                if not await self._ensure_connection():
                    await asyncio.sleep(self.reconnect_delay)
                    continue

                from_block, to_block = self._get_safe_block_range('agent_registry')
                if from_block is None or to_block is None:
                    await asyncio.sleep(self.poll_interval)
                    continue

                if from_block > to_block:
                    await asyncio.sleep(self.poll_interval)
                    continue

                logger.debug(f"Scanning AgentRegistry events from block {from_block} to {to_block}")

                await self._process_events(
                    agent_registry.events.AgentRegistered,
                    from_block,
                    to_block,
                    self._handle_agent_registered
                )

                await self._process_events(
                    agent_registry.events.ReputationUpdated,
                    from_block,
                    to_block,
                    self._handle_reputation_updated
                )

                self._update_last_processed_block('agent_registry', to_block)
                await asyncio.sleep(self.poll_interval)

            except BlockNotFound as e:
                logger.warning(f"Block not found in AgentRegistry listener: {e}")
                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                self.error_count += 1
                self.last_error_time = datetime.now()
                logger.error(f"Error listening to AgentRegistry events: {e}")
                await asyncio.sleep(self.reconnect_delay)

    async def _process_events(
        self,
        event_filter,
        from_block: int,
        to_block: int,
        handler: Callable
    ):
        """
        处理事件

        Args:
            event_filter: 事件过滤器
            from_block: 起始区块
            to_block: 结束区块
            handler: 事件处理函数
        """
        try:
            # 创建事件过滤器
            events = event_filter.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            ).get_all_entries()

            # 处理每个事件
            for event in events:
                # 检查事件是否已处理（去重）
                if self.event_cache.add_event(event):
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Error handling event: {e}")

        except Exception as e:
            logger.error(f"Error processing events: {e}")
            raise

    # ==================== 事件处理方法 ====================

    async def _handle_task_published(self, event):
        """处理TaskPublished事件"""
        try:
            logger.info(f"TaskPublished event: {event}")

            task_id = event['args']['taskId']
            creator = event['args']['creator']
            reward = event['args']['reward']

            # 调用注册的处理器
            if 'TaskPublished' in self.event_handlers:
                await self.event_handlers['TaskPublished'](task_id, creator, reward)

        except Exception as e:
            logger.error(f"Error handling TaskPublished event: {e}")

    async def _handle_task_accepted(self, event):
        """处理TaskAccepted事件"""
        try:
            logger.info(f"TaskAccepted event: {event}")

            task_id = event['args']['taskId']
            agent = event['args']['agent']

            if 'TaskAccepted' in self.event_handlers:
                await self.event_handlers['TaskAccepted'](task_id, agent)

        except Exception as e:
            logger.error(f"Error handling TaskAccepted event: {e}")

    async def _handle_task_submitted(self, event):
        """处理TaskSubmitted事件"""
        try:
            logger.info(f"TaskSubmitted event: {event}")

            task_id = event['args']['taskId']
            agent = event['args']['agent']

            if 'TaskSubmitted' in self.event_handlers:
                await self.event_handlers['TaskSubmitted'](task_id, agent)

        except Exception as e:
            logger.error(f"Error handling TaskSubmitted event: {e}")

    async def _handle_task_completed(self, event):
        """处理TaskCompleted事件"""
        try:
            logger.info(f"TaskCompleted event: {event}")

            task_id = event['args']['taskId']
            agent = event['args']['agent']
            reward = event['args']['reward']

            if 'TaskCompleted' in self.event_handlers:
                await self.event_handlers['TaskCompleted'](task_id, agent, reward)

        except Exception as e:
            logger.error(f"Error handling TaskCompleted event: {e}")

    async def _handle_reward_distributed(self, event):
        """处理RewardDistributed事件"""
        try:
            logger.info(f"RewardDistributed event: {event}")

            agent = event['args']['agent']
            amount = event['args']['amount']
            task_id = event['args']['taskId']

            if 'RewardDistributed' in self.event_handlers:
                await self.event_handlers['RewardDistributed'](agent, amount, task_id)

        except Exception as e:
            logger.error(f"Error handling RewardDistributed event: {e}")

    async def _handle_reward_withdrawn(self, event):
        """处理RewardWithdrawn事件"""
        try:
            logger.info(f"RewardWithdrawn event: {event}")

            agent = event['args']['agent']
            amount = event['args']['amount']

            if 'RewardWithdrawn' in self.event_handlers:
                await self.event_handlers['RewardWithdrawn'](agent, amount)

        except Exception as e:
            logger.error(f"Error handling RewardWithdrawn event: {e}")

    async def _handle_agent_registered(self, event):
        """处理AgentRegistered事件"""
        try:
            logger.info(f"AgentRegistered event: {event}")

            agent = event['args']['agent']
            name = event['args']['name']

            if 'AgentRegistered' in self.event_handlers:
                await self.event_handlers['AgentRegistered'](agent, name)

        except Exception as e:
            logger.error(f"Error handling AgentRegistered event: {e}")

    async def _handle_reputation_updated(self, event):
        """处理ReputationUpdated事件"""
        try:
            logger.info(f"ReputationUpdated event: {event}")

            agent = event['args']['agent']
            new_reputation = event['args']['newReputation']

            if 'ReputationUpdated' in self.event_handlers:
                await self.event_handlers['ReputationUpdated'](agent, new_reputation)

        except Exception as e:
            logger.error(f"Error handling ReputationUpdated event: {e}")

    # ==================== 控制方法 ====================

    async def start(self):
        """启动事件监听器"""
        if self.is_running:
            logger.warning("Event listener is already running")
            return

        self.is_running = True
        logger.info("Starting blockchain event listeners...")

        # 并发运行所有监听器
        try:
            await asyncio.gather(
                self.listen_task_market_events(),
                self.listen_reward_pool_events(),
                self.listen_agent_registry_events(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Event listener error: {e}")
            self.is_running = False

    def stop(self):
        """停止事件监听器"""
        logger.info("Stopping blockchain event listeners...")
        self.is_running = False

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取监听器统计信息

        Returns:
            统计信息字典
        """
        return {
            'is_running': self.is_running,
            'error_count': self.error_count,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'reconnect_count': self.reconnect_count,
            'cached_events': len(self.event_cache.cache),
            'last_processed_blocks': self.last_processed_blocks.copy()
        }

    def get_recent_events(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        获取最近的事件

        Args:
            count: 返回的事件数量

        Returns:
            事件列表
        """
        return self.event_cache.get_recent_events(count)


# 全局事件监听器实例
_event_listener: Optional[BlockchainEventListener] = None


def get_event_listener() -> BlockchainEventListener:
    """获取事件监听器实例（单例）"""
    global _event_listener

    if _event_listener is None:
        _event_listener = BlockchainEventListener()

    return _event_listener


async def start_event_listener():
    """启动事件监听器"""
    listener = get_event_listener()
    await listener.start()


def stop_event_listener():
    """停止事件监听器"""
    listener = get_event_listener()
    listener.stop()


if __name__ == "__main__":
    """测试事件监听器"""
    import asyncio

    async def test_listener():
        listener = get_event_listener()

        # 注册测试处理器
        async def handle_task_published(task_id, creator, reward):
            print(f"Task published: {task_id} by {creator}, reward: {reward}")

        listener.register_handler('TaskPublished', handle_task_published)

        # 启动监听器
        await listener.start()

    asyncio.run(test_listener())
