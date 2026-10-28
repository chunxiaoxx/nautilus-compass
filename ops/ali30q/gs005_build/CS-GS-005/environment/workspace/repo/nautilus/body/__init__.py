"""
Body Module - 执行工作器
执行任务、生成POW、管理HP
"""
import asyncio
import hashlib
import time
import uuid
import logging
from typing import Dict

from nautilus.models import Task, Node, POW
from nautilus.pool import Pool
from nautilus.mind import Mind

logger = logging.getLogger("nautilus.body")


class Body:
    """执行工作器 - 执行任务、生成POW、管理HP"""

    def __init__(self, pool: Pool, mind: Mind):
        self.node_id = str(uuid.uuid4())
        self.hp = 100
        self.pool = pool
        self.mind = mind
        self.pool.register(Node(node_id=self.node_id, node_type="body", hp=self.hp))

    async def work(self, max_tasks: int = 5):
        """工作循环"""
        done = 0
        while self.hp > 0 and done < max_tasks:
            task = self.pool.claim(self.node_id)
            if not task:
                await asyncio.sleep(1)
                continue

            strategy = self.mind.strategy(task)
            brain, cost_rate, speed = self.mind.select(task, budget=10.0)

            result = await self._execute(task, brain, speed)
            pow = self._gen_pow(task, result, cost_rate)

            if self.pool.verify(pow):
                reward = self.pool.settle(pow)
                self.hp = reward.get("hp", self.hp)
                done += 1
                logger.info(f"🎉 Task {task.task_id[:8]} done | HP:{self.hp} | Profit:{reward.get('profit', 0):.2f} | ROI:{reward.get('roi', 0):.2f}")
            else:
                self.hp -= 30
                node = self.pool.nodes.get(self.node_id)
                if node:
                    node.consecutive_success = 0
                logger.warning(f"❌ Task {task.task_id[:8]} failed | HP:{self.hp}")

        logger.info(f"🏁 Work finished: {done} tasks | HP:{self.hp}")

    async def _execute(self, task: Task, brain: str, speed: float) -> Dict:
        """执行任务"""
        start = time.time()
        await asyncio.sleep(speed)
        output = f"[{brain}] {task.desc[:50]}..."
        duration = time.time() - start
        return {"output": output, "duration": duration}

    def _gen_pow(self, task: Task, result: Dict, cost_rate: float) -> POW:
        """生成 POW"""
        ts = time.time()
        data = f"{task.task_id}:{result['output']}:{ts}"
        proof = hashlib.sha256(data.encode()).hexdigest()
        tokens = len(task.desc) + len(result['output'])
        cost = (tokens / 1000) * cost_rate
        return POW(
            pow_id=str(uuid.uuid4()),
            task_id=task.task_id,
            node_id=self.node_id,
            proof=proof,
            output=result['output'],
            duration=result['duration'],
            cost=cost,
            timestamp=ts
        )
