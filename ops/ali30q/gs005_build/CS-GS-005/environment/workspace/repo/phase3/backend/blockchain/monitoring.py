"""
区块链监控模块
监控交易状态、Gas费用、区块链连接等
"""
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

from web3 import Web3
from blockchain.web3_config import get_web3_config, get_w3

logger = logging.getLogger(__name__)


@dataclass
class TransactionMetrics:
    """交易指标"""
    tx_hash: str
    timestamp: datetime
    status: str  # pending, success, failed
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    total_cost: Optional[int] = None
    confirmations: int = 0
    operation_type: str = ""
    error_message: Optional[str] = None


@dataclass
class GasMetrics:
    """Gas费用指标"""
    timestamp: datetime
    gas_price: int  # Wei
    gas_price_gwei: float
    network_congestion: str  # low, medium, high


@dataclass
class ConnectionMetrics:
    """连接指标"""
    timestamp: datetime
    is_connected: bool
    block_number: Optional[int] = None
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None


class BlockchainMonitor:
    """区块链监控器"""

    def __init__(self, max_history: int = 1000):
        """
        初始化监控器

        Args:
            max_history: 保留的历史记录最大数量
        """
        self.web3_config = get_web3_config()
        self.w3 = get_w3()
        self.max_history = max_history

        # 指标存储
        self.transaction_metrics: deque = deque(maxlen=max_history)
        self.gas_metrics: deque = deque(maxlen=max_history)
        self.connection_metrics: deque = deque(maxlen=max_history)

        # 统计数据
        self.stats = {
            'total_transactions': 0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'pending_transactions': 0,
            'total_gas_cost': 0,
            'average_gas_price': 0,
            'connection_failures': 0,
            'last_check_time': None
        }

        # 线程锁
        self.lock = Lock()

        logger.info("Blockchain monitor initialized")

    # ==================== 交易监控 ====================

    def track_transaction(
        self,
        tx_hash: str,
        operation_type: str = ""
    ) -> TransactionMetrics:
        """
        跟踪交易

        Args:
            tx_hash: 交易哈希
            operation_type: 操作类型

        Returns:
            交易指标
        """
        try:
            metrics = TransactionMetrics(
                tx_hash=tx_hash,
                timestamp=datetime.now(),
                status='pending',
                operation_type=operation_type
            )

            with self.lock:
                self.transaction_metrics.append(metrics)
                self.stats['total_transactions'] += 1
                self.stats['pending_transactions'] += 1

            logger.info(f"Tracking transaction: {tx_hash} ({operation_type})")
            return metrics

        except Exception as e:
            logger.error(f"Failed to track transaction: {e}")
            return None

    def update_transaction_status(self, tx_hash: str) -> Optional[TransactionMetrics]:
        """
        更新交易状态

        Args:
            tx_hash: 交易哈希

        Returns:
            更新后的交易指标
        """
        try:
            # 查找交易指标
            metrics = None
            with self.lock:
                for m in self.transaction_metrics:
                    if m.tx_hash == tx_hash:
                        metrics = m
                        break

            if not metrics:
                logger.warning(f"Transaction not found in tracking: {tx_hash}")
                return None

            # 获取交易回执
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            transaction = self.w3.eth.get_transaction(tx_hash)

            # 更新指标
            with self.lock:
                if receipt['status'] == 1:
                    metrics.status = 'success'
                    self.stats['successful_transactions'] += 1
                else:
                    metrics.status = 'failed'
                    self.stats['failed_transactions'] += 1

                if metrics.status != 'pending':
                    self.stats['pending_transactions'] -= 1

                metrics.gas_used = receipt['gasUsed']
                metrics.gas_price = transaction['gasPrice']
                metrics.total_cost = receipt['gasUsed'] * transaction['gasPrice']
                metrics.confirmations = self.w3.eth.block_number - receipt['blockNumber']

                # 更新统计
                self.stats['total_gas_cost'] += metrics.total_cost

            logger.info(
                f"Transaction {tx_hash} status: {metrics.status}, "
                f"gas used: {metrics.gas_used}, cost: {self.w3.from_wei(metrics.total_cost, 'ether')} ETH"
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to update transaction status: {e}")

            # 标记为失败
            if metrics:
                with self.lock:
                    metrics.status = 'failed'
                    metrics.error_message = str(e)
                    self.stats['failed_transactions'] += 1
                    if metrics.status == 'pending':
                        self.stats['pending_transactions'] -= 1

            return None

    def get_transaction_metrics(self, tx_hash: str) -> Optional[TransactionMetrics]:
        """
        获取交易指标

        Args:
            tx_hash: 交易哈希

        Returns:
            交易指标
        """
        with self.lock:
            for metrics in self.transaction_metrics:
                if metrics.tx_hash == tx_hash:
                    return metrics
        return None

    def get_pending_transactions(self) -> List[TransactionMetrics]:
        """获取所有待处理的交易"""
        with self.lock:
            return [m for m in self.transaction_metrics if m.status == 'pending']

    # ==================== Gas费用监控 ====================

    def record_gas_price(self) -> Optional[GasMetrics]:
        """
        记录当前Gas价格

        Returns:
            Gas指标
        """
        try:
            gas_price = self.w3.eth.gas_price
            gas_price_gwei = self.w3.from_wei(gas_price, 'gwei')

            # 判断网络拥堵程度
            congestion = self._assess_network_congestion(gas_price_gwei)

            metrics = GasMetrics(
                timestamp=datetime.now(),
                gas_price=gas_price,
                gas_price_gwei=gas_price_gwei,
                network_congestion=congestion
            )

            with self.lock:
                self.gas_metrics.append(metrics)

                # 更新平均Gas价格
                if len(self.gas_metrics) > 0:
                    total_gas = sum(m.gas_price for m in self.gas_metrics)
                    self.stats['average_gas_price'] = total_gas // len(self.gas_metrics)

            logger.debug(f"Gas price recorded: {gas_price_gwei:.2f} Gwei ({congestion} congestion)")
            return metrics

        except Exception as e:
            logger.error(f"Failed to record gas price: {e}")
            return None

    def _assess_network_congestion(self, gas_price_gwei: float) -> str:
        """
        评估网络拥堵程度

        Args:
            gas_price_gwei: Gas价格（Gwei）

        Returns:
            拥堵程度 (low, medium, high)
        """
        # 基于Sepolia测试网的阈值
        if gas_price_gwei < 2.0:
            return 'low'
        elif gas_price_gwei < 5.0:
            return 'medium'
        else:
            return 'high'

    def get_gas_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取Gas统计信息

        Args:
            hours: 统计时间范围（小时）

        Returns:
            统计信息字典
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with self.lock:
                recent_metrics = [
                    m for m in self.gas_metrics
                    if m.timestamp >= cutoff_time
                ]

            if not recent_metrics:
                return {
                    'period_hours': hours,
                    'sample_count': 0,
                    'error': 'No data available'
                }

            gas_prices = [m.gas_price_gwei for m in recent_metrics]

            return {
                'period_hours': hours,
                'sample_count': len(recent_metrics),
                'current_gas_price_gwei': gas_prices[-1] if gas_prices else 0,
                'average_gas_price_gwei': sum(gas_prices) / len(gas_prices),
                'min_gas_price_gwei': min(gas_prices),
                'max_gas_price_gwei': max(gas_prices),
                'current_congestion': recent_metrics[-1].network_congestion if recent_metrics else 'unknown'
            }

        except Exception as e:
            logger.error(f"Failed to get gas statistics: {e}")
            return {'error': str(e)}

    # ==================== 连接监控 ====================

    def check_connection(self) -> ConnectionMetrics:
        """
        检查区块链连接

        Returns:
            连接指标
        """
        start_time = time.time()

        try:
            is_connected = self.w3.is_connected()
            block_number = self.w3.eth.block_number if is_connected else None
            latency_ms = (time.time() - start_time) * 1000

            metrics = ConnectionMetrics(
                timestamp=datetime.now(),
                is_connected=is_connected,
                block_number=block_number,
                latency_ms=latency_ms
            )

            with self.lock:
                self.connection_metrics.append(metrics)
                self.stats['last_check_time'] = datetime.now()

                if not is_connected:
                    self.stats['connection_failures'] += 1

            logger.debug(
                f"Connection check: {'✅' if is_connected else '❌'}, "
                f"latency: {latency_ms:.2f}ms"
            )

            return metrics

        except Exception as e:
            logger.error(f"Connection check failed: {e}")

            metrics = ConnectionMetrics(
                timestamp=datetime.now(),
                is_connected=False,
                error_message=str(e)
            )

            with self.lock:
                self.connection_metrics.append(metrics)
                self.stats['connection_failures'] += 1

            return metrics

    def get_connection_status(self) -> Dict[str, Any]:
        """
        获取连接状态

        Returns:
            连接状态信息
        """
        try:
            with self.lock:
                if not self.connection_metrics:
                    return {'status': 'unknown', 'message': 'No connection data'}

                latest = self.connection_metrics[-1]
                recent_checks = list(self.connection_metrics)[-10:]  # 最近10次检查

            success_rate = sum(1 for m in recent_checks if m.is_connected) / len(recent_checks) * 100

            return {
                'is_connected': latest.is_connected,
                'block_number': latest.block_number,
                'latency_ms': latest.latency_ms,
                'last_check': latest.timestamp.isoformat(),
                'success_rate_percent': success_rate,
                'total_failures': self.stats['connection_failures']
            }

        except Exception as e:
            logger.error(f"Failed to get connection status: {e}")
            return {'status': 'error', 'error': str(e)}

    # ==================== 综合统计 ====================

    def get_overall_statistics(self) -> Dict[str, Any]:
        """
        获取综合统计信息

        Returns:
            统计信息字典
        """
        try:
            with self.lock:
                stats = self.stats.copy()

            # 计算成功率
            if stats['total_transactions'] > 0:
                success_rate = (stats['successful_transactions'] / stats['total_transactions']) * 100
            else:
                success_rate = 0

            # 转换Gas费用为ETH
            total_gas_cost_eth = self.w3.from_wei(stats['total_gas_cost'], 'ether')
            avg_gas_price_gwei = self.w3.from_wei(stats['average_gas_price'], 'gwei')

            return {
                'transactions': {
                    'total': stats['total_transactions'],
                    'successful': stats['successful_transactions'],
                    'failed': stats['failed_transactions'],
                    'pending': stats['pending_transactions'],
                    'success_rate_percent': success_rate
                },
                'gas': {
                    'total_cost_eth': float(total_gas_cost_eth),
                    'average_price_gwei': float(avg_gas_price_gwei)
                },
                'connection': {
                    'failures': stats['connection_failures'],
                    'last_check': stats['last_check_time'].isoformat() if stats['last_check_time'] else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to get overall statistics: {e}")
            return {'error': str(e)}

    def get_transaction_history(
        self,
        limit: int = 100,
        status_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取交易历史

        Args:
            limit: 返回的最大记录数
            status_filter: 状态过滤 (pending, success, failed)

        Returns:
            交易历史列表
        """
        try:
            with self.lock:
                metrics_list = list(self.transaction_metrics)

            # 过滤
            if status_filter:
                metrics_list = [m for m in metrics_list if m.status == status_filter]

            # 限制数量
            metrics_list = metrics_list[-limit:]

            # 转换为字典
            history = []
            for m in metrics_list:
                history.append({
                    'tx_hash': m.tx_hash,
                    'timestamp': m.timestamp.isoformat(),
                    'status': m.status,
                    'operation_type': m.operation_type,
                    'gas_used': m.gas_used,
                    'gas_price_gwei': self.w3.from_wei(m.gas_price, 'gwei') if m.gas_price else None,
                    'total_cost_eth': float(self.w3.from_wei(m.total_cost, 'ether')) if m.total_cost else None,
                    'confirmations': m.confirmations,
                    'error_message': m.error_message
                })

            return history

        except Exception as e:
            logger.error(f"Failed to get transaction history: {e}")
            return []

    def generate_report(self) -> str:
        """
        生成监控报告

        Returns:
            报告文本
        """
        try:
            stats = self.get_overall_statistics()
            gas_stats = self.get_gas_statistics(hours=24)
            connection_status = self.get_connection_status()

            report = f"""
=== 区块链监控报告 ===
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【交易统计】
- 总交易数: {stats['transactions']['total']}
- 成功: {stats['transactions']['successful']}
- 失败: {stats['transactions']['failed']}
- 待处理: {stats['transactions']['pending']}
- 成功率: {stats['transactions']['success_rate_percent']:.2f}%

【Gas费用】
- 总花费: {stats['gas']['total_cost_eth']:.6f} ETH
- 平均Gas价格: {stats['gas']['average_price_gwei']:.2f} Gwei
- 当前Gas价格: {gas_stats.get('current_gas_price_gwei', 0):.2f} Gwei
- 网络拥堵: {gas_stats.get('current_congestion', 'unknown')}

【连接状态】
- 当前状态: {'✅ 已连接' if connection_status.get('is_connected') else '❌ 断开'}
- 区块高度: {connection_status.get('block_number', 'N/A')}
- 延迟: {connection_status.get('latency_ms', 0):.2f}ms
- 成功率: {connection_status.get('success_rate_percent', 0):.2f}%
- 失败次数: {stats['connection']['failures']}

========================
"""
            return report

        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return f"报告生成失败: {e}"


# 全局监控器实例
_monitor: Optional[BlockchainMonitor] = None


def get_monitor() -> BlockchainMonitor:
    """获取监控器实例（单例）"""
    global _monitor

    if _monitor is None:
        _monitor = BlockchainMonitor()

    return _monitor
