"""
数据模型定义
"""
import time
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class Difficulty(Enum):
    """任务难度等级"""
    D, C, B, A = 10, 50, 150, 500


@dataclass
class Task:
    """任务数据模型"""
    task_id: str
    desc: str
    user_id: str
    difficulty: Difficulty = Difficulty.C
    deadline: float = 0
    status: str = "pending"  # pending/claimed/completed/failed
    claimed_by: Optional[str] = None


@dataclass
class Node:
    """节点数据模型"""
    node_id: str
    node_type: str
    hp: int = 100
    points: int = 0
    meme: float = 0.0
    tasks: int = 0
    roi: float = 0.0
    consecutive_success: int = 0
    last_active: float = field(default_factory=time.time)
    warning_time: Optional[float] = None
    total_cost: float = 0.0


@dataclass
class POW:
    """工作量证明数据模型"""
    pow_id: str
    task_id: str
    node_id: str
    proof: str
    output: str
    duration: float
    cost: float
    timestamp: float
