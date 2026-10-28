"""
测试知识价值集成到评分系统（简化版）
避免复杂的数据库模型依赖
"""
import pytest
from services.survival_service import SurvivalService


class TestKnowledgeValueWeights:
    """测试知识价值权重配置"""

    def test_weights_sum_to_one(self):
        """测试权重总和为1"""
        weights = SurvivalService.WEIGHTS
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001, f"权重总和应为1.0，实际为{total}"

    def test_knowledge_weight_is_25_percent(self):
        """测试知识价值权重为25%"""
        assert SurvivalService.WEIGHTS["knowledge"] == 0.25

    def test_all_weights_present(self):
        """测试所有权重都存在"""
        required_weights = ["task", "quality", "efficiency", "innovation", "collaboration", "knowledge"]
        for weight in required_weights:
            assert weight in SurvivalService.WEIGHTS

    def test_weight_values(self):
        """测试各权重值"""
        assert SurvivalService.WEIGHTS["task"] == 0.25
        assert SurvivalService.WEIGHTS["quality"] == 0.20
        assert SurvivalService.WEIGHTS["efficiency"] == 0.15
        assert SurvivalService.WEIGHTS["innovation"] == 0.10
        assert SurvivalService.WEIGHTS["collaboration"] == 0.05
        assert SurvivalService.WEIGHTS["knowledge"] == 0.25


class TestTotalScoreCalculation:
    """测试总分计算"""

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
        # task: 1000 * 0.25 = 250
        # quality: 80 * 0.20 = 16
        # efficiency: 70 * 0.15 = 10.5
        # innovation: 60 * 0.10 = 6
        # collaboration: 50 * 0.05 = 2.5
        # knowledge: 90 * 0.25 = 22.5
        # Total: 307.5 -> 307

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
        # task: 1000 * 0.25 = 250
        # quality: 80 * 0.20 = 16
        # efficiency: 70 * 0.15 = 10.5
        # innovation: 60 * 0.10 = 6
        # collaboration: 50 * 0.05 = 2.5
        # Total: 285

        assert score == 285

    def test_knowledge_value_impact(self):
        """测试知识价值对总分的影响"""
        base_params = {
            "task_score": 1000,
            "quality_score": 0.8,
            "efficiency_score": 0.7,
            "innovation_score": 0.6,
            "collaboration_score": 0.5
        }

        # 不同的知识价值
        score_zero = SurvivalService.calculate_total_score(**base_params, knowledge_value=0.0)
        score_half = SurvivalService.calculate_total_score(**base_params, knowledge_value=0.5)
        score_full = SurvivalService.calculate_total_score(**base_params, knowledge_value=1.0)

        # 验证递增关系
        assert score_zero < score_half < score_full

        # 验证差异（25%权重）
        diff_half = score_half - score_zero
        diff_full = score_full - score_zero

        # 0.5知识价值应该贡献50*0.25=12.5分
        assert diff_half == 12

        # 1.0知识价值应该贡献100*0.25=25分
        assert diff_full == 25

    def test_zero_knowledge_value(self):
        """测试零知识价值"""
        score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.8,
            efficiency_score=0.7,
            innovation_score=0.6,
            collaboration_score=0.5,
            knowledge_value=0.0
        )

        # 应该等于不传knowledge_value的结果
        score_no_knowledge = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.8,
            efficiency_score=0.7,
            innovation_score=0.6,
            collaboration_score=0.5
        )

        assert score == score_no_knowledge

    def test_max_knowledge_value(self):
        """测试最大知识价值"""
        score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=1.0,
            efficiency_score=1.0,
            innovation_score=1.0,
            collaboration_score=1.0,
            knowledge_value=1.0
        )

        # 所有维度满分
        # task: 1000 * 0.25 = 250
        # quality: 100 * 0.20 = 20
        # efficiency: 100 * 0.15 = 15
        # innovation: 100 * 0.10 = 10
        # collaboration: 100 * 0.05 = 5
        # knowledge: 100 * 0.25 = 25
        # Total: 325

        assert score == 325

    def test_weight_distribution(self):
        """测试权重分布的合理性"""
        # 知识价值和任务积分权重相同（都是25%）
        assert SurvivalService.WEIGHTS["knowledge"] == SurvivalService.WEIGHTS["task"]

        # 知识价值权重大于其他单项
        assert SurvivalService.WEIGHTS["knowledge"] > SurvivalService.WEIGHTS["quality"]
        assert SurvivalService.WEIGHTS["knowledge"] > SurvivalService.WEIGHTS["efficiency"]
        assert SurvivalService.WEIGHTS["knowledge"] > SurvivalService.WEIGHTS["innovation"]
        assert SurvivalService.WEIGHTS["knowledge"] > SurvivalService.WEIGHTS["collaboration"]


class TestScoreComponents:
    """测试评分组件"""

    def test_task_score_component(self):
        """测试任务积分组件"""
        score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.0,
            efficiency_score=0.0,
            innovation_score=0.0,
            collaboration_score=0.0,
            knowledge_value=0.0
        )

        # 只有任务积分: 1000 * 0.25 = 250
        assert score == 250

    def test_knowledge_component_only(self):
        """测试仅知识价值组件"""
        score = SurvivalService.calculate_total_score(
            task_score=0,
            quality_score=0.0,
            efficiency_score=0.0,
            innovation_score=0.0,
            collaboration_score=0.0,
            knowledge_value=1.0
        )

        # 只有知识价值: 100 * 0.25 = 25
        assert score == 25

    def test_balanced_score(self):
        """测试平衡评分"""
        score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.5,
            efficiency_score=0.5,
            innovation_score=0.5,
            collaboration_score=0.5,
            knowledge_value=0.5
        )

        # task: 1000 * 0.25 = 250
        # quality: 50 * 0.20 = 10
        # efficiency: 50 * 0.15 = 7.5
        # innovation: 50 * 0.10 = 5
        # collaboration: 50 * 0.05 = 2.5
        # knowledge: 50 * 0.25 = 12.5
        # Total: 287.5 -> 287

        assert score == 287


class TestROICalculation:
    """测试ROI计算（保持不变）"""

    def test_calculate_roi_normal(self):
        """测试正常ROI计算"""
        roi = SurvivalService.calculate_roi(total_income=1000, total_cost=500)
        assert roi == 2.0

    def test_calculate_roi_zero_cost(self):
        """测试零成本ROI"""
        roi = SurvivalService.calculate_roi(total_income=1000, total_cost=0)
        assert roi == float('inf')

    def test_calculate_roi_zero_income_zero_cost(self):
        """测试零收入零成本"""
        roi = SurvivalService.calculate_roi(total_income=0, total_cost=0)
        assert roi == 0.0

    def test_calculate_roi_loss(self):
        """测试亏损ROI"""
        roi = SurvivalService.calculate_roi(total_income=500, total_cost=1000)
        assert roi == 0.5
