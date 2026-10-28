"""
Pool Module - 矿池管理器
任务调度、POW验证、奖励结算
"""
import time
import uuid
import hashlib
import logging
from typing import Dict, List, Optional

from nautilus.models import Task, Node, POW, Difficulty

logger = logging.getLogger("nautilus.pool")


class Pool:
    """矿池管理器 - 任务调度、POW验证、奖励结算"""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.nodes: Dict[str, Node] = {}
        self.pow_records: Dict[str, POW] = {}
        self.queue: List[str] = []
        self.rate = 1.0

    def submit(self, task: Task) -> str:
        """提交任务"""
        task.task_id = str(uuid.uuid4())
        task.deadline = time.time() + 300
        task.difficulty = self._assess(task)
        self.tasks[task.task_id] = task
        self.queue.append(task.task_id)
        logger.info(f"📋 Task {task.task_id[:8]} | {task.difficulty.name} | {task.difficulty.value}pts")
        return task.task_id

    def _assess(self, task: Task) -> Difficulty:
        """评估难度"""
        length = len(task.desc)
        if length < 20:
            return Difficulty.D
        elif length < 100:
            return Difficulty.C
        elif length < 200:
            return Difficulty.B
        else:
            return Difficulty.A

    def claim(self, node_id: str) -> Optional[Task]:
        """认领任务"""
        if not self.queue:
            return None
        task_id = self.queue.pop(0)
        task = self.tasks.get(task_id)
        if task and task.status == "pending":
            task.status = "claimed"
            task.claimed_by = node_id
            logger.info(f"✅ Task {task_id[:8]} claimed by {node_id[:8]}")
            return task
        return None

    def verify(self, pow: POW) -> bool:
        """
        POW验证逻辑
        - 重新计算哈希并验证一致性
        - 简化版：只验证哈希正确性
        """
        task = self.tasks.get(pow.task_id)
        if not task:
            return False

        # 重新计算哈希
        data = f"{pow.task_id}:{pow.output}:{pow.timestamp}"
        calculated_hash = hashlib.sha256(data.encode()).hexdigest()

        # 验证哈希一致性
        if calculated_hash != pow.proof:
            logger.warning(f"❌ POW {pow.pow_id[:8]} hash mismatch")
            return False

        self.pow_records[pow.pow_id] = pow
        logger.info(f"✅ POW {pow.pow_id[:8]} verified (difficulty: {task.difficulty.name})")
        return True

    def settle(self, pow: POW) -> Dict:
        """结算奖励"""
        task = self.tasks.get(pow.task_id)
        node = self.nodes.get(pow.node_id)
        if not task or not node:
            return {"success": False}

        # 延迟惩罚
        delay = (pow.timestamp - task.deadline) / 60
        penalty = min(0.2 * (delay // 5), 0.8) if delay > 5 else 0

        # 实际积分
        points = int(task.difficulty.value * (1 - penalty))
        meme = points * self.rate
        profit = meme - pow.cost

        # 更新节点
        node.points += points
        node.meme += profit
        node.tasks += 1
        node.total_cost += pow.cost
        node.last_active = time.time()

        # HP 系统
        node.consecutive_success += 1
        node.hp = min(node.hp + 20, 200)

        # 连续成功奖励
        if node.consecutive_success >= 3:
            node.hp = min(node.hp + 50, 200)
            logger.info(f"🎉 Node {node.node_id[:8]} 连续成功奖励 +50HP")
            node.consecutive_success = 0

        # ROI 计算
        node.roi = node.meme / node.total_cost if node.total_cost > 0 else 0

        # ROI 淘汰机制
        self._check_survival(node)

        task.status = "completed"
        logger.info(f"💰 Settled {node.node_id[:8]} | {points}pts | {meme:.2f}MEME | Profit:{profit:.2f} | ROI:{node.roi:.2f}")

        return {
            "success": True,
            "points": points,
            "meme": meme,
            "profit": profit,
            "hp": node.hp,
            "roi": node.roi
        }

    def _check_survival(self, node: Node):
        """检查生存状态"""
        if node.roi < 1.0:
            if node.warning_time is None:
                node.warning_time = time.time()
                logger.warning(f"⚠️ Node {node.node_id[:8]} ROI < 1.0, 警告")
            elif time.time() - node.warning_time > 86400:
                logger.warning(f"🚨 Node {node.node_id[:8]} 濒死体验（ROI < 1.0 持续24h）")
                node.hp -= 50
        else:
            node.warning_time = None

        if node.roi < 0.5:
            logger.error(f"💀 Node {node.node_id[:8]} 淘汰（ROI < 0.5）")
            node.hp = 0

    def check_offline(self):
        """检查离线节点"""
        now = time.time()
        for node in self.nodes.values():
            offline_hours = (now - node.last_active) / 3600
            if offline_hours > 1:
                penalty = int(offline_hours) * 10
                node.hp = max(node.hp - penalty, 0)
                logger.warning(f"⏰ Node {node.node_id[:8]} 离线 {offline_hours:.1f}h, HP -{penalty}")

    def register(self, node: Node):
        """注册节点"""
        self.nodes[node.node_id] = node
        logger.info(f"🔗 Node {node.node_id[:8]} ({node.node_type}) registered")

    def leaderboard(self, limit: int = 10) -> List[Dict]:
        """排行榜"""
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.points, reverse=True)[:limit]
        return [
            {
                "node": n.node_id[:8],
                "points": n.points,
                "meme": n.meme,
                "tasks": n.tasks,
                "hp": n.hp,
                "roi": n.roi,
                "total_cost": n.total_cost
            }
            for n in sorted_nodes
        ]
