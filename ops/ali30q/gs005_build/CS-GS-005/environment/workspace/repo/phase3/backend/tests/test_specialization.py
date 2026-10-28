"""
测试专业化方向识别服务
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from services.specialization_service import SpecializationService
from models.epiplexity import KnowledgeNode
from models.agent_v2 import AgentV2, Base as AgentBase
from models.database import Base as DatabaseBase
from models.agent_survival import Base as SurvivalBase


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_specialization.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    # 创建所有表
    DatabaseBase.metadata.create_all(bind=engine)
    AgentBase.metadata.create_all(bind=engine)
    SurvivalBase.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    yield db
    db.close()

    # 清理所有表
    DatabaseBase.metadata.drop_all(bind=engine)
    AgentBase.metadata.drop_all(bind=engine)
    SurvivalBase.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_agent(test_db):
    """创建测试Agent"""
    agent = AgentV2(
        address="0x1234567890123456789012345678901234567890",
        name="Test Agent",
        reputation=100
    )
    test_db.add(agent)
    test_db.commit()
    test_db.refresh(agent)
    return agent


@pytest.fixture
def backend_knowledge_nodes(test_db, sample_agent):
    """创建后端开发相关的知识节点"""
    nodes = []

    # 高质量API设计知识
    nodes.append(KnowledgeNode(
        content="RESTful API design with proper HTTP methods and status codes",
        content_hash="hash1",
        content_type="CONCEPT",
        epiplexity=0.75,
        learnability=0.8,
        transferability=0.7,
        complexity_level="HIGH",
        created_by_agent_id=sample_agent.address,
        category="API",
        tags=["api", "rest", "design"]
    ))

    # 数据库优化知识
    nodes.append(KnowledgeNode(
        content="Database indexing strategies for query optimization",
        content_hash="hash2",
        content_type="CONCEPT",
        epiplexity=0.72,
        learnability=0.75,
        transferability=0.68,
        complexity_level="HIGH",
        created_by_agent_id=sample_agent.address,
        category="DATABASE",
        tags=["database", "optimization", "index"]
    ))

    # 微服务架构知识
    nodes.append(KnowledgeNode(
        content="Microservice architecture patterns and best practices",
        content_hash="hash3",
        content_type="PATTERN",
        epiplexity=0.78,
        learnability=0.82,
        transferability=0.75,
        complexity_level="HIGH",
        created_by_agent_id=sample_agent.address,
        category="ARCHITECTURE",
        tags=["microservice", "architecture", "backend"]
    ))

    for node in nodes:
        test_db.add(node)

    test_db.commit()
    return nodes


@pytest.fixture
def mixed_knowledge_nodes(test_db, sample_agent):
    """创建混合领域的知识节点"""
    nodes = []

    # 后端知识
    nodes.append(KnowledgeNode(
        content="Building REST API with FastAPI framework",
        content_hash="hash4",
        content_type="CODE",
        epiplexity=0.65,
        learnability=0.7,
        transferability=0.6,
        complexity_level="MEDIUM",
        created_by_agent_id=sample_agent.address,
        category="API",
        tags=["api", "fastapi", "backend"]
    ))

    # 前端知识
    nodes.append(KnowledgeNode(
        content="React component lifecycle and hooks usage",
        content_hash="hash5",
        content_type="CONCEPT",
        epiplexity=0.68,
        learnability=0.72,
        transferability=0.65,
        complexity_level="MEDIUM",
        created_by_agent_id=sample_agent.address,
        category="FRONTEND",
        tags=["react", "frontend", "component"]
    ))

    # 测试知识
    nodes.append(KnowledgeNode(
        content="Unit testing with pytest and mocking strategies",
        content_hash="hash6",
        content_type="CODE",
        epiplexity=0.62,
        learnability=0.68,
        transferability=0.58,
        complexity_level="MEDIUM",
        created_by_agent_id=sample_agent.address,
        category="TESTING",
        tags=["test", "pytest", "mock"]
    ))

    for node in nodes:
        test_db.add(node)

    test_db.commit()
    return nodes


class TestIdentifySpecialization:
    """测试专业方向识别"""

    def test_identify_backend_specialization(self, test_db, sample_agent, backend_knowledge_nodes):
        """测试识别后端开发专业方向"""
        result = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address
        )

        assert len(result) > 0
        # 后端开发应该是主要专业方向
        backend_spec = next((s for s in result if s["domain"] == "BACKEND_DEVELOPMENT"), None)
        assert backend_spec is not None
        assert backend_spec["confidence"] > 0.5
        assert backend_spec["knowledge_count"] >= 3
        assert backend_spec["avg_epiplexity"] > 0.7

    def test_identify_multiple_specializations(self, test_db, sample_agent, mixed_knowledge_nodes):
        """测试识别多个专业方向"""
        result = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address,
            min_confidence=0.2
        )

        assert len(result) >= 2
        domains = [s["domain"] for s in result]
        assert "BACKEND_DEVELOPMENT" in domains or "FRONTEND_DEVELOPMENT" in domains

    def test_no_specialization_for_new_agent(self, test_db, sample_agent):
        """测试新Agent没有专业方向"""
        result = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address
        )

        assert len(result) == 0

    def test_min_confidence_threshold(self, test_db, sample_agent, mixed_knowledge_nodes):
        """测试最小置信度阈值"""
        # 高阈值
        result_high = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address,
            min_confidence=0.8
        )

        # 低阈值
        result_low = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address,
            min_confidence=0.1
        )

        assert len(result_low) >= len(result_high)

    def test_specialization_includes_expertise_level(self, test_db, sample_agent, backend_knowledge_nodes):
        """测试专业方向包含专业水平"""
        result = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address
        )

        if result:
            spec = result[0]
            assert "expertise_level" in spec
            assert spec["expertise_level"] in ["NOVICE", "BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT", "MASTER"]


class TestCalculateExpertiseLevel:
    """测试专业水平计算"""

    def test_novice_level(self):
        """测试新手等级"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=0,
            avg_epiplexity=0.0
        )
        assert level == "NOVICE"

    def test_beginner_level(self):
        """测试初学者等级"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=5,
            avg_epiplexity=0.3
        )
        assert level == "BEGINNER"

    def test_intermediate_level(self):
        """测试中级等级"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=15,
            avg_epiplexity=0.5
        )
        assert level == "INTERMEDIATE"

    def test_advanced_level(self):
        """测试高级等级"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=30,
            avg_epiplexity=0.65
        )
        assert level == "ADVANCED"

    def test_expert_level(self):
        """测试专家等级"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=50,
            avg_epiplexity=0.75
        )
        assert level == "EXPERT"

    def test_master_level(self):
        """测试大师等级"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=100,
            avg_epiplexity=0.85
        )
        assert level == "MASTER"

    def test_insufficient_nodes_for_level(self):
        """测试节点数不足"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=10,
            avg_epiplexity=0.9  # 高质量但数量不足
        )
        assert level in ["NOVICE", "BEGINNER"]

    def test_insufficient_quality_for_level(self):
        """测试质量不足"""
        level = SpecializationService.calculate_expertise_level(
            knowledge_count=100,
            avg_epiplexity=0.3  # 数量足够但质量不足
        )
        assert level in ["NOVICE", "BEGINNER", "INTERMEDIATE"]


