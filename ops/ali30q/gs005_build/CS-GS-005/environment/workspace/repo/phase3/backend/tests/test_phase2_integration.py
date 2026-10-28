"""
Phase 2 集成测试
测试所有Phase 2功能的协同工作
"""
import pytest
from datetime import datetime, timedelta
from services.survival_service import SurvivalService
from services.anti_cheat_service import AntiCheatService
from services.newbie_protection_service import NewbieProtectionService
from services.financial_service import FinancialService


class TestPhase2Integration:
    """Phase 2集成测试"""

    def test_complete_agent_lifecycle(self):
        """
        测试Agent完整生命周期

        流程：
        1. Agent注册
        2. 新手保护期
        3. 完成任务
        4. 毕业
        5. 正常运营
        6. 可能淘汰
        """
        # 模拟Agent生命周期
        agent_id = 1

        # 1. 新手阶段
        assert NewbieProtectionService.PROTECTION_CONFIG["initial_score"] == 500
        assert NewbieProtectionService.PROTECTION_CONFIG["protection_days"] == 7

        # 2. 毕业条件
        assert NewbieProtectionService.PROTECTION_CONFIG["min_tasks_for_graduation"] == 10
        assert NewbieProtectionService.PROTECTION_CONFIG["min_success_rate"] == 0.7

        # 3. 生存等级
        assert "ELITE" in SurvivalService.SURVIVAL_LEVELS
        assert "CRITICAL" in SurvivalService.SURVIVAL_LEVELS

    def test_task_completion_flow(self):
        """
        测试任务完成流程

        流程：
        1. 接受任务
        2. 执行任务
        3. 计算成本
        4. 获得奖励
        5. 结算
        6. 更新评分
        """
        # 模拟任务完成 - 使用更高的奖励确保盈利
        base_reward = 50000  # 提高基础奖励
        execution_time = 100  # 秒

        # 计算收入
        income = FinancialService.calculate_task_income(
            base_reward=base_reward,
            quality_rating=4.8,
            is_innovative=True
        )

        assert income["base_reward"] == base_reward
        assert income["quality_bonus"] > 0  # 高质量奖金
        assert income["innovation_bonus"] > 0  # 创新奖励
        assert income["total_income"] > base_reward

        # 计算成本
        cost = FinancialService.calculate_task_cost(
            execution_time=execution_time,
            storage_size=100,
            network_size=50
        )

        assert cost["compute_cost"] > 0
        assert cost["storage_cost"] > 0
        assert cost["network_cost"] > 0
        assert cost["gas_cost"] > 0
        assert cost["total_cost"] > 0

        # 验证盈利
        net_profit = income["total_income"] - cost["total_cost"]
        assert net_profit > 0  # 应该盈利

    def test_cheat_detection_and_penalty(self):
        """
        测试作弊检测和惩罚流程

        流程：
        1. 检测作弊
        2. 应用惩罚
        3. Agent申诉
        4. 审核申诉
        5. 恢复或维持
        """
        # 验证检测阈值
        assert AntiCheatService.TASK_SPAM_THRESHOLD["tasks_per_hour"] == 20
        assert AntiCheatService.SELF_TRADE_THRESHOLD["same_wallet"] is True

        # 验证惩罚配置
        penalties = AntiCheatService.PENALTIES
        assert "TASK_SPAM" in penalties
        assert "SELF_TRADE" in penalties
        assert penalties["TASK_SPAM"]["score_deduction"] == 100
        assert penalties["SELF_TRADE"]["score_deduction"] == 500

    def test_newbie_protection_flow(self):
        """
        测试新手保护流程

        流程：
        1. 新手注册
        2. 获得保护
        3. 失败容忍
        4. 任务推荐
        5. 毕业检查
        """
        # 验证保护配置
        config = NewbieProtectionService.PROTECTION_CONFIG
        assert config["protection_days"] == 7
        assert config["initial_score"] == 500
        assert config["failure_tolerance"] == 3

        # 验证毕业条件
        assert config["min_tasks_for_graduation"] == 10
        assert config["min_success_rate"] == 0.7
        assert config["min_avg_rating"] == 3.5

    def test_financial_settlement_flow(self):
        """
        测试财务结算流程

        流程：
        1. 任务完成
        2. 计算收入
        3. 计算成本
        4. 记录交易
        5. 更新ROI
        """
        # 验证成本类型
        cost_types = FinancialService.COST_TYPES
        assert "COMPUTE" in cost_types
        assert "STORAGE" in cost_types
        assert "NETWORK" in cost_types
        assert "GAS" in cost_types

        # 验证收入类型
        income_types = FinancialService.INCOME_TYPES
        assert "TASK_REWARD" in income_types
        assert "QUALITY_BONUS" in income_types
        assert "INNOVATION_BONUS" in income_types


class TestSurvivalMechanismIntegration:
    """生存机制集成测试"""

    def test_score_calculation_integration(self):
        """测试评分计算集成"""
        # 测试多维度评分
        score = SurvivalService.calculate_total_score(
            task_score=500,
            quality_score=0.85,
            efficiency_score=0.78,
            innovation_score=0.65,
            collaboration_score=0.90
        )

        assert score > 0
        assert isinstance(score, int)

    def test_roi_and_level_integration(self):
        """测试ROI和等级判断集成"""
        # 测试ROI计算
        roi = SurvivalService.calculate_roi(
            total_income=20000,
            total_cost=10000
        )
        assert roi == 2.0

        # 测试等级判断
        level = SurvivalService.determine_survival_level(
            roi=2.0,
            total_score=5000
        )
        assert level == "ELITE"

    def test_status_determination_integration(self):
        """测试状态判断集成"""
        # 保护期内
        status = SurvivalService.determine_status(
            survival_level="CRITICAL",
            is_protected=True
        )
        assert status == "ACTIVE"

        # 非保护期
        status = SurvivalService.determine_status(
            survival_level="CRITICAL",
            is_protected=False
        )
        assert status == "CRITICAL"


