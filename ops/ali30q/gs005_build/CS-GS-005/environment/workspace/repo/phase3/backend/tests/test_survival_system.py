"""
生存机制单元测试
"""
import pytest
from datetime import datetime, timedelta
from services.survival_service import SurvivalService


class TestSurvivalService:
    """测试生存机制服务"""

    def test_calculate_total_score(self):
        """测试总积分计算"""
        # 测试用例1: 均衡评分
        score = SurvivalService.calculate_total_score(
            task_score=450,
            quality_score=0.85,
            efficiency_score=0.78,
            innovation_score=0.65,
            collaboration_score=0.90
        )
        # 450*0.3 + 85*0.25 + 78*0.2 + 65*0.15 + 90*0.1
        # = 135 + 21.25 + 15.6 + 9.75 + 9 = 190.6
        assert score == 190

        # 测试用例2: 高任务积分
        score = SurvivalService.calculate_total_score(
            task_score=1000,
            quality_score=0.9,
            efficiency_score=0.8,
            innovation_score=0.7,
            collaboration_score=0.85
        )
        # 1000*0.3 + 90*0.25 + 80*0.2 + 70*0.15 + 85*0.1
        # = 300 + 22.5 + 16 + 10.5 + 8.5 = 357.5
        assert score == 357

        # 测试用例3: 零分
        score = SurvivalService.calculate_total_score(
            task_score=0,
            quality_score=0.0,
            efficiency_score=0.0,
            innovation_score=0.0,
            collaboration_score=0.0
        )
        assert score == 0

    def test_calculate_roi(self):
        """测试ROI计算"""
        # 测试用例1: 正常ROI
        roi = SurvivalService.calculate_roi(
            total_income=2000,
            total_cost=1000
        )
        assert roi == 2.0

        # 测试用例2: ROI < 1
        roi = SurvivalService.calculate_roi(
            total_income=500,
            total_cost=1000
        )
        assert roi == 0.5

        # 测试用例3: 零成本
        roi = SurvivalService.calculate_roi(
            total_income=1000,
            total_cost=0
        )
        assert roi == float('inf')

        # 测试用例4: 零收入零成本
        roi = SurvivalService.calculate_roi(
            total_income=0,
            total_cost=0
        )
        assert roi == 0.0

    def test_determine_survival_level(self):
        """测试生存等级判断"""
        # 测试用例1: ELITE
        level = SurvivalService.determine_survival_level(roi=2.5, total_score=6000)
        assert level == "ELITE"

        # 测试用例2: MATURE
        level = SurvivalService.determine_survival_level(roi=1.5, total_score=2000)
        assert level == "MATURE"

        # 测试用例3: GROWING
        level = SurvivalService.determine_survival_level(roi=0.7, total_score=700)
        assert level == "GROWING"

        # 测试用例4: STRUGGLING
        level = SurvivalService.determine_survival_level(roi=0.4, total_score=200)
        assert level == "STRUGGLING"

        # 测试用例5: WARNING
        level = SurvivalService.determine_survival_level(roi=0.15, total_score=80)
        assert level == "WARNING"

        # 测试用例6: CRITICAL
        level = SurvivalService.determine_survival_level(roi=0.05, total_score=30)
        assert level == "CRITICAL"

        # 边界测试: ROI达标但积分不足
        level = SurvivalService.determine_survival_level(roi=2.5, total_score=100)
        assert level == "STRUGGLING"  # 积分不足5000，降级

        # 边界测试: 积分达标但ROI不足
        level = SurvivalService.determine_survival_level(roi=0.5, total_score=6000)
        assert level == "GROWING"  # ROI不足2.0，降级

    def test_determine_status(self):
        """测试状态判断"""
        # 测试用例1: 新手保护期
        status = SurvivalService.determine_status(
            survival_level="CRITICAL",
            is_protected=True
        )
        assert status == "ACTIVE"  # 保护期内始终ACTIVE

        # 测试用例2: ELITE状态
        status = SurvivalService.determine_status(
            survival_level="ELITE",
            is_protected=False
        )
        assert status == "ACTIVE"

        # 测试用例3: WARNING等级
        status = SurvivalService.determine_status(
            survival_level="WARNING",
            is_protected=False
        )
        assert status == "WARNING"

        # 测试用例4: CRITICAL等级
        status = SurvivalService.determine_status(
            survival_level="CRITICAL",
            is_protected=False
        )
        assert status == "CRITICAL"

    def test_newbie_constants(self):
        """测试新手保护常量"""
        assert SurvivalService.NEWBIE_INITIAL_SCORE == 500
        assert SurvivalService.NEWBIE_PROTECTION_DAYS == 7
        assert SurvivalService.NEWBIE_FAILURE_TOLERANCE == 3

    def test_weights_sum_to_one(self):
        """测试权重总和为1"""
        total_weight = sum(SurvivalService.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001  # 允许浮点误差

    def test_survival_levels_order(self):
        """测试生存等级顺序"""
        levels = list(SurvivalService.SURVIVAL_LEVELS.keys())
        assert levels == ["ELITE", "MATURE", "GROWING", "STRUGGLING", "WARNING", "CRITICAL"]

        # 验证ROI递减
        roi_values = [SurvivalService.SURVIVAL_LEVELS[level]["roi"] for level in levels]
        assert roi_values == sorted(roi_values, reverse=True)

        # 验证积分递减
        score_values = [SurvivalService.SURVIVAL_LEVELS[level]["score"] for level in levels]
        assert score_values == sorted(score_values, reverse=True)


class TestSurvivalLevelTransitions:
    """测试生存等级转换"""

    def test_level_upgrade_path(self):
        """测试等级提升路径"""
        # CRITICAL -> WARNING
        level = SurvivalService.determine_survival_level(roi=0.15, total_score=80)
        assert level == "WARNING"

        # WARNING -> STRUGGLING
        level = SurvivalService.determine_survival_level(roi=0.4, total_score=200)
        assert level == "STRUGGLING"

        # STRUGGLING -> GROWING
        level = SurvivalService.determine_survival_level(roi=0.7, total_score=700)
        assert level == "GROWING"

        # GROWING -> MATURE
        level = SurvivalService.determine_survival_level(roi=1.5, total_score=2000)
        assert level == "MATURE"

        # MATURE -> ELITE
        level = SurvivalService.determine_survival_level(roi=2.5, total_score=6000)
        assert level == "ELITE"

    def test_level_downgrade_path(self):
        """测试等级降级路径"""
        # ELITE -> MATURE (ROI下降)
        level = SurvivalService.determine_survival_level(roi=1.5, total_score=6000)
        assert level == "MATURE"

        # MATURE -> GROWING (积分下降)
        level = SurvivalService.determine_survival_level(roi=1.5, total_score=700)
        assert level == "GROWING"

        # GROWING -> STRUGGLING (ROI下降)
        level = SurvivalService.determine_survival_level(roi=0.4, total_score=700)
        assert level == "STRUGGLING"


class TestEdgeCases:
    """测试边界情况"""

    def test_exact_threshold_values(self):
        """测试精确阈值"""
        # ELITE阈值: ROI=2.0, score=5000
        level = SurvivalService.determine_survival_level(roi=2.0, total_score=5000)
        assert level == "ELITE"

        # 刚好不够ELITE
        level = SurvivalService.determine_survival_level(roi=1.99, total_score=5000)
        assert level == "MATURE"

        level = SurvivalService.determine_survival_level(roi=2.0, total_score=4999)
        assert level == "MATURE"

    def test_extreme_values(self):
        """测试极端值"""
        # 极高ROI和积分
        level = SurvivalService.determine_survival_level(roi=100.0, total_score=1000000)
        assert level == "ELITE"

        # 极低ROI和积分
        level = SurvivalService.determine_survival_level(roi=0.001, total_score=1)
        assert level == "CRITICAL"

    def test_negative_values(self):
        """测试负值（虽然实际不应该出现）"""
        # 负ROI（理论上不应该，但测试健壮性）
        level = SurvivalService.determine_survival_level(roi=-1.0, total_score=100)
        assert level == "CRITICAL"

        # 负积分
        level = SurvivalService.determine_survival_level(roi=1.0, total_score=-100)
        assert level == "CRITICAL"


class TestPerformance:
    """测试性能"""

    def test_calculate_total_score_performance(self):
        """测试总积分计算性能"""
        import time

        start = time.time()
        for _ in range(10000):
            SurvivalService.calculate_total_score(
                task_score=500,
                quality_score=0.8,
                efficiency_score=0.7,
                innovation_score=0.6,
                collaboration_score=0.9
            )
        duration = time.time() - start

        # 10000次计算应该在100ms内完成
        assert duration < 0.1

    def test_determine_survival_level_performance(self):
        """测试等级判断性能"""
        import time

        start = time.time()
        for _ in range(10000):
            SurvivalService.determine_survival_level(roi=1.5, total_score=2000)
        duration = time.time() - start

        # 10000次判断应该在100ms内完成
        assert duration < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
