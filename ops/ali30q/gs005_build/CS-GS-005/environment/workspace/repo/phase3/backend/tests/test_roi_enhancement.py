"""
测试ROI增强计算（包含知识价值收益）
"""
import pytest
from services.financial_service import FinancialService
from models.epiplexity import KnowledgeNode, KnowledgeTransfer
from datetime import datetime, timedelta


class TestKnowledgeValueIncome:
    """测试知识价值收益计算"""

    def test_income_types_has_knowledge_value(self):
        """测试收入类型包含知识价值"""
        assert "KNOWLEDGE_VALUE" in FinancialService.INCOME_TYPES

    def test_knowledge_value_config(self):
        """测试知识价值配置"""
        kv = FinancialService.INCOME_TYPES["KNOWLEDGE_VALUE"]
        assert kv["creation_reward"] == 100
        assert kv["transfer_reward"] == 50
        assert kv["usage_reward"] == 10
        assert kv["quality_multiplier"] == 2.0

    def test_calculate_knowledge_value_income_no_nodes(self, db_session):
        """测试无知识节点时返回0"""
        result = FinancialService.calculate_knowledge_value_income(
            db=db_session,
            agent_id=999,
            period_days=30
        )

        assert result["creation_income"] == 0
        assert result["transfer_income"] == 0
        assert result["usage_income"] == 0
        assert result["quality_bonus"] == 0
        assert result["total_knowledge_income"] == 0

    def test_calculate_knowledge_value_income_with_nodes(self, db_session):
        """测试有知识节点时计算正确"""
        # 创建5个知识节点
        for i in range(5):
            node = KnowledgeNode(
                content=f"Knowledge {i}",
                content_hash=f"hash_{i}",
                content_type="code",
                epiplexity=0.5,
                learnability=0.6,
                transferability=0.7,
                usage_count=10,
                transfer_count=2,
                quality_score=0.7,
                created_by_agent_id=1,
                created_at=datetime.utcnow()
            )
            db_session.add(node)

        db_session.commit()

        result = FinancialService.calculate_knowledge_value_income(
            db=db_session,
            agent_id=1,
            period_days=30
        )

        # 5个节点 * 100 = 500
        assert result["creation_income"] == 500
        assert result["nodes_created"] == 5
        assert result["total_knowledge_income"] > 0

    def test_calculate_knowledge_value_income_with_transfers(self, db_session):
        """测试包含知识迁移时计算正确"""
        # 创建知识节点
        node = KnowledgeNode(
            content="Test knowledge",
            content_hash="hash_1",
            content_type="code",
            epiplexity=0.6,
            learnability=0.7,
            transferability=0.8,
            usage_count=5,
            transfer_count=3,
            quality_score=0.9,
            created_by_agent_id=1,
            created_at=datetime.utcnow()
        )
        db_session.add(node)
        db_session.commit()

        # 创建3个成功的迁移
        for i in range(3):
            transfer = KnowledgeTransfer(
                knowledge_node_id=node.id,
                from_task_id=i + 1,
                to_task_id=i + 10,
                success=True,
                value_created=10.0,
                created_at=datetime.utcnow()
            )
            db_session.add(transfer)

        db_session.commit()

        result = FinancialService.calculate_knowledge_value_income(
            db=db_session,
            agent_id=1,
            period_days=30
        )

        # 创建收益: 1 * 100 = 100
        assert result["creation_income"] == 100
        # 迁移收益: 3 * 50 = 150
        assert result["transfer_income"] == 150
        # 使用收益: 5 * 10 = 50
        assert result["usage_income"] == 50
        # 总收益 >= 300
        assert result["total_knowledge_income"] >= 300

    def test_calculate_knowledge_value_income_quality_bonus(self, db_session):
        """测试高质量知识奖励"""
        # 创建3个高质量节点
        for i in range(3):
            node = KnowledgeNode(
                content=f"High quality {i}",
                content_hash=f"hash_hq_{i}",
                content_type="code",
                epiplexity=0.8,
                learnability=0.8,
                transferability=0.8,
                usage_count=10,
                transfer_count=2,
                quality_score=0.9,  # 高质量
                created_by_agent_id=1,
                created_at=datetime.utcnow()
            )
            db_session.add(node)

        db_session.commit()

        result = FinancialService.calculate_knowledge_value_income(
            db=db_session,
            agent_id=1,
            period_days=30
        )

        # 创建收益: 3 * 100 = 300
        assert result["creation_income"] == 300
        # 质量奖励: 3 * 100 * (2.0 - 1) = 300
        assert result["quality_bonus"] == 300
        assert result["high_quality_nodes"] == 3

    def test_calculate_knowledge_value_income_period(self, db_session):
        """测试时间周期过滤"""
        # 创建旧节点（超出周期）
        old_node = KnowledgeNode(
            content="Old knowledge",
            content_hash="hash_old",
            content_type="code",
            epiplexity=0.5,
            learnability=0.6,
            transferability=0.7,
            usage_count=10,
            transfer_count=2,
            quality_score=0.7,
            created_by_agent_id=1,
            created_at=datetime.utcnow() - timedelta(days=60)
        )
        db_session.add(old_node)

        # 创建新节点（在周期内）
        new_node = KnowledgeNode(
            content="New knowledge",
            content_hash="hash_new",
            content_type="code",
            epiplexity=0.5,
            learnability=0.6,
            transferability=0.7,
            usage_count=10,
            transfer_count=2,
            quality_score=0.7,
            created_by_agent_id=1,
            created_at=datetime.utcnow()
        )
        db_session.add(new_node)

        db_session.commit()

        result = FinancialService.calculate_knowledge_value_income(
            db=db_session,
            agent_id=1,
            period_days=30
        )

        # 只统计新节点
        assert result["nodes_created"] == 1
        assert result["creation_income"] == 100


