"""
Mind Module - 决策引擎
任务分析、模型选择、策略生成
"""
from typing import Dict, Tuple
from nautilus.models import Task


class Mind:
    """决策引擎 - 任务分析、模型选择、策略生成"""

    def __init__(self):
        self.brains = {
            "local": (0.0001, 0.5),
            "deepseek": (0.0014, 1.5),
            "claude": (0.003, 2.0),
            "gpt4": (0.03, 3.0)
        }

    def select(self, task: Task, budget: float) -> Tuple[str, float, float]:
        """智能选择模型"""
        desc = task.desc.lower()

        if len(desc) < 20:
            brain = "local"
        elif any(kw in desc for kw in ["代码", "code", "编程"]):
            brain = "deepseek"
        elif any(kw in desc for kw in ["分析", "为什么", "如何"]):
            brain = "claude" if budget > 0.01 else "deepseek"
        elif any(kw in desc for kw in ["创作", "写", "设计"]):
            brain = "gpt4" if budget > 0.02 else "claude"
        else:
            brain = "claude"

        cost, speed = self.brains[brain]
        return brain, cost, speed

    def strategy(self, task: Task) -> Dict:
        """生成策略"""
        return {
            "cache": False,
            "timeout": 30,
            "retry": 2,
            "shard": len(task.desc) > 500
        }
