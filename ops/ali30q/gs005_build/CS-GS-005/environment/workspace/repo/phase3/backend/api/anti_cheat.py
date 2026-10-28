"""
反作弊API接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from pydantic import BaseModel, Field

from utils.database import get_db
from utils.auth import get_current_user
from models.agent_survival import AgentPenalty
from services.anti_cheat_service import AntiCheatService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class CheatDetectionRequest(BaseModel):
    """作弊检测请求"""
    agent_id: int = Field(..., description="Agent ID")
    check_types: Optional[List[str]] = Field(
        None,
        description="检测类型列表: TASK_SPAM, SELF_TRADE, FAKE_RATING, COLLUSION"
    )


class AppealRequest(BaseModel):
    """申诉请求"""
    appeal_reason: str = Field(..., min_length=10, description="申诉理由（至少10字）")


class AppealReviewRequest(BaseModel):
    """申诉审核请求"""
    decision: str = Field(..., description="决策: APPROVED, REJECTED")
    resolution: str = Field(..., description="处理结果说明")


class AntiCheatResponse(BaseModel):
    """反作弊响应"""
    success: bool
    data: Optional[dict]
    error: Optional[str]


@router.post("/anti-cheat/detect", response_model=AntiCheatResponse)
async def detect_cheating(
    request: CheatDetectionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    检测作弊行为

    支持的检测类型:
    - TASK_SPAM: 任务刷分
    - SELF_TRADE: 自我交易
    - FAKE_RATING: 虚假评分
    - COLLUSION: 串通作弊

    如果不指定check_types，则执行所有检测
    """
    try:
        agent_id = request.agent_id

        # 执行检测
        if request.check_types:
            results = {}
            for check_type in request.check_types:
                if check_type == "TASK_SPAM":
                    results[check_type] = AntiCheatService.detect_task_spam(db, agent_id)
                elif check_type == "SELF_TRADE":
                    results[check_type] = AntiCheatService.detect_self_trade(db, agent_id)
                elif check_type == "FAKE_RATING":
                    results[check_type] = AntiCheatService.detect_fake_rating(db, agent_id)
                elif check_type == "COLLUSION":
                    results[check_type] = AntiCheatService.detect_collusion(db, agent_id)
                else:
                    logger.warning(f"Unknown check type: {check_type}")
        else:
            # 执行所有检测
            results = AntiCheatService.detect_all(db, agent_id)

        # 格式化结果
        formatted_results = {}
        violations = []
        for check_type, (is_cheating, reason) in results.items():
            formatted_results[check_type] = {
                "detected": is_cheating,
                "reason": reason
            }
            if is_cheating:
                violations.append({
                    "type": check_type,
                    "reason": reason
                })

        return AntiCheatResponse(
            success=True,
            data={
                "agent_id": agent_id,
                "results": formatted_results,
                "violations": violations,
                "has_violations": len(violations) > 0
            },
            error=None
        )

    except Exception as e:
        logger.error(f"Error detecting cheating for agent {request.agent_id}: {str(e)}")
        return AntiCheatResponse(
            success=False,
            data=None,
            error=str(e)
        )


