"""
测试知识价值集成到评分系统
"""
import pytest
from services.survival_service import SurvivalService
from models.epiplexity import KnowledgeNode, KnowledgeTransfer
from datetime import datetime


class TestKnowledgeValueIntegration:
    """测试知识价值集成"""

    def test_weights_sum_to_one(self):
        """测试权重总和为1"""
        weights = SurvivalService.WEIGHTS
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001, f"权重总和应为1.0，实际为{total}"

    def test_knowledge_weight_is_25_percent(self):
        """测试知识价值权重为25%"""
        assert SurvivalService.WEIGHTS["knowledge"] == 0.25

    def test_calculate_knowledge_value_no_nodes(self, db_session):
        """测试无知识节点时返回0"""
        value = SurvivalService.calculate_knowledge_value(db_session, agent_id=999)
        assert value == 0.0

    def test_calculate_knowledge_value_with_nodes(self, db_session):
        """测试有知识节点时计算正确"""
        # 创建测试知识节点
        nodes = []
        for i in range(5):
            node = KnowledgeNode(
                content=f"Test knowledge {i}",
                content_hash=f"hash_{i}",
                content_type="code",
                epiplexity=0.5 + i * 0.1,
                learnability=0.6,
                transferability=0.7,
                usage_count=i * 2,
                transfer_count=i,
                quality_score=0.8,
                created_by_agent_id=1
            )
            db_session.add(node)
            nodes.append(node)

        db_session.commit()

        # 计算知识价值
        value = SurvivalService.calculate_knowledge_value(db_session, agent_id=1)

        # 验证结果在合理范围内
        assert 0.0 <= value <= 1.0
        assert value > 0.0  # 有节点应该有价值

    def test_calculate_knowledge_value_with_transfers(self, db_session):
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
            created_by_agent_id=1
        )
        db_session.add(node)
        db_session.commit()

        # 创建知识迁移记录
        for i in range(3):
            transfer = KnowledgeTransfer(
                knowledge_node_id=node.id,
                from_task_id=i + 1,
                to_task_id=i + 10,
                success=i < 2,  # 2成功，1失败
                value_created=10.0 if i < 2 else 0.0
            )
            db_session.add(transfer)

        db_session.commit()

        # 计算知识价值
        value = SurvivalService.calculate_knowledge_value(db_session, agent_id=1)

        # 验证结果
        assert 0.0 <= value <= 1.0
        assert value > 0.0

    def test_calculate_total_score_with_knowledge(self):
        """测试包含知识价值的总分计算"""
        score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.8,
            efficiency_score=0.7,
            innovation_score=0.6,
            collaboration_score=0.5,
            knowledge_value=0.9
        )

        # 验证计算
        expected = (
            1000 * 0.25 +  # task: 250
            80 * 0.20 +    # quality: 16
            70 * 0.15 +    # efficiency: 10.5
            60 * 0.10 +    # innovation: 6
            50 * 0.05 +    # collaboration: 2.5
            90 * 0.25      # knowledge: 22.5
        )
        # Total: 250 + 16 + 10.5 + 6 + 2.5 + 22.5 = 307.5 -> 307

        assert score == int(expected)
        assert score == 307

    def test_calculate_total_score_backward_compatible(self):
        """测试向后兼容（不传knowledge_value）"""
        score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.8,
            efficiency_score=0.7,
            innovation_score=0.6,
            collaboration_score=0.5
        )

        # 不传knowledge_value时默认为0
        assert score > 0

    def test_knowledge_value_components(self, db_session):
        """测试知识价值各组成部分"""
        # 创建10个高质量节点
        for i in range(10):
            node = KnowledgeNode(
                content=f"High quality knowledge {i}",
                content_hash=f"hash_high_{i}",
                content_type="code",
                epiplexity=0.8,  # 高Epiplexity
                learnability=0.8,
                transferability=0.8,
                usage_count=10,  # 高使用频率
                transfer_count=5,
                quality_score=0.9,
                created_by_agent_id=1
            )
            db_session.add(node)

        db_session.commit()

        value = SurvivalService.calculate_knowledge_value(db_session, agent_id=1)

        # 高质量节点应该有高价值
        assert value > 0.5

    def test_knowledge_value_scaling(self, db_session):
        """测试知识价值随节点数量的扩展"""
        # 测试不同数量的节点
        for count in [1, 5, 10, 20]:
            # 清空之前的节点
            db_session.query(KnowledgeNode).delete()

            # 创建节点
            for i in range(count):
                node = KnowledgeNode(
                    content=f"Knowledge {i}",
                    content_hash=f"hash_{count}_{i}",
                    content_type="code",
                    epiplexity=0.5,
                    learnability=0.5,
                    transferability=0.5,
                    usage_count=5,
                    transfer_count=2,
                    quality_score=0.7,
                    created_by_agent_id=1
                )
                db_session.add(node)

            db_session.commit()

            value = SurvivalService.calculate_knowledge_value(db_session, agent_id=1)

            # 更多节点应该有更高价值（但有上限）
            assert 0.0 <= value <= 1.0

    def test_weight_adjustment_impact(self):
        """测试权重调整对总分的影响"""
        # 相同的输入
        params = {
            "task_score": 1000,
            "quality_score": 0.8,
            "efficiency_score": 0.7,
            "innovation_score": 0.6,
            "collaboration_score": 0.5
        }

        # 不同的知识价值
        score_low = SurvivalService.calculate_total_score(**params, knowledge_value=0.2)
        score_high = SurvivalService.calculate_total_score(**params, knowledge_value=0.9)

        # 高知识价值应该产生更高总分
        assert score_high > score_low

        # 差异应该显著（25%权重）
        diff = score_high - score_low
        assert diff > 10  # 至少有明显差异


class TestKnowledgeValueFormula:
    """测试知识价值计算公式"""

    def test_node_count_component(self, db_session):
        """测试节点数量组件"""
        # 创建5个节点（50%满分）
        for i in range(5):
            node = KnowledgeNode(
                content=f"Node {i}",
                content_hash=f"hash_{i}",
                content_type="code",
                epiplexity=0.0,  # 其他因素为0
                learnability=0.0,
                transferability=0.0,
                usage_count=0,
                transfer_count=0,
                quality_score=0.0,
                created_by_agent_id=1
            )
            db_session.add(node)

        db_session.commit()

        value = SurvivalService.calculate_knowledge_value(db_session, agent_id=1)

        # 节点数量贡献30%，5个节点=0.5，所以贡献0.5*0.3=0.15
        assert 0.10 <= value <= 0.20

    def test_epiplexity_component(self, db_session):
        """测试Epiplexity组件"""
        # 创建1个高Epiplexity节点
        node = KnowledgeNode(
            content="High epiplexity",
            content_hash="hash_high",
            content_type="code",
            epiplexity=1.0,  # 最高Epiplexity
            learnability=0.0,
            transferability=0.0,
            usage_count=0,
            transfer_count=0,
            quality_score=0.0,
            created_by_agent_id=1
        )
        db_session.add(node)
        db_session.commit()

        value = SurvivalService.calculate_knowledge_value(db_session, agent_id=1)

        # Epiplexity贡献40%，1.0*0.4=0.4
        # 加上节点数量贡献(1/10)*0.3=0.03
        # 总计约0.43
        assert 0.35 <= value <= 0.50


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models.epiplexity import Base as EpiplexityBase

    # 只创建Epiplexity相关的表
    engine = create_engine("sqlite:///:memory:")
    EpiplexityBase.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
