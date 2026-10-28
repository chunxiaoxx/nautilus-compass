"""
测试知识积累可视化服务
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.epiplexity import KnowledgeNode, KnowledgeTransfer, EpiplexityMeasure
from models.agent_survival import AgentSurvival
from models.agent_v2 import AgentV2, Base as AgentBase
from models.database import Base as DatabaseBase
from models.agent_survival import Base as SurvivalBase
from services.knowledge_visualization_service import KnowledgeVisualizationService


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_knowledge_visualization.db"
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

    # 创建测试Agent
    agent = AgentV2(
        address="0x1234567890123456789012345678901234567890",
        name="Test Agent",
        reputation=100
    )
    db.add(agent)
    db.commit()

    yield db
    db.close()

    # 清理所有表
    DatabaseBase.metadata.drop_all(bind=engine)
    AgentBase.metadata.drop_all(bind=engine)
    SurvivalBase.metadata.drop_all(bind=engine)


class TestKnowledgeVisualizationService:
    """测试知识可视化服务"""

    @pytest.fixture
    def sample_agent_id(self):
        """测试Agent ID"""
        return 1

    @pytest.fixture
    def sample_knowledge_nodes(self, test_db: Session, sample_agent_id):
        """创建测试知识节点"""
        nodes = []
        base_time = datetime.utcnow() - timedelta(days=30)

        # 创建不同类型和复杂度的节点
        test_data = [
            ("CODE", "HIGH", 0.85, "backend"),
            ("CODE", "MEDIUM", 0.65, "backend"),
            ("CONCEPT", "LOW", 0.35, "theory"),
            ("PATTERN", "HIGH", 0.78, "design"),
            ("SOLUTION", "MEDIUM", 0.55, "problem_solving"),
            ("CODE", "HIGH", 0.82, "frontend"),
            ("CONCEPT", "MEDIUM", 0.60, "theory"),
            ("PATTERN", "LOW", 0.40, "design"),
            ("CODE", "MEDIUM", 0.68, "backend"),
            ("SOLUTION", "HIGH", 0.75, "problem_solving")
        ]

        for idx, (content_type, complexity, epiplexity, category) in enumerate(test_data):
            node = KnowledgeNode(
                content=f"Test knowledge content {idx}",
                content_hash=f"hash_{idx}_{sample_agent_id}",
                content_type=content_type,
                epiplexity=epiplexity,
                learnability=epiplexity * 0.9,
                transferability=epiplexity * 0.8,
                complexity_level=complexity,
                created_by_agent_id=sample_agent_id,
                category=category,
                usage_count=idx + 1,
                transfer_count=idx % 3,
                quality_score=epiplexity * 0.85,
                created_at=base_time + timedelta(days=idx * 3)
            )
            test_db.add(node)
            nodes.append(node)

        test_db.commit()
        for node in nodes:
            test_db.refresh(node)

        # 添加节点关系
        if len(nodes) >= 3:
            nodes[1].parent_nodes = [nodes[0].id]
            nodes[2].parent_nodes = [nodes[0].id]
            nodes[0].child_nodes = [nodes[1].id, nodes[2].id]
            nodes[1].related_nodes = [nodes[2].id]
            test_db.commit()

        return nodes

    @pytest.fixture
    def sample_transfers(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """创建测试知识迁移记录"""
        transfers = []
        base_time = datetime.utcnow() - timedelta(days=20)

        for idx, node in enumerate(sample_knowledge_nodes[:5]):
            transfer = KnowledgeTransfer(
                knowledge_node_id=node.id,
                from_task_id=100 + idx,
                to_task_id=200 + idx,
                transferred_by_agent_id=sample_agent_id,
                success=idx % 2 == 0,
                adaptation_required=idx % 3 == 0,
                created_at=base_time + timedelta(days=idx * 2)
            )
            test_db.add(transfer)
            transfers.append(transfer)

        test_db.commit()
        return transfers

    @pytest.fixture
    def sample_survival_records(self, test_db: Session, sample_agent_id):
        """创建测试生存记录"""
        # 删除所有现有记录
        test_db.query(AgentSurvival).filter(
            AgentSurvival.agent_id == sample_agent_id
        ).delete()
        test_db.commit()

        # 只创建一条记录，使用最新的数据
        base_time = datetime.utcnow() - timedelta(days=60)

        record = AgentSurvival(
            agent_id=sample_agent_id,
            total_score=850,  # 最终分数
            roi=1.7,  # 最终ROI
            updated_at=base_time + timedelta(weeks=7)
        )
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)

        return [record]

    # ==================== 知识图谱测试 ====================

    def test_generate_knowledge_graph_basic(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试生成基础知识图谱"""
        result = KnowledgeVisualizationService.generate_knowledge_graph(
            db=test_db,
            agent_id=sample_agent_id
        )

        assert "nodes" in result
        assert "edges" in result
        assert "stats" in result
        assert len(result["nodes"]) == len(sample_knowledge_nodes)
        assert result["stats"]["total_nodes"] == len(sample_knowledge_nodes)

    def test_generate_knowledge_graph_with_max_nodes(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试限制最大节点数"""
        max_nodes = 5
        result = KnowledgeVisualizationService.generate_knowledge_graph(
            db=test_db,
            agent_id=sample_agent_id,
            max_nodes=max_nodes
        )

        assert len(result["nodes"]) <= max_nodes
        assert result["stats"]["total_nodes"] <= max_nodes

    def test_generate_knowledge_graph_with_min_epiplexity(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试Epiplexity阈值过滤"""
        min_epiplexity = 0.7
        result = KnowledgeVisualizationService.generate_knowledge_graph(
            db=test_db,
            agent_id=sample_agent_id,
            min_epiplexity=min_epiplexity
        )

        for node in result["nodes"]:
            assert node["epiplexity"] >= min_epiplexity

    def test_generate_knowledge_graph_node_structure(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试节点数据结构"""
        result = KnowledgeVisualizationService.generate_knowledge_graph(
            db=test_db,
            agent_id=sample_agent_id
        )

        node = result["nodes"][0]
        assert "id" in node
        assert "db_id" in node
        assert "label" in node
        assert "type" in node
        assert "epiplexity" in node
        assert "complexity" in node
        assert "usage_count" in node
        assert "quality_score" in node

    def test_generate_knowledge_graph_edges(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试边关系"""
        result = KnowledgeVisualizationService.generate_knowledge_graph(
            db=test_db,
            agent_id=sample_agent_id
        )

        assert len(result["edges"]) > 0
        edge = result["edges"][0]
        assert "source" in edge
        assert "target" in edge
        assert "type" in edge
        assert "weight" in edge

    def test_generate_knowledge_graph_stats(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试统计信息"""
        result = KnowledgeVisualizationService.generate_knowledge_graph(
            db=test_db,
            agent_id=sample_agent_id
        )

        stats = result["stats"]
        assert "total_nodes" in stats
        assert "total_edges" in stats
        assert "avg_epiplexity" in stats
        assert "complexity_distribution" in stats
        assert stats["avg_epiplexity"] > 0

    def test_generate_knowledge_graph_empty(self, test_db: Session):
        """测试空知识图谱"""
        result = KnowledgeVisualizationService.generate_knowledge_graph(
            db=test_db,
            agent_id=99999
        )

        assert result["nodes"] == []
        assert result["edges"] == []
        assert result["stats"]["total_nodes"] == 0

    # ==================== 学习进度测试 ====================

    def test_generate_learning_progress_basic(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试生成基础学习进度"""
        result = KnowledgeVisualizationService.generate_learning_progress(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        assert "timeline" in result
        assert "summary" in result
        assert len(result["timeline"]) == 31  # 30天 + 今天

    def test_generate_learning_progress_timeline_structure(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试时间线数据结构"""
        result = KnowledgeVisualizationService.generate_learning_progress(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        day = result["timeline"][0]
        assert "date" in day
        assert "new_nodes" in day
        assert "total_nodes" in day
        assert "avg_epiplexity" in day
        assert "knowledge_transfers" in day

    def test_generate_learning_progress_cumulative(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试累计节点数递增"""
        result = KnowledgeVisualizationService.generate_learning_progress(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        timeline = result["timeline"]
        for i in range(1, len(timeline)):
            assert timeline[i]["total_nodes"] >= timeline[i-1]["total_nodes"]

    def test_generate_learning_progress_summary(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试汇总统计"""
        result = KnowledgeVisualizationService.generate_learning_progress(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        summary = result["summary"]
        assert "total_knowledge_nodes" in summary
        assert "new_nodes_in_period" in summary
        assert "total_transfers" in summary
        assert "avg_daily_growth" in summary
        assert "learning_velocity" in summary

    def test_generate_learning_progress_with_transfers(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_transfers):
        """测试包含知识迁移的学习进度"""
        result = KnowledgeVisualizationService.generate_learning_progress(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        assert result["summary"]["total_transfers"] > 0

    def test_generate_learning_progress_empty(self, test_db: Session):
        """测试空学习进度"""
        result = KnowledgeVisualizationService.generate_learning_progress(
            db=test_db,
            agent_id=99999,
            days=30
        )

        assert len(result["timeline"]) == 31
        assert result["summary"]["total_knowledge_nodes"] == 0

    # ==================== 成长轨迹测试 ====================

    def test_generate_growth_trajectory_basic(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_survival_records):
        """测试生成基础成长轨迹"""
        result = KnowledgeVisualizationService.generate_growth_trajectory(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        assert "trajectory" in result
        assert "milestones" in result
        assert "growth_rate" in result

    def test_generate_growth_trajectory_structure(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_survival_records):
        """测试轨迹数据结构"""
        result = KnowledgeVisualizationService.generate_growth_trajectory(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        if result["trajectory"]:
            point = result["trajectory"][0]
            assert "week" in point
            assert "knowledge_score" in point
            assert "node_count" in point
            assert "survival_score" in point
            assert "roi" in point

    def test_generate_growth_trajectory_milestones(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试里程碑识别"""
        result = KnowledgeVisualizationService.generate_growth_trajectory(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        milestones = result["milestones"]
        assert len(milestones) > 0

        milestone = milestones[0]
        assert "date" in milestone
        assert "type" in milestone
        assert "description" in milestone

    def test_generate_growth_trajectory_growth_rate(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_survival_records):
        """测试成长率计算"""
        result = KnowledgeVisualizationService.generate_growth_trajectory(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        growth_rate = result["growth_rate"]
        assert "knowledge" in growth_rate
        assert "survival" in growth_rate
        assert "overall" in growth_rate

    def test_generate_growth_trajectory_empty(self, test_db: Session):
        """测试空成长轨迹"""
        result = KnowledgeVisualizationService.generate_growth_trajectory(
            db=test_db,
            agent_id=99999,
            days=90
        )

        assert result["trajectory"] == []
        assert result["milestones"] == []

    # ==================== 知识热力图测试 ====================

    def test_generate_knowledge_heatmap_basic(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试生成知识热力图"""
        result = KnowledgeVisualizationService.generate_knowledge_heatmap(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        assert "by_type" in result
        assert "by_complexity" in result
        assert "by_category" in result

    def test_generate_knowledge_heatmap_by_type(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试按类型分组"""
        result = KnowledgeVisualizationService.generate_knowledge_heatmap(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        by_type = result["by_type"]
        assert "CODE" in by_type
        assert by_type["CODE"] > 0

    def test_generate_knowledge_heatmap_by_complexity(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试按复杂度分组"""
        result = KnowledgeVisualizationService.generate_knowledge_heatmap(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        by_complexity = result["by_complexity"]
        assert "HIGH" in by_complexity or "MEDIUM" in by_complexity or "LOW" in by_complexity

    def test_generate_knowledge_heatmap_by_category(self, test_db: Session, sample_agent_id, sample_knowledge_nodes):
        """测试按分类分组"""
        result = KnowledgeVisualizationService.generate_knowledge_heatmap(
            db=test_db,
            agent_id=sample_agent_id,
            days=90
        )

        by_category = result["by_category"]
        assert len(by_category) > 0

    def test_generate_knowledge_heatmap_empty(self, test_db: Session):
        """测试空热力图"""
        result = KnowledgeVisualizationService.generate_knowledge_heatmap(
            db=test_db,
            agent_id=99999,
            days=90
        )

        assert result["by_type"] == {}
        assert result["by_complexity"] == {}
        assert result["by_category"] == {}

    # ==================== 迁移网络测试 ====================

    def test_generate_transfer_network_basic(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_transfers):
        """测试生成迁移网络"""
        result = KnowledgeVisualizationService.generate_transfer_network(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        assert "nodes" in result
        assert "edges" in result
        assert "stats" in result

    def test_generate_transfer_network_nodes(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_transfers):
        """测试迁移网络节点"""
        result = KnowledgeVisualizationService.generate_transfer_network(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        assert len(result["nodes"]) > 0
        node = result["nodes"][0]
        assert "id" in node
        assert "type" in node
        assert "transfers_out" in node
        assert "transfers_in" in node

    def test_generate_transfer_network_edges(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_transfers):
        """测试迁移网络边"""
        result = KnowledgeVisualizationService.generate_transfer_network(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        assert len(result["edges"]) > 0
        edge = result["edges"][0]
        assert "source" in edge
        assert "target" in edge
        assert "knowledge_id" in edge
        assert "success" in edge

    def test_generate_transfer_network_stats(self, test_db: Session, sample_agent_id, sample_knowledge_nodes, sample_transfers):
        """测试迁移网络统计"""
        result = KnowledgeVisualizationService.generate_transfer_network(
            db=test_db,
            agent_id=sample_agent_id,
            days=30
        )

        stats = result["stats"]
        assert "total_transfers" in stats
        assert "successful_transfers" in stats
        assert "success_rate" in stats
        assert 0 <= stats["success_rate"] <= 1

    def test_generate_transfer_network_empty(self, test_db: Session):
        """测试空迁移网络"""
        result = KnowledgeVisualizationService.generate_transfer_network(
            db=test_db,
            agent_id=99999,
            days=30
        )

        assert result["nodes"] == []
        assert result["edges"] == []
        assert result["stats"]["total_transfers"] == 0


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    class MockDB:
        def query(self, model):
            return self

        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args):
            return self

        def all(self):
            return []

        def first(self):
            return None

        def scalar(self):
            return 0

    return MockDB()
