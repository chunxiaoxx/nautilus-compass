"""
Raid API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from nautilus.raid import RaidManager, RaidLevel, RaidStatus, raid_manager

router = APIRouter(prefix="/api/raid", tags=["raid"])


class RaidSubmitRequest(BaseModel):
    """提交Raid任务请求"""
    task: str
    raid_level: int = 2  # 默认RAID_2
    

class RaidReviewRequest(BaseModel):
    """提交审查结果请求"""
    score: float
    feedback: str
    approved: bool
    issues: List[str] = []


@router.post("/submit")
async def submit_raid_task(request: RaidSubmitRequest) -> Dict:
    """提交Raid任务"""
    level = RaidLevel(request.raid_level)
    task_id = await raid_manager.submit_task(request.task, level)
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": f"Raid task submitted with Level {level.value}"
    }


@router.get("/status/{task_id}")
async def get_raid_status(task_id: str) -> Dict:
    """获取Raid任务状态"""
    task = raid_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("/list")
async def list_raid_tasks(
    status: Optional[str] = None,
    limit: int = 10
) -> Dict:
    """获取Raid任务列表"""
    if status:
        try:
            raid_status = RaidStatus(status)
            tasks = raid_manager.get_tasks_by_status(raid_status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    else:
        tasks = [task.to_dict() for task in raid_manager.tasks.values()]
        
    return {
        "total": len(tasks),
        "tasks": tasks[:limit]
    }


@router.get("/stats")
async def get_raid_stats() -> Dict:
    """获取Raid统计信息"""
    tasks = list(raid_manager.tasks.values())
    
    stats = {
        "total": len(tasks),
        "pending": 0,
        "executing": 0,
        "reviewing": 0,
        "approved": 0,
        "rejected": 0,
        "arbitrating": 0
    }
    
    for task in tasks:
        stats[task.status.value] += 1
    
    # 计算通过率
    completed = stats["approved"] + stats["rejected"]
    if completed > 0:
        stats["approval_rate"] = round(stats["approved"] / completed * 100, 2)
    else:
        stats["approval_rate"] = 0
        
    return stats


@router.post("/review/{task_id}")
async def submit_review(task_id: str, request: RaidReviewRequest) -> Dict:
    """手动提交审查结果"""
    task = raid_manager.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    from nautilus.raid import ReviewResult
    task.reviewer_result = ReviewResult(
        score=request.score,
        feedback=request.feedback,
        approved=request.approved,
        issues=request.issues
    )
    
    # 重新判定
    raid_manager._judge_task(task)
    
    return {
        "task_id": task_id,
        "status": task.status.value,
        "score": request.score
    }


@router.post("/retry/{task_id}")
async def retry_raid_task(task_id: str) -> Dict:
    """重试Raid任务"""
    task = raid_manager.tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # 重新提交执行
    asyncio.create_task(raid_manager._execute_raid(task_id))
    
    return {
        "task_id": task_id,
        "status": "retrying"
    }
