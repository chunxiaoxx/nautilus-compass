"""
测试基于Epiplexity的任务推荐
"""
import pytest
from services.task_recommendation_service import TaskRecommendationService


class TestRecommendationConfig:
    """测试推荐配置"""

    def test_config_exists(self):
        """测试配置存在"""
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        assert "learning_zone_range" in config
        assert "min_match_score" in config
        assert "max_recommendations" in config

    def test_config_values(self):
        """测试配置值合理"""
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        assert 0 < config["learning_zone_range"] <= 0.5
        assert 0 < config["min_match_score"] <= 1.0
        assert config["max_recommendations"] > 0

    def test_weights_sum_to_one(self):
        """测试权重总和为1"""
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        total = (
            config["diversity_weight"] +
            config["learning_value_weight"] +
            config["skill_match_weight"]
        )
        assert abs(total - 1.0) < 0.001


class TestLearningCapacity:
    """测试学习能力计算"""

    def test_calculate_agent_learning_capacity_default(self, mock_db):
        """测试默认学习能力"""
        capacity = TaskRecommendationService.calculate_agent_learning_capacity(
            db=mock_db,
            agent_id=999  # 不存在的Agent
        )
        assert capacity == 0.5  # 默认中等能力

    def test_learning_capacity_range(self, mock_db):
        """测试学习能力范围"""
        capacity = TaskRecommendationService.calculate_agent_learning_capacity(
            db=mock_db,
            agent_id=1
        )
        assert 0.0 <= capacity <= 1.0


class TestTaskMatchScore:
    """测试任务匹配分数"""

    def test_optimal_zone_match(self):
        """测试最佳学习区间匹配"""
        agent_capacity = 0.5
        task_epiplexity = 0.5  # 完全匹配

        match_score, details = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=agent_capacity,
            task_epiplexity=task_epiplexity,
            agent_knowledge=[],
            task_requirements=None
        )

        assert match_score > 0.5
        assert details["in_optimal_zone"] == True
        assert details["difficulty_level"] == "optimal"

    def test_easy_task_match(self):
        """测试简单任务匹配"""
        agent_capacity = 0.7
        task_epiplexity = 0.3  # 太简单

        match_score, details = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=agent_capacity,
            task_epiplexity=task_epiplexity,
            agent_knowledge=[],
            task_requirements=None
        )

        assert details["difficulty_level"] == "easy"
        assert details["in_optimal_zone"] == False

    def test_challenging_task_match(self):
        """测试挑战性任务匹配"""
        agent_capacity = 0.3
        task_epiplexity = 0.8  # 太难

        match_score, details = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=agent_capacity,
            task_epiplexity=task_epiplexity,
            agent_knowledge=[],
            task_requirements=None
        )

        assert details["difficulty_level"] == "challenging"
        assert details["in_optimal_zone"] == False

    def test_match_score_range(self):
        """测试匹配分数范围"""
        match_score, _ = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=0.5,
            task_epiplexity=0.6,
            agent_knowledge=[],
            task_requirements=None
        )

        assert 0.0 <= match_score <= 1.0

    def test_zone_score_calculation(self):
        """测试学习区间分数计算"""
        agent_capacity = 0.5
        config = TaskRecommendationService.RECOMMENDATION_CONFIG

        # 测试不同难度的任务
        test_cases = [
            (0.5, True),   # 完全匹配
            (0.6, True),   # 在区间内
            (0.4, True),   # 在区间内
            (0.2, False),  # 太简单
            (0.9, False),  # 太难
        ]

        for task_epiplexity, should_be_in_zone in test_cases:
            _, details = TaskRecommendationService.calculate_task_match_score(
                agent_capacity=agent_capacity,
                task_epiplexity=task_epiplexity,
                agent_knowledge=[],
                task_requirements=None
            )
            assert details["in_optimal_zone"] == should_be_in_zone


