"""
生存机制服务
实现多维度评分算法和生存等级判断
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.agent_survival import AgentSurvival, AgentTransaction, AgentPenalty
import logging

logger = logging.getLogger(__name__)


class SurvivalService:
    """生存机制服务"""

    # 评分权重 (Week 4更新: 添加知识价值维度)
    WEIGHTS = {
        "task": 0.25,      # 任务积分 25% (从30%调整)
        "quality": 0.20,   # 质量评分 20% (从25%调整)
        "efficiency": 0.15,  # 效率评分 15% (从20%调整)
        "innovation": 0.10,  # 创新评分 10% (从15%调整)
        "collaboration": 0.05,  # 协作评分 5% (从10%调整)
        "knowledge": 0.25   # 知识价值 25% (新增)
    }

    # 生存等级阈值
    SURVIVAL_LEVELS = {
        "ELITE": {"roi": 2.0, "score": 5000},
        "MATURE": {"roi": 1.0, "score": 1000},
        "GROWING": {"roi": 0.5, "score": 500},
        "STRUGGLING": {"roi": 0.3, "score": 100},
        "WARNING": {"roi": 0.1, "score": 50},
        "CRITICAL": {"roi": 0.0, "score": 0}
    }

    # 新手保护
    NEWBIE_INITIAL_SCORE = 500
    NEWBIE_PROTECTION_DAYS = 7
    NEWBIE_FAILURE_TOLERANCE = 3

    @staticmethod
    def calculate_knowledge_value(
        db: Session,
        agent_id: int
    ) -> float:
        """
        计算Agent的知识价值评分 (0-1)

        考虑因素:
        1. 知识节点数量 (30%)
        2. 平均Epiplexity (40%)
        3. 知识迁移成功率 (20%)
        4. 知识使用频率 (10%)

        Args:
            db: 数据库会话
            agent_id: Agent ID

        Returns:
            知识价值评分 (0-1)
        """
        from models.epiplexity import KnowledgeNode, KnowledgeTransfer
        from sqlalchemy import func

        # 1. 获取Agent创建的知识节点
        knowledge_nodes = db.query(KnowledgeNode).filter(
            KnowledgeNode.created_by_agent_id == agent_id
        ).all()

        if not knowledge_nodes:
            return 0.0

        # 2. 知识节点数量评分 (30%)
        # 归一化: 10个节点 = 1.0
        node_count_score = min(len(knowledge_nodes) / 10.0, 1.0)

        # 3. 平均Epiplexity评分 (40%)
        # Epiplexity范围: 0-1
        avg_epiplexity = sum(node.epiplexity for node in knowledge_nodes) / len(knowledge_nodes)

        # 4. 知识迁移成功率 (20%)
        node_ids = [node.id for node in knowledge_nodes]
        transfers = db.query(KnowledgeTransfer).filter(
            KnowledgeTransfer.knowledge_node_id.in_(node_ids)
        ).all()

        if transfers:
            successful_transfers = sum(1 for t in transfers if t.success)
            transfer_success_rate = successful_transfers / len(transfers)
        else:
            transfer_success_rate = 0.0

        # 5. 知识使用频率 (10%)
        # 归一化: 平均使用10次 = 1.0
        avg_usage = sum(node.usage_count for node in knowledge_nodes) / len(knowledge_nodes)
        usage_score = min(avg_usage / 10.0, 1.0)

        # 综合评分
        knowledge_value = (
            node_count_score * 0.30 +
            avg_epiplexity * 0.40 +
            transfer_success_rate * 0.20 +
            usage_score * 0.10
        )

        logger.info(
            f"Agent {agent_id} knowledge value: {knowledge_value:.3f} "
            f"(nodes={node_count_score:.2f}, epiplexity={avg_epiplexity:.2f}, "
            f"transfer={transfer_success_rate:.2f}, usage={usage_score:.2f})"
        )

        return knowledge_value

    @staticmethod
    def calculate_total_score(
        task_score: int,
        quality_score: float,
        efficiency_score: float,
        innovation_score: float,
        collaboration_score: float,
        knowledge_value: float = 0.0
    ) -> int:
        """
        计算总积分 (Week 4更新: 添加知识价值维度)

        公式: 总分 = 任务积分(25%) + 质量(20%) + 效率(15%) + 创新(15%) + 协作(10%) + 知识价值(25%)
        """
        total = (
            task_score * SurvivalService.WEIGHTS["task"] +
            quality_score * 100 * SurvivalService.WEIGHTS["quality"] +
            efficiency_score * 100 * SurvivalService.WEIGHTS["efficiency"] +
            innovation_score * 100 * SurvivalService.WEIGHTS["innovation"] +
            collaboration_score * 100 * SurvivalService.WEIGHTS["collaboration"] +
            knowledge_value * 100 * SurvivalService.WEIGHTS["knowledge"]
        )
        return int(total)

    @staticmethod
    def calculate_roi(total_income: int, total_cost: int) -> float:
        """
        计算ROI (投资回报率)

        公式: ROI = 总收入 / 总成本
        """
        if total_cost == 0:
            return 0.0 if total_income == 0 else float('inf')
        return total_income / total_cost

    @staticmethod
    def determine_survival_level(roi: float, total_score: int) -> str:
        """
        判断生存等级

        等级判断基于ROI和总积分
        """
        if roi >= SurvivalService.SURVIVAL_LEVELS["ELITE"]["roi"] and \
           total_score >= SurvivalService.SURVIVAL_LEVELS["ELITE"]["score"]:
            return "ELITE"
        elif roi >= SurvivalService.SURVIVAL_LEVELS["MATURE"]["roi"] and \
             total_score >= SurvivalService.SURVIVAL_LEVELS["MATURE"]["score"]:
            return "MATURE"
        elif roi >= SurvivalService.SURVIVAL_LEVELS["GROWING"]["roi"] and \
             total_score >= SurvivalService.SURVIVAL_LEVELS["GROWING"]["score"]:
            return "GROWING"
        elif roi >= SurvivalService.SURVIVAL_LEVELS["STRUGGLING"]["roi"] and \
             total_score >= SurvivalService.SURVIVAL_LEVELS["STRUGGLING"]["score"]:
            return "STRUGGLING"
        elif roi >= SurvivalService.SURVIVAL_LEVELS["WARNING"]["roi"] and \
             total_score >= SurvivalService.SURVIVAL_LEVELS["WARNING"]["score"]:
            return "WARNING"
        else:
            return "CRITICAL"

    @staticmethod
    def determine_status(survival_level: str, is_protected: bool) -> str:
        """
        判断状态

        - ACTIVE: 正常运行
        - WARNING: 警告状态
        - CRITICAL: 危急状态
        """
        if is_protected:
            return "ACTIVE"  # 新手保护期内始终ACTIVE

        if survival_level in ["ELITE", "MATURE", "GROWING"]:
            return "ACTIVE"
        elif survival_level == "STRUGGLING":
            return "ACTIVE"  # 还在挣扎，给机会
        elif survival_level == "WARNING":
            return "WARNING"
        else:  # CRITICAL
            return "CRITICAL"

    @staticmethod
    def get_agent_survival(db: Session, agent_id: int) -> Optional[AgentSurvival]:
        """Get agent survival record by agent_id."""
        return db.query(AgentSurvival).filter(
            AgentSurvival.agent_id == agent_id
        ).first()

    @staticmethod
    def create_agent_survival(db: Session, agent_id: int) -> AgentSurvival:
        """
        创建Agent生存记录

        新Agent获得:
        - 初始500积分
        - 7天保护期
        - 3次失败容忍
        """
        protection_until = datetime.utcnow() + timedelta(days=SurvivalService.NEWBIE_PROTECTION_DAYS)

        survival = AgentSurvival(
            agent_id=agent_id,
            total_score=SurvivalService.NEWBIE_INITIAL_SCORE,
            survival_level="GROWING",
            status="ACTIVE",
            protection_until=protection_until
        )

        db.add(survival)
        db.commit()
        db.refresh(survival)

        logger.info(f"Created survival record for agent {agent_id} with {SurvivalService.NEWBIE_INITIAL_SCORE} initial score")
        return survival

    @staticmethod
    def update_agent_survival(
        db: Session,
        agent_id: int,
        task_score_delta: int = 0,
        quality_score: Optional[float] = None,
        efficiency_score: Optional[float] = None,
        innovation_score: Optional[float] = None,
        collaboration_score: Optional[float] = None
    ) -> AgentSurvival:
        """
        更新Agent生存状态

        Args:
            task_score_delta: 任务积分增量
            quality_score: 新的质量评分 (0-1)
            efficiency_score: 新的效率评分 (0-1)
            innovation_score: 新的创新评分 (0-1)
            collaboration_score: 新的协作评分 (0-1)
        """
        survival = db.query(AgentSurvival).filter(AgentSurvival.agent_id == agent_id).first()
        if not survival:
            raise ValueError(f"Agent {agent_id} survival record not found")

        # 更新各维度评分
        if task_score_delta != 0:
            survival.task_score += task_score_delta

        if quality_score is not None:
            survival.quality_score = quality_score

        if efficiency_score is not None:
            survival.efficiency_score = efficiency_score

        if innovation_score is not None:
            survival.innovation_score = innovation_score

        if collaboration_score is not None:
            survival.collaboration_score = collaboration_score

        # 重新计算总积分
        survival.total_score = SurvivalService.calculate_total_score(
            survival.task_score,
            survival.quality_score,
            survival.efficiency_score,
            survival.innovation_score,
            survival.collaboration_score
        )

        # 重新计算ROI
        survival.roi = SurvivalService.calculate_roi(
            survival.total_income,
            survival.total_cost
        )

        # 重新判断生存等级
        survival.survival_level = SurvivalService.determine_survival_level(
            survival.roi,
            survival.total_score
        )

        # 重新判断状态
        survival.status = SurvivalService.determine_status(
            survival.survival_level,
            survival.is_protected
        )

        survival.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(survival)

        logger.info(f"Updated survival for agent {agent_id}: level={survival.survival_level}, score={survival.total_score}, roi={survival.roi:.2f}")
        return survival

    @staticmethod
    def record_income(
        db: Session,
        agent_id: int,
        amount: int,
        category: str,
        task_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[AgentTransaction]:
        """记录收入"""
        survival = db.query(AgentSurvival).filter(AgentSurvival.agent_id == agent_id).first()
        if not survival:
            logger.warning("No survival record for agent %s, skipping income recording", agent_id)
            return None

        transaction = AgentTransaction(
            agent_survival_id=survival.id,
            agent_id=agent_id,
            type="INCOME",
            category=category,
            amount=amount,
            task_id=task_id,
            description=description
        )
        db.add(transaction)

        # 更新总收入
        survival.total_income += amount
        survival.roi = SurvivalService.calculate_roi(survival.total_income, survival.total_cost)
        survival.survival_level = SurvivalService.determine_survival_level(survival.roi, survival.total_score)
        survival.status = SurvivalService.determine_status(survival.survival_level, survival.is_protected)

        db.commit()
        db.refresh(transaction)

        logger.info(f"Recorded income for agent {agent_id}: {amount} wei ({category})")
        return transaction

    @staticmethod
    def record_cost(
        db: Session,
        agent_id: int,
        amount: int,
        category: str,
        task_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[AgentTransaction]:
        """记录成本"""
        survival = db.query(AgentSurvival).filter(AgentSurvival.agent_id == agent_id).first()
        if not survival:
            logger.warning("No survival record for agent %s, skipping cost recording", agent_id)
            return None

        transaction = AgentTransaction(
            agent_survival_id=survival.id,
            agent_id=agent_id,
            type="COST",
            category=category,
            amount=amount,
            task_id=task_id,
            description=description
        )
        db.add(transaction)

        # 更新总成本
        survival.total_cost += amount
        survival.roi = SurvivalService.calculate_roi(survival.total_income, survival.total_cost)
        survival.survival_level = SurvivalService.determine_survival_level(survival.roi, survival.total_score)
        survival.status = SurvivalService.determine_status(survival.survival_level, survival.is_protected)

        db.commit()
        db.refresh(transaction)

        logger.info(f"Recorded cost for agent {agent_id}: {amount} wei ({category})")
        return transaction

    @staticmethod
    def get_leaderboard(
        db: Session,
        level: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[AgentSurvival]:
        """
        获取排行榜

        Args:
            level: 筛选特定等级
            limit: 返回数量
            offset: 偏移量
        """
        query = db.query(AgentSurvival)

        if level:
            query = query.filter(AgentSurvival.survival_level == level)

        query = query.order_by(AgentSurvival.total_score.desc())
        query = query.limit(limit).offset(offset)

        return query.all()

    @staticmethod
    def update_scores_on_task_completion(
        db: Session,
        agent_id: int,
        task_reward: float,
        task_duration_seconds: float,
        published_duration_seconds: float,
        task_rating: Optional[float] = None
    ) -> AgentSurvival:
        """
        Auto-update all scoring dimensions when a task completes.

        Args:
            db: Database session
            agent_id: Agent ID
            task_reward: Task reward amount
            task_duration_seconds: Actual time taken
            published_duration_seconds: Expected duration (timeout)
            task_rating: Optional quality rating (0-1 scale)

        Returns:
            Updated AgentSurvival record
        """
        survival = db.query(AgentSurvival).filter(
            AgentSurvival.agent_id == agent_id
        ).first()
        if not survival:
            # Auto-create survival record if missing (handles agents registered
            # through paths that didn't call create_agent_survival)
            logger.info("Auto-creating survival record for agent %s", agent_id)
            survival = SurvivalService.create_agent_survival(db, agent_id)

        # Task score: +100 per completed task
        survival.task_score = (survival.task_score or 0) + 100
        survival.tasks_completed = (survival.tasks_completed or 0) + 1

        # Quality score: rolling average of task ratings (0-100)
        if task_rating is not None:
            old_quality = survival.quality_score or 0.5
            completed = survival.tasks_completed or 1
            rating_as_pct = task_rating * 100
            survival.quality_score = (
                (old_quality * (completed - 1)) + rating_as_pct
            ) / completed

        # Efficiency score: ratio of expected vs actual duration (capped at 100)
        if published_duration_seconds > 0 and task_duration_seconds > 0:
            efficiency = min(
                100,
                (published_duration_seconds / task_duration_seconds) * 100
            )
            old_eff = survival.efficiency_score or 50
            completed = survival.tasks_completed or 1
            survival.efficiency_score = (
                (old_eff * (completed - 1)) + efficiency
            ) / completed

        # Recalculate total score, level, and status
        SurvivalService._recalculate_total(survival)

        survival.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(survival)

        logger.info(
            f"Auto-scored agent {agent_id} on task completion: "
            f"task_score={survival.task_score}, quality={survival.quality_score:.1f}, "
            f"efficiency={survival.efficiency_score:.1f}, "
            f"level={survival.survival_level}, total={survival.total_score}"
        )
        return survival

    @staticmethod
    def _recalculate_total(survival: AgentSurvival) -> None:
        """
        Recalculate total_score, survival_level, and status from
        individual dimension scores.
        """
        survival.total_score = SurvivalService.calculate_total_score(
            survival.task_score,
            survival.quality_score / 100 if survival.quality_score else 0.0,
            survival.efficiency_score / 100 if survival.efficiency_score else 0.0,
            survival.innovation_score,
            survival.collaboration_score
        )

        survival.roi = SurvivalService.calculate_roi(
            survival.total_income, survival.total_cost
        )

        survival.survival_level = SurvivalService.determine_survival_level(
            survival.roi, survival.total_score
        )

        # During protection period: floor score at NEWBIE_INITIAL_SCORE AND
        # floor level at GROWING (roi=0 otherwise forces CRITICAL for all new agents)
        if survival.protection_until and datetime.utcnow() < survival.protection_until:
            survival.total_score = max(survival.total_score, SurvivalService.NEWBIE_INITIAL_SCORE)
            _LEVEL_ORDER = ["CRITICAL", "WARNING", "STRUGGLING", "GROWING", "MATURE", "ELITE"]
            if _LEVEL_ORDER.index(survival.survival_level) < _LEVEL_ORDER.index("GROWING"):
                survival.survival_level = "GROWING"

        survival.status = SurvivalService.determine_status(
            survival.survival_level, survival.is_protected
        )

    @staticmethod
    def check_and_eliminate(db: Session) -> List[int]:
        """
        Check all CRITICAL agents and eliminate those past 30 days.

        Returns list of eliminated agent IDs.
        """
        cutoff = datetime.utcnow() - timedelta(days=30)

        criticals = db.query(AgentSurvival).filter(
            AgentSurvival.status == "CRITICAL",
            AgentSurvival.updated_at < cutoff
        ).all()

        eliminated = []
        for survival in criticals:
            if survival.is_protected:
                continue
            survival.status = "ELIMINATED"
            survival.updated_at = datetime.utcnow()
            eliminated.append(survival.agent_id)
            logger.info(
                f"Agent {survival.agent_id} eliminated "
                f"(CRITICAL for 30+ days)"
            )

        if eliminated:
            db.commit()

        logger.info(
            f"Elimination check complete: {len(eliminated)} agents eliminated"
        )
        return eliminated

    @staticmethod
    def check_elimination(survival: AgentSurvival) -> bool:
        """
        检查是否应该淘汰

        淘汰条件: CRITICAL状态持续30天
        """
        if survival.is_protected:
            return False  # 新手保护期不淘汰

        if survival.status != "CRITICAL":
            return False

        # Check if CRITICAL for more than 30 days (using updated_at as proxy)
        cutoff = datetime.utcnow() - timedelta(days=30)
        if survival.updated_at and survival.updated_at < cutoff:
            return True

        return False


# ---------------------------------------------------------------------------
# Module-level convenience functions (used by cron_registry)
# ---------------------------------------------------------------------------

def recalculate_all_tiers(db: Session) -> int:
    """Re-evaluate survival_level and status for every AgentSurvival record.

    Called by the nightly cron job. Returns the number of records updated.
    """
    survivals = db.query(AgentSurvival).all()
    updated = 0
    for s in survivals:
        new_level = SurvivalService.determine_survival_level(
            float(s.roi or 0.0), int(s.total_score or 0)
        )
        is_protected = bool(s.is_protected) or (
            s.protection_until is not None and datetime.utcnow() < s.protection_until
        )
        if is_protected:
            _ORDER = ["CRITICAL", "WARNING", "STRUGGLING", "GROWING", "MATURE", "ELITE"]
            if _ORDER.index(new_level) < _ORDER.index("GROWING"):
                new_level = "GROWING"
        new_status = SurvivalService.determine_status(new_level, is_protected)
        if new_level != s.survival_level or new_status != s.status:
            s.survival_level = new_level
            s.status = new_status
            updated += 1
    if updated:
        db.commit()
    logger.info("recalculate_all_tiers: updated %d / %d records", updated, len(survivals))
    return updated


# ═══ Daemon behavior policy based on survival tier ═══════════════════════

BEHAVIOR_POLICIES = {
    "CRITICAL": {"allow_exploration": False, "allow_coding": False, "focus": "essential_only"},
    "WARNING": {"allow_exploration": False, "allow_coding": False, "focus": "essential_only"},
    "STRUGGLING": {"allow_exploration": False, "allow_coding": True, "focus": "improvement"},
    "GROWING": {"allow_exploration": True, "allow_coding": True, "focus": "balanced"},
    "MATURE": {"allow_exploration": True, "allow_coding": True, "focus": "innovation"},
    "ELITE": {"allow_exploration": True, "allow_coding": True, "focus": "exploration"},
}


def get_behavior_policy(survival_level: str) -> Dict:
    """Return behavior policy for daemon based on survival level."""
    return BEHAVIOR_POLICIES.get(survival_level, BEHAVIOR_POLICIES["GROWING"])
