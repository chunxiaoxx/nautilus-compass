"""
Economy Module - MEME 币经济系统
预留接口，用于未来集成代币经济
"""
from typing import Dict, Optional


class MEMEEconomy:
    """MEME 币经济系统"""

    def __init__(self, initial_rate: float = 1.0):
        self.rate = initial_rate
        self.total_supply = 0.0
        self.circulation = 0.0
        self.balances: Dict[str, float] = {}

    def mint(self, node_id: str, amount: float) -> bool:
        """铸造代币"""
        if amount <= 0:
            return False

        self.total_supply += amount
        self.circulation += amount
        self.balances[node_id] = self.balances.get(node_id, 0.0) + amount
        return True

    def transfer(self, from_node: str, to_node: str, amount: float) -> bool:
        """转账"""
        if amount <= 0:
            return False

        if self.balances.get(from_node, 0.0) < amount:
            return False

        self.balances[from_node] -= amount
        self.balances[to_node] = self.balances.get(to_node, 0.0) + amount
        return True

    def burn(self, node_id: str, amount: float) -> bool:
        """销毁代币"""
        if amount <= 0:
            return False

        if self.balances.get(node_id, 0.0) < amount:
            return False

        self.balances[node_id] -= amount
        self.circulation -= amount
        return True

    def get_balance(self, node_id: str) -> float:
        """查询余额"""
        return self.balances.get(node_id, 0.0)

    def adjust_rate(self, new_rate: float):
        """调整兑换率"""
        if new_rate > 0:
            self.rate = new_rate

    def get_stats(self) -> Dict:
        """获取经济统计"""
        return {
            "total_supply": self.total_supply,
            "circulation": self.circulation,
            "rate": self.rate,
            "holders": len(self.balances)
        }


__all__ = ["MEMEEconomy"]