class TestRecommendationExplanation:
    """测试推荐解释"""

    def test_explain_optimal_task(self):
        """测试最佳任务解释"""
        explanation = TaskRecommendationService.explain_recommendation(
            agent_capacity=0.5,
            task_epiplexity=0.5,
            match_score=0.8,
            details={
                "difficulty_level": "optimal",
                "in_optimal_zone": True,
                "skill_match": 0.7
            }
        )

        assert "适合" in explanation or "optimal" in explanation.lower()
        assert len(explanation) > 0

    def test_explain_easy_task(self):
        """测试简单任务解释"""
        explanation = TaskRecommendationService.explain_recommendation(
            agent_capacity=0.7,
            task_epiplexity=0.3,
            match_score=0.6,
            details={
                "difficulty_level": "easy",
                "in_optimal_zone": False,
                "skill_match": 0.8
            }
        )

        assert "简单" in explanation or "easy" in explanation.lower()

    def test_explain_challenging_task(self):
        """测试挑战性任务解释"""
        explanation = TaskRecommendationService.explain_recommendation(
            agent_capacity=0.3,
            task_epiplexity=0.7,
            match_score=0.5,
            details={
                "difficulty_level": "challenging",
                "in_optimal_zone": False,
                "skill_match": 0.3
            }
        )

        assert "挑战" in explanation or "challenging" in explanation.lower()

    def test_explanation_includes_skill_match(self):
        """测试解释包含技能匹配信息"""
        # 高技能匹配
        explanation_high = TaskRecommendationService.explain_recommendation(
            agent_capacity=0.5,
            task_epiplexity=0.5,
            match_score=0.8,
            details={
                "difficulty_level": "optimal",
                "in_optimal_zone": True,
                "skill_match": 0.9
            }
        )
        assert "技能" in explanation_high or "skill" in explanation_high.lower()

        # 低技能匹配
        explanation_low = TaskRecommendationService.explain_recommendation(
            agent_capacity=0.5,
            task_epiplexity=0.5,
            match_score=0.6,
            details={
                "difficulty_level": "optimal",
                "in_optimal_zone": True,
                "skill_match": 0.2
            }
        )
        assert "新" in explanation_low or "new" in explanation_low.lower()


class TestLearningZone:
    """测试学习区间理论 (Zone of Proximal Development)"""

    def test_zpd_concept(self):
        """测试最近发展区概念"""
        agent_capacity = 0.5
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        zone_range = config["learning_zone_range"]

        # 最佳学习区间
        optimal_min = agent_capacity - zone_range
        optimal_max = agent_capacity + zone_range

        # 测试区间内的任务
        for epiplexity in [0.35, 0.5, 0.65]:
            match_score, details = TaskRecommendationService.calculate_task_match_score(
                agent_capacity=agent_capacity,
                task_epiplexity=epiplexity,
                agent_knowledge=[],
                task_requirements=None
            )
            assert details["in_optimal_zone"] == True
            assert details["zone_score"] == 1.0

    def test_zpd_boundaries(self):
        """测试学习区间边界"""
        agent_capacity = 0.5
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        zone_range = config["learning_zone_range"]

        # 边界值
        optimal_min = agent_capacity - zone_range
        optimal_max = agent_capacity + zone_range

        # 测试边界
        _, details_min = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=agent_capacity,
            task_epiplexity=optimal_min,
            agent_knowledge=[],
            task_requirements=None
        )
        assert details_min["in_optimal_zone"] == True

        _, details_max = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=agent_capacity,
            task_epiplexity=optimal_max,
            agent_knowledge=[],
            task_requirements=None
        )
        assert details_max["in_optimal_zone"] == True

    def test_zpd_outside_zone(self):
        """测试区间外的任务"""
        agent_capacity = 0.5
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        zone_range = config["learning_zone_range"]

        # 太简单
        _, details_easy = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=agent_capacity,
            task_epiplexity=agent_capacity - zone_range - 0.1,
            agent_knowledge=[],
            task_requirements=None
        )
        assert details_easy["in_optimal_zone"] == False
        assert details_easy["zone_score"] < 1.0

        # 太难
        _, details_hard = TaskRecommendationService.calculate_task_match_score(
            agent_capacity=agent_capacity,
            task_epiplexity=agent_capacity + zone_range + 0.1,
            agent_knowledge=[],
            task_requirements=None
        )
        assert details_hard["in_optimal_zone"] == False
        assert details_hard["zone_score"] < 1.0


class TestRecommendationStrategy:
    """测试推荐策略"""

    def test_min_match_score_filter(self):
        """测试最低匹配分数过滤"""
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        min_score = config["min_match_score"]

        # 低分任务应该被过滤
        assert min_score > 0
        assert min_score <= 1.0

    def test_recommendation_limit(self):
        """测试推荐数量限制"""
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        max_recs = config["max_recommendations"]

        assert max_recs > 0
        assert max_recs <= 50  # 合理的上限

    def test_diversity_consideration(self):
        """测试多样性考虑"""
        config = TaskRecommendationService.RECOMMENDATION_CONFIG
        diversity_weight = config["diversity_weight"]

        # 多样性应该有一定权重
        assert diversity_weight > 0
        assert diversity_weight < 1.0


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

    return MockDB()
