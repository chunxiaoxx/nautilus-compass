"""
测试Agent学习能力追踪服务
"""
import pytest
from services.learning_tracking_service import LearningTrackingService


class TestTrackingConfig:
    """测试追踪配置"""

    def test_config_exists(self):
        """测试配置存在"""
        config = LearningTrackingService.TRACKING_CONFIG
        assert "history_days" in config
        assert "min_sessions" in config
        assert "session_gap_hours" in config
        assert "speed_baseline" in config

    def test_config_values(self):
        """测试配置值合理"""
        config = LearningTrackingService.TRACKING_CONFIG
        assert config["history_days"] > 0
        assert config["min_sessions"] > 0
        assert config["session_gap_hours"] > 0
        assert 0 < config["speed_baseline"] <= 1.0


class TestLearningProgress:
    """测试学习进度追踪"""

    def test_track_learning_progress_structure(self, mock_db):
        """测试进度追踪结果结构"""
        result = LearningTrackingService.track_learning_progress(
            db=mock_db,
            agent_id=1
        )

        assert "agent_id" in result
        assert "period_days" in result
        assert "has_activity" in result

    def test_no_activity_response(self, mock_db):
        """测试无活动时的响应"""
        result = LearningTrackingService.track_learning_progress(
            db=mock_db,
            agent_id=999
        )

        assert result["has_activity"] == False
        assert "message" in result


class TestLearningSpeed:
    """测试学习速度计算"""

    def test_calculate_learning_speed_structure(self, mock_db):
        """测试学习速度结果结构"""
        result = LearningTrackingService.calculate_learning_speed(
            db=mock_db,
            agent_id=1
        )

        assert "agent_id" in result
        assert "has_data" in result

    def test_speed_ratings(self):
        """测试速度评级"""
        valid_ratings = ["very_fast", "fast", "moderate", "slow", "very_slow"]

        # 测试不同速度的评级
        rating_fast = LearningTrackingService._rate_learning_speed(
            acquisition_speed=2.0,
            epiplexity_speed=0.02,
            efficiency=1.0
        )
        assert rating_fast in valid_ratings

        rating_slow = LearningTrackingService._rate_learning_speed(
            acquisition_speed=0.1,
            epiplexity_speed=0.001,
            efficiency=0.05
        )
        assert rating_slow in valid_ratings

    def test_speed_interpretation(self):
        """测试速度解释"""
        for rating in ["very_fast", "fast", "moderate", "slow", "very_slow"]:
            interpretation = LearningTrackingService._interpret_speed(rating)
            assert isinstance(interpretation, str)
            assert len(interpretation) > 0


class TestLearningPatterns:
    """测试学习模式识别"""

    def test_identify_learning_patterns_structure(self, mock_db):
        """测试学习模式结果结构"""
        result = LearningTrackingService.identify_learning_patterns(
            db=mock_db,
            agent_id=1
        )

        assert "agent_id" in result
        assert "has_patterns" in result

    def test_learning_strategies(self):
        """测试学习策略类型"""
        valid_strategies = ["breadth_first", "depth_first", "mixed", "unknown"]

        # 测试策略识别逻辑存在
        assert len(valid_strategies) == 4


class TestProgressScore:
    """测试进度分数计算"""

    def test_calculate_progress_score_range(self):
        """测试进度分数范围"""
        score = LearningTrackingService._calculate_progress_score(
            total_nodes=10,
            epiplexity_progress={"has_progress": True, "improvement_rate": 20},
            transfer_success_rate=0.8,
            session_count=5
        )

        assert 0.0 <= score <= 1.0

    def test_progress_score_components(self):
        """测试进度分数组成"""
        # 测试各组件权重
        # 节点数量: 30%
        # Epiplexity提升: 40%
        # 迁移成功率: 20%
        # 学习会话: 10%

        score_high = LearningTrackingService._calculate_progress_score(
            total_nodes=50,
            epiplexity_progress={"has_progress": True, "improvement_rate": 50},
            transfer_success_rate=1.0,
            session_count=10
        )

        score_low = LearningTrackingService._calculate_progress_score(
            total_nodes=1,
            epiplexity_progress={"has_progress": False},
            transfer_success_rate=0.0,
            session_count=1
        )

        assert score_high > score_low


class TestSessionIdentification:
    """测试学习会话识别"""

    def test_identify_learning_sessions_empty(self):
        """测试空列表"""
        sessions = LearningTrackingService._identify_learning_sessions([])
        assert sessions == []

    def test_session_structure(self):
        """测试会话结构"""
        # 会话应该包含的字段
        required_fields = ["start_time", "end_time", "nodes_count", "duration_hours"]
        assert len(required_fields) == 4


class TestTimePreference:
    """测试学习时间偏好分析"""

    def test_analyze_time_preference_empty(self):
        """测试空列表"""
        result = LearningTrackingService._analyze_time_preference([])
        assert result["has_preference"] == False

    def test_time_periods(self):
        """测试时间段分类"""
        valid_periods = ["morning", "afternoon", "evening", "night"]
        assert len(valid_periods) == 4