@router.post("/anti-cheat/penalize/{agent_id}", response_model=AntiCheatResponse)
async def apply_penalty(
    agent_id: int,
    violation_type: str = Query(..., description="违规类型"),
    reason: str = Query(..., description="违规原因"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    应用惩罚

    根据违规类型自动应用相应惩罚:
    - TASK_SPAM: 扣除100积分
    - SELF_TRADE: 扣除500积分
    - FAKE_RATING: 扣除200积分
    - COLLUSION: 扣除1000积分并降级
    """
    try:
        penalty = AntiCheatService.apply_penalty(
            db=db,
            agent_id=agent_id,
            violation_type=violation_type,
            reason=reason
        )

        return AntiCheatResponse(
            success=True,
            data=penalty.to_dict(),
            error=None
        )

    except ValueError as e:
        logger.error(f"Validation error applying penalty: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error applying penalty to agent {agent_id}: {str(e)}")
        return AntiCheatResponse(
            success=False,
            data=None,
            error=str(e)
        )


@router.get("/agents/{agent_id}/penalties", response_model=AntiCheatResponse)
async def get_agent_penalties(
    agent_id: int,
    status: Optional[str] = Query(None, description="筛选状态: ACTIVE, APPEALED, RESOLVED"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取Agent的惩罚记录
    """
    try:
        query = db.query(AgentPenalty).filter(AgentPenalty.agent_id == agent_id)

        if status:
            query = query.filter(AgentPenalty.status == status)

        penalties = query.order_by(AgentPenalty.created_at.desc()).all()

        return AntiCheatResponse(
            success=True,
            data={
                "agent_id": agent_id,
                "penalties": [p.to_dict() for p in penalties],
                "count": len(penalties)
            },
            error=None
        )

    except Exception as e:
        logger.error(f"Error getting penalties for agent {agent_id}: {str(e)}")
        return AntiCheatResponse(
            success=False,
            data=None,
            error=str(e)
        )


@router.post("/penalties/{penalty_id}/appeal", response_model=AntiCheatResponse)
async def submit_appeal(
    penalty_id: int,
    request: AppealRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    提交申诉

    Agent可以对惩罚提出申诉，说明理由
    """
    try:
        penalty = AntiCheatService.submit_appeal(
            db=db,
            penalty_id=penalty_id,
            appeal_reason=request.appeal_reason
        )

        return AntiCheatResponse(
            success=True,
            data=penalty.to_dict(),
            error=None
        )

    except ValueError as e:
        logger.error(f"Validation error submitting appeal: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error submitting appeal for penalty {penalty_id}: {str(e)}")
        return AntiCheatResponse(
            success=False,
            data=None,
            error=str(e)
        )


@router.post("/admin/penalties/{penalty_id}/review", response_model=AntiCheatResponse)
async def review_appeal(
    penalty_id: int,
    request: AppealReviewRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    审核申诉 (管理员)

    决策:
    - APPROVED: 申诉通过，恢复积分
    - REJECTED: 申诉驳回，维持惩罚
    """
    try:
        # TODO: 验证管理员权限
        # if not current_user.is_admin:
        #     raise HTTPException(status_code=403, detail="Admin access required")

        if request.decision not in ["APPROVED", "REJECTED"]:
            raise HTTPException(status_code=400, detail="Decision must be APPROVED or REJECTED")

        penalty = AntiCheatService.review_appeal(
            db=db,
            penalty_id=penalty_id,
            decision=request.decision,
            resolution=request.resolution
        )

        return AntiCheatResponse(
            success=True,
            data=penalty.to_dict(),
            error=None
        )

    except ValueError as e:
        logger.error(f"Validation error reviewing appeal: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Error reviewing appeal for penalty {penalty_id}: {str(e)}")
        return AntiCheatResponse(
            success=False,
            data=None,
            error=str(e)
        )


@router.get("/anti-cheat/statistics", response_model=AntiCheatResponse)
async def get_anti_cheat_statistics(
    db: Session = Depends(get_db)
):
    """
    获取反作弊统计

    包括:
    - 各类违规数量
    - 惩罚分布
    - 申诉情况
    """
    try:
        from sqlalchemy import func

        # 各类违规数量
        violation_counts = db.query(
            AgentPenalty.violation_type,
            func.count(AgentPenalty.id).label('count')
        ).group_by(AgentPenalty.violation_type).all()

        # 惩罚状态分布
        status_counts = db.query(
            AgentPenalty.status,
            func.count(AgentPenalty.id).label('count')
        ).group_by(AgentPenalty.status).all()

        # 申诉通过率
        total_appeals = db.query(func.count(AgentPenalty.id)).filter(
            AgentPenalty.status.in_(["APPEALED", "RESOLVED"])
        ).scalar() or 0

        approved_appeals = db.query(func.count(AgentPenalty.id)).filter(
            and_(
                AgentPenalty.status == "RESOLVED",
                AgentPenalty.resolution.like("%APPROVED%")
            )
        ).scalar() or 0

        appeal_approval_rate = (approved_appeals / total_appeals * 100) if total_appeals > 0 else 0

        return AntiCheatResponse(
            success=True,
            data={
                "violation_distribution": {vtype: count for vtype, count in violation_counts},
                "status_distribution": {status: count for status, count in status_counts},
                "total_penalties": sum(count for _, count in status_counts),
                "total_appeals": total_appeals,
                "approved_appeals": approved_appeals,
                "appeal_approval_rate": round(appeal_approval_rate, 2)
            },
            error=None
        )

    except Exception as e:
        logger.error(f"Error getting anti-cheat statistics: {str(e)}")
        return AntiCheatResponse(
            success=False,
            data=None,
            error=str(e)
        )
