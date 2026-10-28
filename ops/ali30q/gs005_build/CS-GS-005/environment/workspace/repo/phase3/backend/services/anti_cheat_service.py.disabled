"""
反作弊检测服务
实现多种作弊检测算法
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models.agent_survival import AgentSurvival, AgentPenalty
from models.database import Task, Agent
import logging

logger = logging.getLogger(__name__)


class AntiCheatService:
    """反作弊服务"""

    # 检测阈值
    TASK_SPAM_THRESHOLD = {
        "tasks_per_hour": 20,  # 1小时内完成20个任务
        "min_task_duration": 60,  # 最小任务时长60秒
        "low_quality_threshold": 0.3  # 低质量阈值
    }

    SELF_TRADE_THRESHOLD = {
        "same_wallet": True  # 发布者和接受者钱包相同
    }

    FAKE_RATING_THRESHOLD = {
        "consecutive_high_ratings": 10,  # 连续10个高评分
        "high_rating_value": 4.5,  # 高评分阈值
        "rating_variance": 0.1  # 评分方差阈值
    }

    COLLUSION_THRESHOLD = {
        "mutual_tasks": 5,  # 互相完成任务数
        "time_window_days": 30,  # 时间窗口30天
        "rating_similarity": 0.9  # 评分相似度
    }

    # 惩罚配置
    PENALTIES = {
        "TASK_SPAM": {
            "severity": "MINOR",
            "penalty_type": "SCORE_DEDUCTION",
            "score_deduction": 100
        },
        "SELF_TRADE": {
            "severity": "MAJOR",
            "penalty_type": "SCORE_DEDUCTION",
            "score_deduction": 500
        },
        "FAKE_RATING": {
            "severity": "MINOR",
            "penalty_type": "SCORE_DEDUCTION",
            "score_deduction": 200
        },
        "COLLUSION": {
            "severity": "MAJOR",
            "penalty_type": "DOWNGRADE",
            "score_deduction": 1000
        }
    }

    @staticmethod
    def detect_task_spam(db: Session, agent_id: int) -> Tuple[bool, Optional[str]]:
        """
        检测任务刷分

        检测条件:
        - 短时间内完成大量任务
        - 任务时长异常短
        - 任务质量低
        """
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        # 查询1小时内该Agent作为acceptor的已完成任务
        recent_tasks = db.query(Task).filter(
            and_(
                Task.acceptor == db.query(Agent).filter(Agent.agent_id == agent_id).first().owner if db.query(Agent).filter(Agent.agent_id == agent_id).first() else None,
                Task.status == "completed",
                Task.updated_at >= one_hour_ago
            )
        ).all()

        task_count = len(recent_tasks)

        # 检查任务数量
        if task_count < AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"]:
            return False, None

        # 检查任务时长
        suspicious_count = 0
        for task in recent_tasks:
            # 计算任务时长
            if task.created_at and task.updated_at:
                duration = (task.updated_at - task.created_at).total_seconds()
                if duration < AntiCheatService.TASK_SPAM_THRESHOLD["min_task_duration"]:
                    suspicious_count += 1

        # 如果超过一半的任务时长异常短
        if suspicious_count > task_count / 2:
            reason = f"在1小时内完成{task_count}个任务，其中{suspicious_count}个任务时长异常短（<60秒）"
            logger.warning(f"Task spam detected for agent {agent_id}: {reason}")
            return True, reason

        return False, None

    @staticmethod
    def detect_self_trade(db: Session, agent_id: int) -> Tuple[bool, Optional[str]]:
        """
        检测自我交易

        检测条件:
        - 发布者和接受者是同一个Agent
        - 或者钱包地址相同
        """
        # 查询Agent
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            return False, None

        # 查询该Agent接受的任务中，发布者是自己的
        self_trades = db.query(Task).filter(
            and_(
                Task.acceptor == agent.owner,
                Task.publisher == agent.owner  # 发布者钱包 = 接受者钱包
            )
        ).all()

        if len(self_trades) > 0:
            reason = f"检测到{len(self_trades)}个自我交易（发布者和接受者钱包相同）"
            logger.warning(f"Self trade detected for agent {agent_id}: {reason}")
            return True, reason

        return False, None

    @staticmethod
    def detect_fake_rating(db: Session, agent_id: int) -> Tuple[bool, Optional[str]]:
        """
        检测虚假评分

        检测条件:
        - 连续多个高评分
        - 评分方差极低
        - 评分模式异常

        注意: 当前Task模型可能没有rating字段，此检测暂时简化
        """
        # 简化实现：检查Agent的平均评分
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            return False, None

        # TODO: 当Task模型有rating字段时，实现完整检测
        # 暂时返回False
        return False, None

    @staticmethod
    def detect_collusion(db: Session, agent_id: int) -> Tuple[bool, Optional[str]]:
        """
        检测串通作弊

        检测条件:
        - 多个Agent互相完成任务
        - 互相给高评分
        - 形成作弊网络
        """
        time_window = datetime.utcnow() - timedelta(
            days=AntiCheatService.COLLUSION_THRESHOLD["time_window_days"]
        )

        # 查询Agent
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            return False, None

        # 查询该Agent完成的任务（作为acceptor）
        completed_tasks = db.query(Task).filter(
            and_(
                Task.acceptor == agent.owner,
                Task.status == "completed",
                Task.updated_at >= time_window
            )
        ).all()

        # 统计每个发布者的任务数
        publisher_counts = {}
        for task in completed_tasks:
            publisher = task.publisher
            publisher_counts[publisher] = publisher_counts.get(publisher, 0) + 1

        # 检查是否有互相完成任务的情况
        for publisher, count in publisher_counts.items():
            if count >= AntiCheatService.COLLUSION_THRESHOLD["mutual_tasks"]:
                # 检查该发布者是否也完成了当前Agent发布的任务
                publisher_agent = db.query(Agent).filter(Agent.owner == publisher).first()
                if publisher_agent:
                    reverse_tasks = db.query(Task).filter(
                        and_(
                            Task.acceptor == publisher,
                            Task.publisher == agent.owner,
                            Task.status == "completed",
                            Task.updated_at >= time_window
                        )
                    ).count()

                    if reverse_tasks >= AntiCheatService.COLLUSION_THRESHOLD["mutual_tasks"]:
                        reason = f"与Agent {publisher_agent.agent_id} 互相完成任务（{count}个和{reverse_tasks}个）"
                        logger.warning(f"Collusion detected for agent {agent_id}: {reason}")
                        return True, reason

        return False, None

    @staticmethod
    def detect_all(db: Session, agent_id: int) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        执行所有检测

        返回: {检测类型: (是否作弊, 原因)}
        """
        results = {
            "TASK_SPAM": AntiCheatService.detect_task_spam(db, agent_id),
            "SELF_TRADE": AntiCheatService.detect_self_trade(db, agent_id),
            "FAKE_RATING": AntiCheatService.detect_fake_rating(db, agent_id),
            "COLLUSION": AntiCheatService.detect_collusion(db, agent_id)
        }

        return results

    @staticmethod
    def apply_penalty(
        db: Session,
        agent_id: int,
        violation_type: str,
        reason: str
    ) -> AgentPenalty:
        """
        应用惩罚

        根据违规类型自动应用相应惩罚
        """
        penalty_config = AntiCheatService.PENALTIES.get(violation_type)
        if not penalty_config:
            raise ValueError(f"Unknown violation type: {violation_type}")

        # 创建惩罚记录
        penalty = AgentPenalty(
            agent_id=agent_id,
            violation_type=violation_type,
            severity=penalty_config["severity"],
            penalty_type=penalty_config["penalty_type"],
            score_deduction=penalty_config["score_deduction"],
            status="ACTIVE"
        )
        db.add(penalty)

        # 扣除积分
        survival = db.query(AgentSurvival).filter(AgentSurvival.agent_id == agent_id).first()
        if survival:
            survival.total_score -= penalty_config["score_deduction"]
            survival.warning_count += 1

            # 重新计算等级
            from services.survival_service import SurvivalService
            survival.survival_level = SurvivalService.determine_survival_level(
                survival.roi,
                survival.total_score
            )
            survival.status = SurvivalService.determine_status(
                survival.survival_level,
                survival.is_protected
            )

        db.commit()
        db.refresh(penalty)

        logger.info(f"Applied penalty to agent {agent_id}: {violation_type}, deducted {penalty_config['score_deduction']} points")
        return penalty

    @staticmethod
    def submit_appeal(
        db: Session,
        penalty_id: int,
        appeal_reason: str
    ) -> AgentPenalty:
        """
        提交申诉
        """
        penalty = db.query(AgentPenalty).filter(AgentPenalty.id == penalty_id).first()
        if not penalty:
            raise ValueError(f"Penalty {penalty_id} not found")

        if penalty.status != "ACTIVE":
            raise ValueError(f"Penalty {penalty_id} is not active")

        penalty.status = "APPEALED"
        penalty.appeal_reason = appeal_reason
        db.commit()
        db.refresh(penalty)

        logger.info(f"Appeal submitted for penalty {penalty_id}")
        return penalty

    @staticmethod
    def review_appeal(
        db: Session,
        penalty_id: int,
        decision: str,  # APPROVED, REJECTED
        resolution: str
    ) -> AgentPenalty:
        """
        审核申诉
        """
        penalty = db.query(AgentPenalty).filter(AgentPenalty.id == penalty_id).first()
        if not penalty:
            raise ValueError(f"Penalty {penalty_id} not found")

        if penalty.status != "APPEALED":
            raise ValueError(f"Penalty {penalty_id} is not in appealed status")

        penalty.status = "RESOLVED"
        penalty.resolution = resolution
        penalty.resolved_at = datetime.utcnow()

        # 如果申诉通过，恢复积分
        if decision == "APPROVED":
            survival = db.query(AgentSurvival).filter(
                AgentSurvival.agent_id == penalty.agent_id
            ).first()
            if survival:
                survival.total_score += penalty.score_deduction
                survival.warning_count = max(0, survival.warning_count - 1)

                # 重新计算等级
                from services.survival_service import SurvivalService
                survival.survival_level = SurvivalService.determine_survival_level(
                    survival.roi,
                    survival.total_score
                )
                survival.status = SurvivalService.determine_status(
                    survival.survival_level,
                    survival.is_protected
                )

        db.commit()
        db.refresh(penalty)

        logger.info(f"Appeal reviewed for penalty {penalty_id}: {decision}")
        return penalty