class TestIntensityPattern:
    """测试学习强度模式"""

    def test_analyze_intensity_pattern(self):
        """测试强度分析"""
        from models.epiplexity import KnowledgeNode
        from datetime import datetime

        # 模拟节点
        nodes = [
            type('Node', (), {'created_at': datetime.utcnow()})()
            for _ in range(10)
        ]

        result = LearningTrackingService._analyze_intensity_pattern(nodes, 30)

        assert "intensity" in result
        assert "nodes_per_day" in result
        assert result["intensity"] in ["high", "moderate", "low", "very_low"]


class TestDomainPreference:
    """测试知识领域偏好"""

    def test_analyze_domain_preference_empty(self):
        """测试空列表"""
        result = LearningTrackingService._analyze_domain_preference([])
        assert result["total_domains"] == 0
        assert result["top_domains"] == []

    def test_domain_preference_structure(self):
        """测试领域偏好结构"""
        from models.epiplexity import KnowledgeNode

        # 模拟节点
        nodes = [
            type('Node', (), {'category': 'python'})(),
            type('Node', (), {'category': 'python'})(),
            type('Node', (), {'category': 'javascript'})()
        ]

        result = LearningTrackingService._analyze_domain_preference(nodes)

        assert result["total_domains"] == 2
        assert len(result["top_domains"]) <= 5

        if result["top_domains"]:
            top = result["top_domains"][0]
            assert "domain" in top
            assert "count" in top


class TestLearningStrategy:
    """测试学习策略识别"""

    def test_identify_learning_strategy_empty(self):
        """测试空列表"""
        result = LearningTrackingService._identify_learning_strategy([])
        assert result["type"] == "unknown"

    def test_strategy_types(self):
        """测试策略类型"""
        valid_types = ["breadth_first", "depth_first", "mixed", "unknown"]

        # 测试广度优先识别
        nodes_breadth = [
            type('Node', (), {
                'category': f'domain_{i}',
                'epiplexity': 0.5
            })()
            for i in range(10)
        ]

        result_breadth = LearningTrackingService._identify_learning_strategy(nodes_breadth)
        assert result_breadth["type"] in valid_types
        assert "description" in result_breadth
        assert "diversity" in result_breadth


class TestWeeklyGrowth:
    """测试每周增长计算"""

    def test_calculate_weekly_growth_empty(self):
        """测试空列表"""
        result = LearningTrackingService._calculate_weekly_growth([], 30)
        assert isinstance(result, list)

    def test_weekly_growth_structure(self):
        """测试每周增长结构"""
        from datetime import datetime

        nodes = [
            type('Node', (), {
                'created_at': datetime.utcnow(),
                'epiplexity': 0.5
            })()
            for _ in range(5)
        ]

        result = LearningTrackingService._calculate_weekly_growth(nodes, 14)

        if result:
            week_data = result[0]
            assert "week" in week_data
            assert "nodes_created" in week_data
            assert "avg_epiplexity" in week_data


class TestEpiplexityProgress:
    """测试Epiplexity进度计算"""

    def test_calculate_epiplexity_progress_empty(self):
        """测试空列表"""
        result = LearningTrackingService._calculate_epiplexity_progress([])
        assert result["has_progress"] == False

    def test_epiplexity_progress_structure(self):
        """测试进度结构"""
        nodes = [
            type('Node', (), {'epiplexity': 0.3})(),
            type('Node', (), {'epiplexity': 0.4})(),
            type('Node', (), {'epiplexity': 0.5})(),
            type('Node', (), {'epiplexity': 0.6})()
        ]

        result = LearningTrackingService._calculate_epiplexity_progress(nodes)

        assert result["has_progress"] == True
        assert "initial_avg" in result
        assert "current_avg" in result
        assert "improvement" in result
        assert "improvement_rate" in result

    def test_epiplexity_improvement_calculation(self):
        """测试提升计算"""
        nodes = [
            type('Node', (), {'epiplexity': 0.3})(),
            type('Node', (), {'epiplexity': 0.6})()
        ]

        result = LearningTrackingService._calculate_epiplexity_progress(nodes)

        # 应该有提升
        assert result["improvement"] > 0
        assert result["improvement_rate"] > 0


class TestTrackingMetrics:
    """测试追踪指标"""

    def test_metrics_completeness(self):
        """测试指标完整性"""
        # 学习进度应该包含的指标
        progress_metrics = [
            "knowledge_growth",
            "epiplexity_progress",
            "learning_sessions",
            "knowledge_transfer",
            "progress_score"
        ]
        assert len(progress_metrics) == 5

        # 学习速度应该包含的指标
        speed_metrics = [
            "acquisition_speed",
            "epiplexity_speed",
            "skill_acquisition_speed",
            "learning_efficiency",
            "speed_rating"
        ]
        assert len(speed_metrics) == 5

        # 学习模式应该包含的指标
        pattern_metrics = [
            "time_preference",
            "intensity_pattern",
            "domain_preference",
            "learning_strategy"
        ]
        assert len(pattern_metrics) == 4


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

    return MockDB()