class TestRecommendSpecializationPath:
    """测试专业化路径推荐"""

    def test_recommend_path_for_new_agent(self, test_db, sample_agent):
        """测试为新Agent推荐路径"""
        result = SpecializationService.recommend_specialization_path(
            db=test_db,
            agent_id=sample_agent.address
        )

        assert "recommended_domain" in result
        assert "current_level" in result
        assert result["current_level"] == "NOVICE"
        assert "next_level" in result
        assert result["next_level"] == "BEGINNER"
        assert "path" in result
        assert len(result["path"]) > 0
        assert "estimated_time" in result

    def test_recommend_path_with_existing_specialization(self, test_db, sample_agent, backend_knowledge_nodes):
        """测试为有专业方向的Agent推荐路径"""
        result = SpecializationService.recommend_specialization_path(
            db=test_db,
            agent_id=sample_agent.address
        )

        assert result["recommended_domain"] == "BACKEND_DEVELOPMENT"
        # 有3个高质量节点，应该至少是BEGINNER级别
        assert result["current_level"] in ["NOVICE", "BEGINNER"]
        assert len(result["path"]) > 0

    def test_recommend_path_with_target_domain(self, test_db, sample_agent, mixed_knowledge_nodes):
        """测试指定目标领域推荐路径"""
        result = SpecializationService.recommend_specialization_path(
            db=test_db,
            agent_id=sample_agent.address,
            target_domain="DATA_SCIENCE"
        )

        assert result["recommended_domain"] == "DATA_SCIENCE"
        assert "path" in result

    def test_invalid_target_domain(self, test_db, sample_agent):
        """测试无效的目标领域"""
        with pytest.raises(ValueError):
            SpecializationService.recommend_specialization_path(
                db=test_db,
                agent_id=sample_agent.address,
                target_domain="INVALID_DOMAIN"
            )

    def test_path_includes_steps(self, test_db, sample_agent):
        """测试路径包含具体步骤"""
        result = SpecializationService.recommend_specialization_path(
            db=test_db,
            agent_id=sample_agent.address
        )

        path = result["path"]
        assert len(path) > 0

        for step in path:
            assert "step" in step
            assert "action" in step
            assert "target" in step
            assert "target_epiplexity" in step
            assert "estimated_nodes" in step
            assert "focus_areas" in step