class TestTaskIncomeWithKnowledge:
    """测试包含知识价值的任务收入计算"""

    def test_calculate_task_income_with_knowledge_value(self):
        """测试包含知识价值的收入计算"""
        result = FinancialService.calculate_task_income(
            base_reward=10000,
            quality_rating=4.8,
            is_innovative=True,
            knowledge_value_income=2000
        )

        # base: 10000
        # quality_bonus: 10000 * 0.5 = 5000
        # innovation: 500
        # knowledge: 2000
        # total: 17500

        assert result["base_reward"] == 10000
        assert result["quality_bonus"] == 5000
        assert result["innovation_bonus"] == 500
        assert result["knowledge_value_income"] == 2000
        assert result["total_income"] == 17500

    def test_calculate_task_income_backward_compatible(self):
        """测试向后兼容（不传knowledge_value_income）"""
        result = FinancialService.calculate_task_income(
            base_reward=10000,
            quality_rating=4.8,
            is_innovative=True
        )

        # 不传knowledge_value_income时默认为0
        assert result["knowledge_value_income"] == 0
        assert result["total_income"] == 15500

    def test_calculate_task_income_only_knowledge(self):
        """测试仅知识价值收益"""
        result = FinancialService.calculate_task_income(
            base_reward=10000,
            knowledge_value_income=3000
        )

        # base: 10000
        # knowledge: 3000
        # total: 13000

        assert result["base_reward"] == 10000
        assert result["knowledge_value_income"] == 3000
        assert result["total_income"] == 13000

    def test_knowledge_value_impact_on_income(self):
        """测试知识价值对收入的影响"""
        base_params = {
            "base_reward": 10000,
            "quality_rating": 4.0,
            "is_innovative": False
        }

        # 不同的知识价值收益
        income_no_kv = FinancialService.calculate_task_income(**base_params, knowledge_value_income=0)
        income_low_kv = FinancialService.calculate_task_income(**base_params, knowledge_value_income=1000)
        income_high_kv = FinancialService.calculate_task_income(**base_params, knowledge_value_income=5000)

        # 验证递增关系
        assert income_no_kv["total_income"] < income_low_kv["total_income"] < income_high_kv["total_income"]

        # 验证差异
        assert income_low_kv["total_income"] - income_no_kv["total_income"] == 1000
        assert income_high_kv["total_income"] - income_no_kv["total_income"] == 5000


class TestROIWithKnowledge:
    """测试包含知识价值的ROI计算"""

    def test_roi_with_knowledge_value_income(self):
        """测试知识价值提升ROI"""
        # 场景1: 无知识价值
        task_income_no_kv = FinancialService.calculate_task_income(
            base_reward=10000,
            knowledge_value_income=0
        )
        roi_no_kv = task_income_no_kv["total_income"] / 5000  # 假设成本5000

        # 场景2: 有知识价值
        task_income_with_kv = FinancialService.calculate_task_income(
            base_reward=10000,
            knowledge_value_income=3000
        )
        roi_with_kv = task_income_with_kv["total_income"] / 5000

        # 知识价值应该提升ROI
        assert roi_with_kv > roi_no_kv
        assert roi_with_kv == 2.6  # (10000 + 3000) / 5000
        assert roi_no_kv == 2.0    # 10000 / 5000

    def test_roi_improvement_percentage(self):
        """测试ROI提升百分比"""
        base_reward = 10000
        cost = 5000
        knowledge_income = 2500

        # 原ROI
        original_roi = base_reward / cost  # 2.0

        # 新ROI
        total_income = base_reward + knowledge_income
        new_roi = total_income / cost  # 2.5

        # ROI提升
        improvement = (new_roi - original_roi) / original_roi * 100

        assert improvement == 25.0  # 提升25%


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models.epiplexity import Base as EpiplexityBase

    engine = create_engine("sqlite:///:memory:")
    EpiplexityBase.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
