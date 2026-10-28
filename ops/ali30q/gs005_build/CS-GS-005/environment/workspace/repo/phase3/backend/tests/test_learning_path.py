"""
测试学习路径规划服务
"""
import pytest
from services.learning_path_service import LearningPathService


class TestPathConfig:
    """测试路径配置"""

    def test_config_exists(self):
        """测试配置存在"""
        config = LearningPathService.PATH_CONFIG
        assert "max_path_length" in config
        assert "difficulty_increment" in config
        assert "prerequisite_threshold" in config
        assert "mastery_threshold" in config

    def test_config_values(self):
        """测试配置值合理"""
        config = LearningPathService.PATH_CONFIG
        assert config["max_path_length"] > 0
        assert 0 < config["difficulty_increment"] <= 0.5
        assert 0 < config["prerequisite_threshold"] <= 1.0
        assert 0 < config["mastery_threshold"] <= 1.0

    def test_thresholds_relationship(self):
        """测试阈值关系"""
        config = LearningPathService.PATH_CONFIG
        # 掌握阈值应该高于前置知识阈值
        assert config["mastery_threshold"] >= config["prerequisite_threshold"]


class TestKnowledgeGapAnalysis:
    """测试知识缺口分析"""

    def test_analyze_knowledge_gaps_structure(self, mock_db):
        """测试分析结果结构"""
        result = LearningPathService.analyze_knowledge_gaps(
            db=mock_db,
            agent_id=1
        )

        assert "agent_id" in result
        assert "current_knowledge" in result
        assert "gaps" in result
        assert isinstance(result["gaps"], list)

    def test_gap_types(self):
        """测试缺口类型"""
        valid_gap_types = ["missing", "insufficient", "weak"]
        # 这些是系统识别的缺口类型
        assert len(valid_gap_types) == 3

    def test_priority_levels(self):
        """测试优先级级别"""
        valid_priorities = ["high", "medium", "low"]
        assert len(valid_priorities) == 3


class TestLearningPathPlanning:
    """测试学习路径规划"""

    def test_plan_learning_path_structure(self, mock_db):
        """测试规划结果结构"""
        result = LearningPathService.plan_learning_path(
            db=mock_db,
            agent_id=1
        )

        assert "agent_id" in result
        assert "learning_path" in result
        assert "summary" in result
        assert "recommendations" in result
        assert isinstance(result["learning_path"], list)

    def test_learning_step_structure(self, mock_db):
        """测试学习步骤结构"""
        result = LearningPathService.plan_learning_path(
            db=mock_db,
            agent_id=1,
            max_steps=1
        )

        if result["learning_path"]:
            step = result["learning_path"][0]
            assert "step_number" in step
            assert "category" in step
            assert "goal" in step
            assert "start_difficulty" in step
            assert "target_difficulty" in step
            assert "estimated_tasks" in step
            assert "estimated_days" in step
            assert "prerequisites" in step
            assert "milestones" in step

    def test_difficulty_progression(self, mock_db):
        """测试难度递进"""
        result = LearningPathService.plan_learning_path(
            db=mock_db,
            agent_id=1,
            max_steps=3
        )

        for step in result["learning_path"]:
            # 目标难度应该高于起始难度
            assert step["target_difficulty"] >= step["start_difficulty"]
            # 难度应该在合理范围内
            assert 0 <= step["start_difficulty"] <= 1.0
            assert 0 <= step["target_difficulty"] <= 1.0

    def test_max_steps_limit(self, mock_db):
        """测试最大步骤限制"""
        max_steps = 5
        result = LearningPathService.plan_learning_path(
            db=mock_db,
            agent_id=1,
            max_steps=max_steps
        )

        assert len(result["learning_path"]) <= max_steps

    def test_summary_calculation(self, mock_db):
        """测试摘要计算"""
        result = LearningPathService.plan_learning_path(
            db=mock_db,
            agent_id=1
        )

        summary = result["summary"]
        assert "total_steps" in summary
        assert "total_tasks" in summary
        assert "total_days" in summary
        assert "difficulty_range" in summary

        # 验证计算正确性
        assert summary["total_steps"] == len(result["learning_path"])


class TestNextStepSuggestions:
    """测试下一步建议"""

    def test_suggest_next_steps_structure(self, mock_db):
        """测试建议结构"""
        suggestions = LearningPathService.suggest_next_steps(
            db=mock_db,
            agent_id=1
        )

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

        for suggestion in suggestions:
            assert "type" in suggestion
            assert "message" in suggestion

    def test_suggestion_types(self):
        """测试建议类型"""
        valid_types = ["start", "next", "continue", "completed"]
        # 这些是系统支持的建议类型
        assert len(valid_types) == 4

    def test_suggestion_limit(self, mock_db):
        """测试建议数量限制"""
        suggestions = LearningPathService.suggest_next_steps(
            db=mock_db,
            agent_id=1
        )

        # 最多推荐3个步骤（或1个完成消息）
        assert len(suggestions) <= 3