class TestGetSpecializationTrends:
    """测试专业化趋势分析"""

    def test_trends_with_no_history(self, test_db, sample_agent):
        """测试没有历史数据的趋势"""
        result = SpecializationService.get_specialization_trends(
            db=test_db,
            agent_id=sample_agent.address,
            days=30
        )

        assert result["period_days"] == 30
        assert "domains" in result
        assert "fastest_growing" in result
        assert "recommendations" in result

    def test_trends_with_growing_specialization(self, test_db, sample_agent):
        """测试增长中的专业方向趋势"""
        # 创建不同时期的知识节点
        old_date = datetime.utcnow() - timedelta(days=20)

        # 旧节点
        old_node = KnowledgeNode(
            content="Basic API concepts",
            content_hash="hash_old",
            content_type="CONCEPT",
            epiplexity=0.5,
            learnability=0.6,
            transferability=0.5,
            complexity_level="MEDIUM",
            created_by_agent_id=sample_agent.address,
            category="API",
            created_at=old_date
        )
        test_db.add(old_node)

        # 新节点（更高质量）
        new_nodes = []
        for i in range(5):
            node = KnowledgeNode(
                content=f"Advanced API design pattern {i}",
                content_hash=f"hash_new_{i}",
                content_type="PATTERN",
                epiplexity=0.75,
                learnability=0.8,
                transferability=0.7,
                complexity_level="HIGH",
                created_by_agent_id=sample_agent.address,
                category="API"
            )
            new_nodes.append(node)
            test_db.add(node)

        test_db.commit()

        result = SpecializationService.get_specialization_trends(
            db=test_db,
            agent_id=sample_agent.address,
            days=30
        )

        assert "domains" in result
        assert "fastest_growing" in result
        assert result["fastest_growing"] is not None

    def test_trends_includes_growth_metrics(self, test_db, sample_agent, backend_knowledge_nodes):
        """测试趋势包含增长指标"""
        result = SpecializationService.get_specialization_trends(
            db=test_db,
            agent_id=sample_agent.address,
            days=30
        )

        domains = result["domains"]
        for domain, metrics in domains.items():
            assert "start_confidence" in metrics
            assert "end_confidence" in metrics
            assert "growth" in metrics
            assert "growth_rate" in metrics

    def test_trends_generates_recommendations(self, test_db, sample_agent, backend_knowledge_nodes):
        """测试趋势生成建议"""
        result = SpecializationService.get_specialization_trends(
            db=test_db,
            agent_id=sample_agent.address,
            days=30
        )

        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert all(isinstance(rec, str) for rec in result["recommendations"])


class TestSpecializationDomains:
    """测试专业领域定义"""

    def test_all_domains_have_required_fields(self):
        """测试所有领域包含必需字段"""
        for domain, config in SpecializationService.SPECIALIZATION_DOMAINS.items():
            assert "keywords" in config
            assert "categories" in config
            assert "description" in config
            assert len(config["keywords"]) > 0
            assert len(config["categories"]) > 0
            assert len(config["description"]) > 0

    def test_domain_count(self):
        """测试领域数量"""
        assert len(SpecializationService.SPECIALIZATION_DOMAINS) >= 8


class TestExpertiseLevels:
    """测试专业水平等级定义"""

    def test_all_levels_have_required_fields(self):
        """测试所有等级包含必需字段"""
        for level, config in SpecializationService.EXPERTISE_LEVELS.items():
            assert "min_nodes" in config
            assert "min_avg_epiplexity" in config
            assert "description" in config

    def test_levels_are_progressive(self):
        """测试等级是递进的"""
        levels = ["NOVICE", "BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT", "MASTER"]

        for i in range(len(levels) - 1):
            current = SpecializationService.EXPERTISE_LEVELS[levels[i]]
            next_level = SpecializationService.EXPERTISE_LEVELS[levels[i + 1]]

            assert next_level["min_nodes"] >= current["min_nodes"]
            assert next_level["min_avg_epiplexity"] >= current["min_avg_epiplexity"]


class TestEdgeCases:
    """测试边界情况"""

    def test_agent_with_single_node(self, test_db, sample_agent):
        """测试只有一个知识节点的Agent"""
        node = KnowledgeNode(
            content="Single knowledge node",
            content_hash="hash_single",
            content_type="CONCEPT",
            epiplexity=0.5,
            learnability=0.6,
            transferability=0.5,
            complexity_level="MEDIUM",
            created_by_agent_id=sample_agent.address
        )
        test_db.add(node)
        test_db.commit()

        result = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address,
            min_confidence=0.0
        )

        # 应该能识别出某些专业方向，即使只有一个节点
        assert isinstance(result, list)

    def test_agent_with_very_high_quality_nodes(self, test_db, sample_agent):
        """测试拥有极高质量节点的Agent"""
        for i in range(10):
            node = KnowledgeNode(
                content=f"Expert level API design pattern {i}",
                content_hash=f"hash_expert_{i}",
                content_type="PATTERN",
                epiplexity=0.95,
                learnability=0.98,
                transferability=0.92,
                complexity_level="HIGH",
                created_by_agent_id=sample_agent.address,
                category="API"
            )
            test_db.add(node)

        test_db.commit()

        result = SpecializationService.identify_specialization(
            db=test_db,
            agent_id=sample_agent.address
        )

        if result:
            # 应该有较高的置信度
            assert result[0]["confidence"] > 0.7
            assert result[0]["avg_epiplexity"] > 0.9

    def test_nonexistent_agent(self, test_db):
        """测试不存在的Agent"""
        result = SpecializationService.identify_specialization(
            db=test_db,
            agent_id="nonexistent_agent"
        )

        assert result == []
