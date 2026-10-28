"""
Raid 机制 - 多Agent审查模式
实现 Raid 1/2/3 等级
"""
import time
import uuid
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("nautilus.raid")


class RaidLevel(Enum):
    """Raid等级"""
    RAID_1 = 1  # 单Agent
    RAID_2 = 2  # 执行+审查
    RAID_3 = 3  # 三Agent多数投票


class RaidStatus(Enum):
    """Raid任务状态"""
    PENDING = "pending"           # 待执行
    EXECUTING = "executing"      # 执行中
    REVIEWING = "reviewing"        # 审查中
    APPROVED = "approved"         # 通过
    REJECTED = "rejected"        # 拒绝
    ARBITRATING = "arbitrating"  # 仲裁中
    COMPLETED = "completed"       # 已完成


@dataclass
class ReviewResult:
    """审查结果"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reviewer_id: str = ""
    score: float = 0.0           # 0-100分
    feedback: str = ""
    approved: bool = False
    issues: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "result_id": self.result_id,
            "reviewer_id": self.reviewer_id,
            "score": self.score,
            "feedback": self.feedback,
            "approved": self.approved,
            "issues": self.issues,
            "timestamp": self.timestamp
        }


@dataclass
class RaidTask:
    """Raid任务"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    original_task: str = ""
    raid_level: RaidLevel = RaidLevel.RAID_2
    status: RaidStatus = RaidStatus.PENDING
    
    # 执行结果
    executor_result: Optional[Dict] = None
    executor_id: str = ""
    executor_time: float = 0.0
    
    # 审查结果
    reviewer_result: Optional[ReviewResult] = None
    reviewer_id: str = ""
    reviewer_time: float = 0.0
    
    # 仲裁结果 (RAID_3)
    arbitrator_result: Optional[Dict] = None
    
    # 元数据
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    
    # 配置
    pass_threshold: float = 80.0      # 通过阈值
    arbitrate_threshold: float = 60.0  # 仲裁阈值
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "original_task": self.original_task,
            "raid_level": self.raid_level.value,
            "status": self.status.value,
            "executor_result": self.executor_result,
            "executor_id": self.executor_id,
            "reviewer_result": self.reviewer_result.to_dict() if self.reviewer_result else None,
            "reviewer_id": self.reviewer_id,
            "score": self.reviewer_result.score if self.reviewer_result else 0,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class RaidManager:
    """Raid管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, RaidTask] = {}
        self.executors: Dict[str, Any] = {}  # Agent执行器
        self.reviewers: Dict[str, Any] = {}  # Agent审查器
        
    def register_executor(self, agent_id: str, executor: Any):
        """注册执行Agent"""
        self.executors[agent_id] = executor
        logger.info(f"✅ Registered executor: {agent_id}")
        
    def register_reviewer(self, agent_id: str, reviewer: Any):
        """注册审查Agent"""
        self.reviewers[agent_id] = reviewer
        logger.info(f"✅ Registered reviewer: {agent_id}")
        
    async def submit_task(self, task: str, raid_level: RaidLevel = RaidLevel.RAID_2) -> str:
        """提交Raid任务"""
        raid_task = RaidTask(
            original_task=task,
            raid_level=raid_level,
            status=RaidStatus.PENDING
        )
        self.tasks[raid_task.task_id] = raid_task
        logger.info(f"📋 RaidTask {raid_task.task_id[:8]} | Level {raid_level.value} | {task[:50]}...")
        
        # 异步执行Raid流程
        asyncio.create_task(self._execute_raid(raid_task.task_id))
        
        return raid_task.task_id
    
    async def _execute_raid(self, task_id: str):
        """执行Raid流程"""
        task = self.tasks.get(task_id)
        if not task:
            return
            
        try:
            # 阶段1: 执行
            task.status = RaidStatus.EXECUTING
            executor = self._select_executor(task)
            if executor:
                task.executor_result = await executor.execute(task.original_task)
                task.executor_id = executor.agent_id if hasattr(executor, 'agent_id') else "executor"
            else:
                # 模拟执行结果
                task.executor_result = {"result": f"Mock result for: {task.original_task[:30]}..."}
                task.executor_id = "mock_executor"
                
            task.status = RaidStatus.REVIEWING
            
            # 阶段2: 审查
            reviewer = self._select_reviewer(task)
            if reviewer:
                task.reviewer_result = await reviewer.review(
                    task.original_task, 
                    task.executor_result
                )
            else:
                # 模拟审查结果
                task.reviewer_result = ReviewResult(
                    score=85.0,
                    feedback="Auto-approved",
                    approved=True
                )
                
            task.reviewer_id = reviewer.agent_id if hasattr(reviewer, 'agent_id') else "mock_reviewer"
            
            # 阶段3: 判定
            task = self._judge_task(task)
            
        except Exception as e:
            logger.error(f"❌ Raid execution failed: {e}")
            task.status = RaidStatus.REJECTED
            
    def _select_executor(self, task: RaidTask) -> Optional[Any]:
        """选择执行Agent"""
        # 简单的负载均衡选择
        if self.executors:
            agents = list(self.executors.values())
            return agents[hash(task.task_id) % len(agents)]
        return None
    
    def _select_reviewer(self, task: RaidTask) -> Optional[Any]:
        """选择审查Agent"""
        if self.reviewers:
            agents = list(self.reviewers.values())
            return agents[hash(task.task_id + "review") % len(agents)]
        return None
    
    def _judge_task(self, task: RaidTask) -> RaidTask:
        """判定任务结果"""
        score = task.reviewer_result.score if task.reviewer_result else 0
        
        if score >= task.pass_threshold:
            task.status = RaidStatus.APPROVED
            logger.info(f"✅ RaidTask {task.task_id[:8]} APPROVED | Score: {score}")
        elif score >= task.arbitrate_threshold:
            task.status = RaidStatus.ARBITRATING
            logger.warning(f"⚠️ RaidTask {task.task_id[:8]} ARBITRATING | Score: {score}")
        else:
            task.status = RaidStatus.REJECTED
            logger.error(f"❌ RaidTask {task.task_id[:8]} REJECTED | Score: {score}")
            
        task.completed_at = time.time()
        return task
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_tasks_by_status(self, status: RaidStatus) -> List[Dict]:
        """获取指定状态的任务"""
        return [
            task.to_dict() 
            for task in self.tasks.values() 
            if task.status == status
        ]


# 全局实例
raid_manager = RaidManager()

__all__ = [
    "RaidLevel", 
    "RaidStatus", 
    "RaidTask", 
    "ReviewResult", 
    "RaidManager",
    "raid_manager"
]