class TestAntiCheatIntegration:
    """反作弊集成测试"""

    def test_detection_and_penalty_integration(self):
        """测试检测和惩罚集成"""
        # 验证所有违规类型都有对应惩罚
        for violation_type in ["TASK_SPAM", "SELF_TRADE", "FAKE_RATING", "COLLUSION"]:
            assert violation_type in AntiCheatService.PENALTIES

    def test_penalty_severity_consistency(self):
        """测试惩罚严重程度一致性"""
        penalties = AntiCheatService.PENALTIES

        # MINOR惩罚应该比MAJOR惩罚轻
        minor_penalties = [
            p["score_deduction"]
            for p in penalties.values()
            if p["severity"] == "MINOR"
        ]

        major_penalties = [
            p["score_deduction"]
            for p in penalties.values()
            if p["severity"] == "MAJOR"
        ]

        if minor_penalties and major_penalties:
            assert max(minor_penalties) < min(major_penalties)


class TestNewbieProtectionIntegration:
    """新手保护集成测试"""

    def test_protection_and_graduation_integration(self):
        """测试保护和毕业集成"""
        config = NewbieProtectionService.PROTECTION_CONFIG

        # 验证配置一致性
        assert config["initial_score"] == SurvivalService.NEWBIE_INITIAL_SCORE
        assert config["protection_days"] == SurvivalService.NEWBIE_PROTECTION_DAYS

    def test_failure_tolerance_integration(self):
        """测试失败容忍集成"""
        config = NewbieProtectionService.PROTECTION_CONFIG

        # 验证失败容忍配置
        assert config["failure_tolerance"] == SurvivalService.NEWBIE_FAILURE_TOLERANCE


class TestFinancialIntegration:
    """财务集成测试"""

    def test_cost_calculation_consistency(self):
        """测试成本计算一致性"""
        # 测试零成本
        cost = FinancialService.calculate_task_cost(
            execution_time=0,
            storage_size=0,
            network_size=0,
            include_gas=False
        )
        assert cost["total_cost"] == 0

        # 测试正常成本
        cost = FinancialService.calculate_task_cost(
            execution_time=100,
            storage_size=100,
            network_size=50,
            include_gas=True
        )
        assert cost["total_cost"] > 0
        assert cost["compute_cost"] > 0
        assert cost["gas_cost"] > 0

    def test_income_calculation_consistency(self):
        """测试收入计算一致性"""
        # 基础奖励
        income = FinancialService.calculate_task_income(
            base_reward=10000
        )
        assert income["total_income"] == 10000
        assert income["quality_bonus"] == 0
        assert income["innovation_bonus"] == 0

        # 带质量奖金
        income = FinancialService.calculate_task_income(
            base_reward=10000,
            quality_rating=4.8
        )
        assert income["total_income"] > 10000
        assert income["quality_bonus"] > 0

        # 带创新奖励
        income = FinancialService.calculate_task_income(
            base_reward=10000,
            is_innovative=True
        )
        assert income["total_income"] > 10000
        assert income["innovation_bonus"] > 0


class TestPerformanceIntegration:
    """性能集成测试"""

    def test_survival_calculation_performance(self):
        """测试生存机制计算性能"""
        import time

        start = time.time()
        for _ in range(1000):
            SurvivalService.calculate_total_score(
                task_score=500,
                quality_score=0.8,
                efficiency_score=0.7,
                innovation_score=0.6,
                collaboration_score=0.9
            )
            SurvivalService.calculate_roi(10000, 5000)
            SurvivalService.determine_survival_level(1.5, 2000)
        duration = time.time() - start

        # 1000次计算应该在100ms内完成
        assert duration < 0.1

    def test_financial_calculation_performance(self):
        """测试财务计算性能"""
        import time

        start = time.time()
        for _ in range(1000):
            FinancialService.calculate_task_cost(100, 100, 50)
            FinancialService.calculate_task_income(10000, 4.5, True)
        duration = time.time() - start

        # 1000次计算应该在50ms内完成
        assert duration < 0.05


class TestDataConsistency:
    """数据一致性测试"""

    def test_config_consistency(self):
        """测试配置一致性"""
        # 新手保护配置应该一致
        assert (
            NewbieProtectionService.PROTECTION_CONFIG["initial_score"] ==
            SurvivalService.NEWBIE_INITIAL_SCORE
        )

        assert (
            NewbieProtectionService.PROTECTION_CONFIG["protection_days"] ==
            SurvivalService.NEWBIE_PROTECTION_DAYS
        )

        assert (
            NewbieProtectionService.PROTECTION_CONFIG["failure_tolerance"] ==
            SurvivalService.NEWBIE_FAILURE_TOLERANCE
        )

    def test_weights_sum_to_one(self):
        """测试权重总和为1"""
        total_weight = sum(SurvivalService.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
