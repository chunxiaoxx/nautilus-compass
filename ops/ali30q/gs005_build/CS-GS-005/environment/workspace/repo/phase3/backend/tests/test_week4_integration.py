"""
Week 4集成测试
测试所有Week 4功能的端到端集成
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base as DatabaseBase, Agent, Task
from models.epiplexity import Base as EpiplexityBase, KnowledgeNode, KnowledgeTransfer
from models.agent_survival import Base as SurvivalBase, AgentSurvival, AgentTransaction
from services.survival_service import SurvivalService
from services.financial_service import FinancialService
from services.task_recommendation_service import TaskRecommendationService
from services.learning_path_service import LearningPathService
from services.learning_tracking_service import LearningTrackingService


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    engine = create_engine("sqlite:///:memory:")

    # 创建所有表
    DatabaseBase.metadata.create_all(engine)
    EpiplexityBase.metadata.create_all(engine)
    SurvivalBase.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def sample_agent(test_db):
    """创建示例Agent"""
    agent = Agent(
        agent_id=1,
        owner="0x1234567890abcdef1234567890abcdef12345678",
        name="Test Agent",
        reputation=100
    )
    test_db.add(agent)
    test_db.commit()
    return agent


@pytest.fixture
def sample_knowledge_nodes(test_db, sample_agent):
    """创建示例知识节点"""
    nodes = []
    categories = ["python", "javascript", "database", "api", "testing"]

    for i, category in enumerate(categories):
        for j in range(3):
            node = KnowledgeNode(
                content=f"{category} knowledge {j}",
                content_hash=f"hash_{category}_{j}",
                content_type="code",
                category=category,
                epiplexity=0.3 + (i * 0.1) + (j * 0.05),
                learnability=0.6 + (j * 0.1),
                transferability=0.7,
                complexity_level="MEDIUM",  # 添加必需字段
                usage_count=5 + j * 2,
                transfer_count=2 + j,
                quality_score=0.7 + (j * 0.1),
                created_by_agent_id=sample_agent.agent_id,
                created_at=datetime.utcnow() - timedelta(days=15 - i)
            )
            test_db.add(node)
            nodes.append(node)

    test_db.commit()
    return nodes


@pytest.fixture
def sample_transfers(test_db, sample_knowledge_nodes, sample_agent):
    """创建示例知识迁移"""
    transfers = []

    for i, node in enumerate(sample_knowledge_nodes[:10]):
        transfer = KnowledgeTransfer(
            knowledge_node_id=node.id,
            from_task_id=i + 1,
            to_task_id=i + 100,
            transferred_by_agent_id=sample_agent.agent_id,  # 添加必需字段
            success=i % 3 != 0,  # 2/3成功率
            value_created=10.0 if i % 3 != 0 else 0.0,
            created_at=datetime.utcnow() - timedelta(days=10 - i)
        )
        test_db.add(transfer)
        transfers.append(transfer)

    test_db.commit()
    return transfers


class TestKnowledgeValueScoringIntegration:
    """测试知识价值评分集成"""

    def test_knowledge_value_calculation_flow(self, test_db, sample_agent, sample_knowledge_nodes, sample_transfers):
        """测试知识价值计算完整流程"""
        # 1. 计算知识价值
        knowledge_value = SurvivalService.calculate_knowledge_value(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 验证知识价值在合理范围内
        assert 0.0 <= knowledge_value <= 1.0
        assert knowledge_value > 0.0  # 有节点应该有价值

        # 2. 计算总分（包含知识价值）
        total_score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.8,
            efficiency_score=0.7,
            innovation_score=0.6,
            collaboration_score=0.5,
            knowledge_value=knowledge_value
        )

        # 验证总分计算正确
        assert total_score > 0

        # 3. 验证知识价值权重为25%
        assert SurvivalService.WEIGHTS["knowledge"] == 0.25

        # 4. 验证权重总和为1
        total_weight = sum(SurvivalService.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_knowledge_value_components(self, test_db, sample_agent, sample_knowledge_nodes, sample_transfers):
        """测试知识价值各组成部分"""
        knowledge_value = SurvivalService.calculate_knowledge_value(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 验证组成部分都有贡献
        # 节点数量: 15个节点
        # 平均Epiplexity: 应该在0.3-0.8之间
        # 迁移成功率: 约2/3
        # 使用频率: 5-11次

        assert knowledge_value > 0.3  # 应该有显著价值


class TestROIEnhancementIntegration:
    """测试ROI增强集成"""

    def test_knowledge_value_income_calculation(self, test_db, sample_agent, sample_knowledge_nodes, sample_transfers):
        """测试知识价值收益计算"""
        # 计算知识价值收益
        kv_income = FinancialService.calculate_knowledge_value_income(
            db=test_db,
            agent_id=sample_agent.agent_id,
            period_days=30
        )

        # 验证收益结构
        assert "creation_income" in kv_income
        assert "transfer_income" in kv_income
        assert "usage_income" in kv_income
        assert "quality_bonus" in kv_income
        assert "total_knowledge_income" in kv_income

        # 验证收益计算
        assert kv_income["nodes_created"] == 15
        assert kv_income["creation_income"] == 15 * 100  # 15节点 * 100
        assert kv_income["transfer_income"] > 0  # 有成功迁移
        assert kv_income["usage_income"] > 0  # 有使用
        assert kv_income["total_knowledge_income"] > 0

    def test_task_income_with_knowledge_value(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试包含知识价值的任务收入"""
        # 计算知识价值收益
        kv_income = FinancialService.calculate_knowledge_value_income(
            db=test_db,
            agent_id=sample_agent.agent_id,
            period_days=30
        )

        # 计算任务收入（包含知识价值）
        task_income = FinancialService.calculate_task_income(
            base_reward=10000,
            quality_rating=4.5,
            is_innovative=True,
            knowledge_value_income=kv_income["total_knowledge_income"]
        )

        # 验证知识价值被包含
        assert task_income["knowledge_value_income"] == kv_income["total_knowledge_income"]
        assert task_income["total_income"] > 10000  # 应该高于基础奖励

    def test_roi_improvement_with_knowledge(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试知识价值对ROI的提升"""
        # 场景1: 无知识价值
        income_no_kv = FinancialService.calculate_task_income(
            base_reward=10000,
            knowledge_value_income=0
        )

        # 场景2: 有知识价值
        kv_income = FinancialService.calculate_knowledge_value_income(
            db=test_db,
            agent_id=sample_agent.agent_id,
            period_days=30
        )

        income_with_kv = FinancialService.calculate_task_income(
            base_reward=10000,
            knowledge_value_income=kv_income["total_knowledge_income"]
        )

        # 验证知识价值提升了收入
        assert income_with_kv["total_income"] > income_no_kv["total_income"]

        # 计算ROI提升
        cost = 5000
        roi_no_kv = income_no_kv["total_income"] / cost
        roi_with_kv = income_with_kv["total_income"] / cost

        assert roi_with_kv > roi_no_kv


class TestTaskRecommendationIntegration:
    """测试任务推荐集成"""

    def test_learning_capacity_calculation(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试学习能力计算"""
        capacity = TaskRecommendationService.calculate_agent_learning_capacity(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 验证学习能力在合理范围
        assert 0.0 <= capacity <= 1.0
        assert capacity > 0.3  # 有知识节点应该有一定能力

    def test_task_match_score_calculation(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试任务匹配分数计算"""
        # 计算Agent学习能力
        capacity = TaskRecommendationService.calculate_agent_learning_capacity(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 测试不同难度的任务
        test_cases = [
            (capacity, "optimal"),      # 完全匹配
            (capacity + 0.1, "optimal"), # 略难
            (capacity - 0.1, "optimal"), # 略易
            (capacity + 0.3, "challenging"),  # 太难
            (capacity - 0.3, "easy")     # 太简单
        ]

        for task_epiplexity, expected_level in test_cases:
            match_score, details = TaskRecommendationService.calculate_task_match_score(
                agent_capacity=capacity,
                task_epiplexity=task_epiplexity,
                agent_knowledge=sample_knowledge_nodes,
                task_requirements=None
            )

            assert 0.0 <= match_score <= 1.0
            assert "difficulty_level" in details
            assert "in_optimal_zone" in details

    def test_recommendation_explanation(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试推荐解释生成"""
        capacity = TaskRecommendationService.calculate_agent_learning_capacity(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        match_score, details = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=capacity,
            task_epiplexity=capacity,
            agent_knowledge=sample_knowledge_nodes,
            task_requirements=None
        )

        explanation = TaskRecommendationService.explain_recommendation(
            agent_capacity=capacity,
            task_epiplexity=capacity,
            match_score=match_score,
            details=details
        )

        assert isinstance(explanation, str)
        assert len(explanation) > 0


class TestLearningPathIntegration:
    """测试学习路径规划集成"""

    def test_knowledge_gap_analysis(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试知识缺口分析"""
        gap_analysis = LearningPathService.analyze_knowledge_gaps(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 验证分析结果结构
        assert "agent_id" in gap_analysis
        assert "current_knowledge" in gap_analysis
        assert "gaps" in gap_analysis
        assert isinstance(gap_analysis["gaps"], list)

    def test_learning_path_planning(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试学习路径规划"""
        learning_path = LearningPathService.plan_learning_path(
            db=test_db,
            agent_id=sample_agent.agent_id,
            max_steps=5
        )

        # 验证路径结构
        assert "agent_id" in learning_path
        assert "learning_path" in learning_path
        assert "summary" in learning_path
        assert "recommendations" in learning_path

        # 验证路径长度
        assert len(learning_path["learning_path"]) <= 5

        # 验证每个步骤的结构
        for step in learning_path["learning_path"]:
            assert "step_number" in step
            assert "category" in step
            assert "goal" in step
            assert "start_difficulty" in step
            assert "target_difficulty" in step
            assert "estimated_tasks" in step
            assert "estimated_days" in step

    def test_prerequisite_check(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试前置知识检查"""
        result = LearningPathService.check_prerequisites(
            db=test_db,
            agent_id=sample_agent.agent_id,
            required_knowledge=["python", "javascript"]
        )

        # 验证检查结果
        assert "all_prerequisites_met" in result
        assert "details" in result
        assert "missing_count" in result
        assert isinstance(result["all_prerequisites_met"], bool)

    def test_next_step_suggestions(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试下一步建议"""
        suggestions = LearningPathService.suggest_next_steps(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 验证建议结构
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        for suggestion in suggestions:
            assert "type" in suggestion
            assert "message" in suggestion


class TestLearningTrackingIntegration:
    """测试学习能力追踪集成"""

    def test_learning_progress_tracking(self, test_db, sample_agent, sample_knowledge_nodes, sample_transfers):
        """测试学习进度追踪"""
        progress = LearningTrackingService.track_learning_progress(
            db=test_db,
            agent_id=sample_agent.agent_id,
            period_days=30
        )

        # 验证进度报告结构
        assert "agent_id" in progress
        assert "period_days" in progress
        assert "has_activity" in progress

        if progress["has_activity"]:
            assert "knowledge_growth" in progress
            assert "epiplexity_progress" in progress
            assert "learning_sessions" in progress
            assert "knowledge_transfer" in progress

    def test_learning_speed_calculation(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试学习速度计算"""
        speed = LearningTrackingService.calculate_learning_speed(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 验证速度报告结构
        assert "agent_id" in speed
        assert "has_data" in speed

    def test_learning_pattern_identification(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试学习模式识别"""
        patterns = LearningTrackingService.identify_learning_patterns(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        # 验证模式报告结构
        assert "agent_id" in patterns
        assert "has_patterns" in patterns


class TestCompleteWorkflow:
    """测试完整工作流程"""

    def test_agent_learning_and_growth_workflow(self, test_db, sample_agent, sample_knowledge_nodes, sample_transfers):
        """
        测试Agent学习和成长完整工作流程

        流程:
        1. 计算当前知识价值
        2. 评估学习能力
        3. 推荐合适任务
        4. 规划学习路径
        5. 追踪学习进度
        6. 计算知识价值收益
        7. 更新评分和ROI
        """
        agent_id = sample_agent.agent_id

        # 1. 计算知识价值
        knowledge_value = SurvivalService.calculate_knowledge_value(
            db=test_db,
            agent_id=agent_id
        )
        assert knowledge_value > 0

        # 2. 评估学习能力
        learning_capacity = TaskRecommendationService.calculate_agent_learning_capacity(
            db=test_db,
            agent_id=agent_id
        )
        assert 0.0 <= learning_capacity <= 1.0

        # 3. 任务匹配
        match_score, details = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=learning_capacity,
            task_epiplexity=learning_capacity + 0.1,
            agent_knowledge=sample_knowledge_nodes,
            task_requirements=None
        )
        assert match_score > 0

        # 4. 规划学习路径
        learning_path = LearningPathService.plan_learning_path(
            db=test_db,
            agent_id=agent_id,
            max_steps=3
        )
        assert len(learning_path["learning_path"]) > 0

        # 5. 追踪学习进度
        progress = LearningTrackingService.track_learning_progress(
            db=test_db,
            agent_id=agent_id,
            period_days=30
        )
        assert progress["has_activity"] == True

        # 6. 计算知识价值收益
        kv_income = FinancialService.calculate_knowledge_value_income(
            db=test_db,
            agent_id=agent_id,
            period_days=30
        )
        assert kv_income["total_knowledge_income"] > 0

        # 7. 计算总收入和ROI
        total_income = FinancialService.calculate_task_income(
            base_reward=10000,
            quality_rating=4.5,
            is_innovative=True,
            knowledge_value_income=kv_income["total_knowledge_income"]
        )

        cost = 5000
        roi = total_income["total_income"] / cost
        assert roi > 1.0  # 应该盈利

    def test_knowledge_value_impact_on_survival(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试知识价值对生存评分的影响"""
        # 场景1: 无知识价值
        score_no_kv = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.7,
            efficiency_score=0.6,
            innovation_score=0.5,
            collaboration_score=0.4,
            knowledge_value=0.0
        )

        # 场景2: 有知识价值
        knowledge_value = SurvivalService.calculate_knowledge_value(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        score_with_kv = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.7,
            efficiency_score=0.6,
            innovation_score=0.5,
            collaboration_score=0.4,
            knowledge_value=knowledge_value
        )

        # 验证知识价值提升了评分
        assert score_with_kv > score_no_kv

        # 验证提升幅度显著（25%权重）
        improvement = score_with_kv - score_no_kv
        assert improvement > 10  # 应该有明显提升


class TestPerformanceBenchmarks:
    """测试性能基准"""

    def test_knowledge_value_calculation_performance(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试知识价值计算性能"""
        import time

        start = time.time()
        for _ in range(10):
            SurvivalService.calculate_knowledge_value(
                db=test_db,
                agent_id=sample_agent.agent_id
            )
        end = time.time()

        avg_time = (end - start) / 10
        assert avg_time < 0.1  # 平均每次应该小于100ms

    def test_task_recommendation_performance(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试任务推荐性能"""
        import time

        capacity = TaskRecommendationService.calculate_agent_learning_capacity(
            db=test_db,
            agent_id=sample_agent.agent_id
        )

        start = time.time()
        for _ in range(10):
            TaskRecommendationService.calculate_task_match_score(
                agent_capacity=capacity,
                task_epiplexity=capacity,
                agent_knowledge=sample_knowledge_nodes,
                task_requirements=None
            )
        end = time.time()

        avg_time = (end - start) / 10
        assert avg_time < 0.05  # 平均每次应该小于50ms

    def test_learning_path_planning_performance(self, test_db, sample_agent, sample_knowledge_nodes):
        """测试学习路径规划性能"""
        import time

        start = time.time()
        for _ in range(5):
            LearningPathService.plan_learning_path(
                db=test_db,
                agent_id=sample_agent.agent_id,
                max_steps=5
            )
        end = time.time()

        avg_time = (end - start) / 5
        assert avg_time < 0.2  # 平均每次应该小于200ms


class TestDataConsistency:
    """测试数据一致性"""

    def test_weight_consistency(self):
        """测试权重一致性"""
        # 验证评分权重总和为1
        survival_weights = SurvivalService.WEIGHTS
        total = sum(survival_weights.values())
        assert abs(total - 1.0) < 0.001

        # 验证推荐权重总和为1
        rec_config = TaskRecommendationService.RECOMMENDATION_CONFIG
        rec_total = (
            rec_config["diversity_weight"] +
            rec_config["learning_value_weight"] +
            rec_config["skill_match_weight"]
        )
        assert abs(rec_total - 1.0) < 0.001

    def test_config_consistency(self):
        """测试配置一致性"""
        # 验证学习路径配置
        path_config = LearningPathService.PATH_CONFIG
        assert path_config["mastery_threshold"] >= path_config["prerequisite_threshold"]
        assert 0 < path_config["difficulty_increment"] <= 0.5

        # 验证追踪配置
        tracking_config = LearningTrackingService.TRACKING_CONFIG
        assert tracking_config["history_days"] > 0
        assert tracking_config["min_sessions"] > 0
        assert 0 < tracking_config["speed_baseline"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
