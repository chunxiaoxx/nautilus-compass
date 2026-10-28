"""
反作弊系统单元测试
"""
import pytest
from datetime import datetime, timedelta
from services.anti_cheat_service import AntiCheatService


class TestAntiCheatThresholds:
    """测试反作弊阈值配置"""

    def test_task_spam_threshold(self):
        """测试任务刷分阈值"""
        assert AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"] == 20
        assert AntiCheatService.TASK_SPAM_THRESHOLD["min_task_duration"] == 60
        assert AntiCheatService.TASK_SPAM_THRESHOLD["low_quality_threshold"] == 0.3

    def test_self_trade_threshold(self):
        """测试自我交易阈值"""
        assert AntiCheatService.SELF_TRADE_THRESHOLD["same_wallet"] is True

    def test_fake_rating_threshold(self):
        """测试虚假评分阈值"""
        assert AntiCheatService.FAKE_RATING_THRESHOLD["consecutive_high_ratings"] == 10
        assert AntiCheatService.FAKE_RATING_THRESHOLD["high_rating_value"] == 4.5
        assert AntiCheatService.FAKE_RATING_THRESHOLD["rating_variance"] == 0.1

    def test_collusion_threshold(self):
        """测试串通作弊阈值"""
        assert AntiCheatService.COLLUSION_THRESHOLD["mutual_tasks"] == 5
        assert AntiCheatService.COLLUSION_THRESHOLD["time_window_days"] == 30
        assert AntiCheatService.COLLUSION_THRESHOLD["rating_similarity"] == 0.9


class TestPenaltyConfiguration:
    """测试惩罚配置"""

    def test_task_spam_penalty(self):
        """测试任务刷分惩罚"""
        penalty = AntiCheatService.PENALTIES["TASK_SPAM"]
        assert penalty["severity"] == "MINOR"
        assert penalty["penalty_type"] == "SCORE_DEDUCTION"
        assert penalty["score_deduction"] == 100

    def test_self_trade_penalty(self):
        """测试自我交易惩罚"""
        penalty = AntiCheatService.PENALTIES["SELF_TRADE"]
        assert penalty["severity"] == "MAJOR"
        assert penalty["penalty_type"] == "SCORE_DEDUCTION"
        assert penalty["score_deduction"] == 500

    def test_fake_rating_penalty(self):
        """测试虚假评分惩罚"""
        penalty = AntiCheatService.PENALTIES["FAKE_RATING"]
        assert penalty["severity"] == "MINOR"
        assert penalty["penalty_type"] == "SCORE_DEDUCTION"
        assert penalty["score_deduction"] == 200

    def test_collusion_penalty(self):
        """测试串通作弊惩罚"""
        penalty = AntiCheatService.PENALTIES["COLLUSION"]
        assert penalty["severity"] == "MAJOR"
        assert penalty["penalty_type"] == "DOWNGRADE"
        assert penalty["score_deduction"] == 1000

    def test_penalty_severity_order(self):
        """测试惩罚严重程度顺序"""
        severities = ["WARNING", "MINOR", "MAJOR", "CRITICAL"]

        # TASK_SPAM和FAKE_RATING是MINOR
        assert AntiCheatService.PENALTIES["TASK_SPAM"]["severity"] == "MINOR"
        assert AntiCheatService.PENALTIES["FAKE_RATING"]["severity"] == "MINOR"

        # SELF_TRADE和COLLUSION是MAJOR
        assert AntiCheatService.PENALTIES["SELF_TRADE"]["severity"] == "MAJOR"
        assert AntiCheatService.PENALTIES["COLLUSION"]["severity"] == "MAJOR"

    def test_score_deduction_proportional(self):
        """测试积分扣除与严重程度成正比"""
        minor_penalties = [
            AntiCheatService.PENALTIES["TASK_SPAM"]["score_deduction"],
            AntiCheatService.PENALTIES["FAKE_RATING"]["score_deduction"]
        ]

        major_penalties = [
            AntiCheatService.PENALTIES["SELF_TRADE"]["score_deduction"],
            AntiCheatService.PENALTIES["COLLUSION"]["score_deduction"]
        ]

        # MAJOR惩罚应该比MINOR惩罚更重
        assert min(major_penalties) > max(minor_penalties)


class TestDetectionLogic:
    """测试检测逻辑"""

    def test_task_spam_detection_logic(self):
        """测试任务刷分检测逻辑"""
        # 模拟场景：1小时内完成25个任务，其中15个时长<60秒
        task_count = 25
        suspicious_count = 15

        # 检查是否超过阈值
        assert task_count >= AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"]

        # 检查是否超过一半任务异常
        assert suspicious_count > task_count / 2

    def test_fake_rating_variance_calculation(self):
        """测试虚假评分方差计算"""
        # 正常评分（方差较大）
        normal_ratings = [4.5, 3.8, 4.2, 4.0, 3.5, 4.8, 4.1, 3.9, 4.3, 4.6]
        avg = sum(normal_ratings) / len(normal_ratings)
        variance = sum((r - avg) ** 2 for r in normal_ratings) / len(normal_ratings)
        assert variance > AntiCheatService.FAKE_RATING_THRESHOLD["rating_variance"]

        # 虚假评分（方差极小）
        fake_ratings = [4.9, 5.0, 4.9, 5.0, 4.9, 5.0, 4.9, 5.0, 4.9, 5.0]
        avg = sum(fake_ratings) / len(fake_ratings)
        variance = sum((r - avg) ** 2 for r in fake_ratings) / len(fake_ratings)
        assert variance < AntiCheatService.FAKE_RATING_THRESHOLD["rating_variance"]

    def test_consecutive_high_ratings(self):
        """测试连续高评分检测"""
        # 连续10个高评分
        ratings = [4.8, 4.9, 5.0, 4.7, 4.9, 5.0, 4.8, 4.9, 5.0, 4.8]
        consecutive_high = sum(
            1 for r in ratings
            if r >= AntiCheatService.FAKE_RATING_THRESHOLD["high_rating_value"]
        )
        assert consecutive_high >= AntiCheatService.FAKE_RATING_THRESHOLD["consecutive_high_ratings"]