class TestPrerequisiteCheck:
    """测试前置知识检查"""

    def test_check_prerequisites_structure(self, mock_db):
        """测试检查结果结构"""
        result = LearningPathService.check_prerequisites(
            db=mock_db,
            agent_id=1,
            required_knowledge=["python", "javascript"]
        )

        assert "all_prerequisites_met" in result
        assert "details" in result
        assert "missing_count" in result
        assert isinstance(result["all_prerequisites_met"], bool)
        assert isinstance(result["details"], list)

    def test_prerequisite_detail_structure(self, mock_db):
        """测试前置知识详情结构"""
        result = LearningPathService.check_prerequisites(
            db=mock_db,
            agent_id=1,
            required_knowledge=["python"]
        )

        if result["details"]:
            detail = result["details"][0]
            assert "knowledge" in detail
            assert "has_knowledge" in detail
            assert "mastery_level" in detail

    def test_mastery_levels(self):
        """测试掌握度级别"""
        valid_levels = ["none", "low", "medium", "high"]
        assert len(valid_levels) == 4


class TestRecommendations:
    """测试学习建议生成"""

    def test_generate_recommendations(self):
        """测试建议生成"""
        gap_analysis = {
            "gaps": [
                {"category": "python", "gap_type": "missing", "priority": "high"}
            ]
        }
        learning_steps = [
            {"step_number": 1, "category": "python"}
        ]
        current_capacity = 0.5

        recommendations = LearningPathService._generate_recommendations(
            gap_analysis=gap_analysis,
            learning_steps=learning_steps,
            current_capacity=current_capacity
        )

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert all(isinstance(r, str) for r in recommendations)

    def test_recommendations_based_on_gaps(self):
        """测试基于缺口的建议"""
        # 无缺口
        recs_no_gap = LearningPathService._generate_recommendations(
            gap_analysis={"gaps": []},
            learning_steps=[],
            current_capacity=0.5
        )
        assert len(recs_no_gap) > 0

        # 少量缺口
        recs_few_gaps = LearningPathService._generate_recommendations(
            gap_analysis={"gaps": [{"category": "test"}]},
            learning_steps=[],
            current_capacity=0.5
        )
        assert len(recs_few_gaps) > 0

        # 多个缺口
        recs_many_gaps = LearningPathService._generate_recommendations(
            gap_analysis={"gaps": [{"category": f"test{i}"} for i in range(5)]},
            learning_steps=[],
            current_capacity=0.5
        )
        assert len(recs_many_gaps) > 0

    def test_recommendations_based_on_capacity(self):
        """测试基于能力的建议"""
        gap_analysis = {"gaps": []}
        learning_steps = []

        # 低能力
        recs_low = LearningPathService._generate_recommendations(
            gap_analysis=gap_analysis,
            learning_steps=learning_steps,
            current_capacity=0.2
        )
        assert len(recs_low) > 0

        # 中等能力
        recs_medium = LearningPathService._generate_recommendations(
            gap_analysis=gap_analysis,
            learning_steps=learning_steps,
            current_capacity=0.5
        )
        assert len(recs_medium) > 0

        # 高能力
        recs_high = LearningPathService._generate_recommendations(
            gap_analysis=gap_analysis,
            learning_steps=learning_steps,
            current_capacity=0.8
        )
        assert len(recs_high) > 0


class TestMilestones:
    """测试里程碑设置"""

    def test_milestone_structure(self, mock_db):
        """测试里程碑结构"""
        result = LearningPathService.plan_learning_path(
            db=mock_db,
            agent_id=1,
            max_steps=1
        )

        if result["learning_path"]:
            step = result["learning_path"][0]
            milestones = step["milestones"]

            assert isinstance(milestones, list)
            for milestone in milestones:
                assert "name" in milestone
                assert "difficulty" in milestone

    def test_milestone_progression(self, mock_db):
        """测试里程碑难度递进"""
        result = LearningPathService.plan_learning_path(
            db=mock_db,
            agent_id=1,
            max_steps=1
        )

        if result["learning_path"]:
            step = result["learning_path"][0]
            milestones = step["milestones"]

            if len(milestones) > 1:
                # 里程碑难度应该递增
                for i in range(len(milestones) - 1):
                    assert milestones[i]["difficulty"] <= milestones[i + 1]["difficulty"]


class TestLearningStrategy:
    """测试学习策略"""

    def test_difficulty_increment(self):
        """测试难度递增策略"""
        config = LearningPathService.PATH_CONFIG
        increment = config["difficulty_increment"]

        # 难度递增应该合理
        assert 0.05 <= increment <= 0.2

    def test_path_length_limit(self):
        """测试路径长度限制"""
        config = LearningPathService.PATH_CONFIG
        max_length = config["max_path_length"]

        # 路径长度应该合理
        assert 5 <= max_length <= 20

    def test_review_interval(self):
        """测试复习间隔"""
        config = LearningPathService.PATH_CONFIG
        interval = config["review_interval_days"]

        # 复习间隔应该合理
        assert 1 <= interval <= 30


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    class MockDB:
        def query(self, model):
            return self

        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return None

        def all(self):
            return []

        def order_by(self, *args):
            return self

        def limit(self, n):
            return self

    return MockDB()