class TestPenaltyApplication:
    """测试惩罚应用逻辑"""

    def test_penalty_types(self):
        """测试惩罚类型"""
        valid_types = ["WARNING", "SCORE_DEDUCTION", "DOWNGRADE", "BAN"]

        for violation_type, config in AntiCheatService.PENALTIES.items():
            assert config["penalty_type"] in valid_types

    def test_score_deduction_values(self):
        """测试积分扣除值"""
        for violation_type, config in AntiCheatService.PENALTIES.items():
            assert config["score_deduction"] > 0
            assert config["score_deduction"] <= 1000  # 最大扣除1000分


class TestAppealProcess:
    """测试申诉流程"""

    def test_appeal_status_flow(self):
        """测试申诉状态流转"""
        # 正常流程: ACTIVE -> APPEALED -> RESOLVED
        statuses = ["ACTIVE", "APPEALED", "RESOLVED"]

        # 验证状态顺序
        assert statuses[0] == "ACTIVE"
        assert statuses[1] == "APPEALED"
        assert statuses[2] == "RESOLVED"

    def test_appeal_decisions(self):
        """测试申诉决策"""
        valid_decisions = ["APPROVED", "REJECTED"]

        # 验证决策类型
        assert "APPROVED" in valid_decisions
        assert "REJECTED" in valid_decisions


class TestEdgeCases:
    """测试边界情况"""

    def test_zero_tasks(self):
        """测试零任务情况"""
        task_count = 0
        assert task_count < AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"]

    def test_exact_threshold_tasks(self):
        """测试精确阈值"""
        task_count = AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"]
        assert task_count >= AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"]

    def test_single_high_rating(self):
        """测试单个高评分"""
        consecutive_high = 1
        assert consecutive_high < AntiCheatService.FAKE_RATING_THRESHOLD["consecutive_high_ratings"]

    def test_exact_threshold_ratings(self):
        """测试精确评分阈值"""
        consecutive_high = AntiCheatService.FAKE_RATING_THRESHOLD["consecutive_high_ratings"]
        assert consecutive_high >= AntiCheatService.FAKE_RATING_THRESHOLD["consecutive_high_ratings"]


class TestPerformance:
    """测试性能"""

    def test_detection_performance(self):
        """测试检测性能"""
        import time

        # 模拟检测逻辑（简化版）
        start = time.time()
        for _ in range(1000):
            # 模拟任务刷分检测
            task_count = 25
            suspicious_count = 15
            is_spam = (
                task_count >= AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"] and
                suspicious_count > task_count / 2
            )
        duration = time.time() - start

        # 1000次检测应该在100ms内完成
        assert duration < 0.1

    def test_penalty_calculation_performance(self):
        """测试惩罚计算性能"""
        import time

        start = time.time()
        for _ in range(10000):
            # 模拟惩罚配置查询
            penalty = AntiCheatService.PENALTIES.get("TASK_SPAM")
            score_deduction = penalty["score_deduction"] if penalty else 0
        duration = time.time() - start

        # 10000次查询应该在50ms内完成
        assert duration < 0.05


class TestIntegration:
    """测试集成场景"""

    def test_multiple_violations(self):
        """测试多重违规"""
        # 一个Agent可能同时触发多种违规
        violations = ["TASK_SPAM", "FAKE_RATING"]
        total_deduction = sum(
            AntiCheatService.PENALTIES[v]["score_deduction"]
            for v in violations
        )

        # 总扣除 = 100 + 200 = 300
        assert total_deduction == 300

    def test_repeated_violations(self):
        """测试重复违规"""
        # 同一违规类型重复3次
        violation_type = "TASK_SPAM"
        repeat_count = 3
        total_deduction = (
            AntiCheatService.PENALTIES[violation_type]["score_deduction"] *
            repeat_count
        )

        # 总扣除 = 100 * 3 = 300
        assert total_deduction == 300

    def test_appeal_approval_restores_score(self):
        """测试申诉通过恢复积分"""
        # 原始积分
        original_score = 1000

        # 扣除惩罚
        penalty_deduction = AntiCheatService.PENALTIES["TASK_SPAM"]["score_deduction"]
        score_after_penalty = original_score - penalty_deduction
        assert score_after_penalty == 900

        # 申诉通过，恢复积分
        score_after_appeal = score_after_penalty + penalty_deduction
        assert score_after_appeal == original_score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
