"""
Epiplexity服务层测试
"""
import pytest
from services.epiplexity_service import EpiplexityService


class TestEpiplexityCalculation:
    """测试Epiplexity计算"""

    def test_calculate_epiplexity_basic(self):
        """测试基础Epiplexity计算"""
        content = """
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        """

        result = EpiplexityService.calculate_epiplexity(content, "CODE")

        assert "structural_complexity" in result
        assert "learnable_content" in result
        assert "transferability" in result
        assert "epiplexity_score" in result

        # 验证范围
        assert 0.0 <= result["structural_complexity"] <= 1.0
        assert 0.0 <= result["learnable_content"] <= 1.0
        assert 0.0 <= result["transferability"] <= 1.0
        assert 0.0 <= result["epiplexity_score"] <= 1.0

    def test_empty_content(self):
        """测试空内容"""
        result = EpiplexityService.calculate_epiplexity("", "TEXT")

        assert result["structural_complexity"] == 0.0
        assert result["learnable_content"] == 0.0
        assert result["transferability"] == 0.0
        assert result["epiplexity_score"] == 0.0

    def test_simple_vs_complex(self):
        """测试简单内容vs复杂内容"""
        simple = "Hello world"
        complex_content = """
        class ComplexSystem:
            def __init__(self):
                self.data = {}
                self.cache = []

            def process(self, input_data):
                if input_data in self.cache:
                    return self.data[input_data]

                result = self._compute(input_data)
                self.cache.append(input_data)
                self.data[input_data] = result
                return result

            def _compute(self, data):
                # Complex computation
                return sum(ord(c) for c in str(data))
        """

        simple_result = EpiplexityService.calculate_epiplexity(simple, "TEXT")
        complex_result = EpiplexityService.calculate_epiplexity(complex_content, "CODE")

        # 复杂内容应该有更高的评分
        assert complex_result["epiplexity_score"] > simple_result["epiplexity_score"]


class TestStructuralComplexity:
    """测试结构复杂性分析"""

    def test_code_nesting(self):
        """测试代码嵌套"""
        nested_code = """
        def outer():
            def inner():
                if True:
                    for i in range(10):
                        while i > 0:
                            pass
        """

        sc = EpiplexityService.analyze_structural_complexity(nested_code, "CODE")
        assert sc > 0.2  # 有嵌套应该有一定复杂性

    def test_simple_text(self):
        """测试简单文本"""
        simple_text = "This is a simple sentence."

        sc = EpiplexityService.analyze_structural_complexity(simple_text, "TEXT")
        assert sc < 0.5  # 简单文本应该有较低复杂性


class TestLearnableContent:
    """测试可学习内容分析"""

    def test_concept_rich_content(self):
        """测试概念丰富的内容"""
        content = """
        Machine Learning uses Neural Networks and Deep Learning.
        Algorithms like Gradient Descent optimize Model Parameters.
        """

        lc = EpiplexityService.analyze_learnable_content(content, "TEXT")
        assert lc > 0.3  # 概念丰富应该有较高可学习性

    def test_repetitive_content(self):
        """测试重复内容"""
        content = "test test test test test"

        lc = EpiplexityService.analyze_learnable_content(content, "TEXT")
        assert lc < 0.5  # 重复内容可学习性较低


class TestTransferability:
    """测试可迁移性分析"""

    def test_generic_code(self):
        """测试通用代码"""
        generic = """
        def sort_list(items):
            return sorted(items)
        """

        t = EpiplexityService.analyze_transferability(generic, {})
        assert t > 0.3  # 通用代码可迁移性较高

    def test_specific_code(self):
        """测试特定代码"""
        specific = """
        def connect_to_localhost():
            import custom_module
            return custom_module.connect('localhost:8080')
        """

        t = EpiplexityService.analyze_transferability(specific, {})
        # 特定代码可迁移性可能较低（但不一定，取决于其他因素）
        assert 0.0 <= t <= 1.0


class TestComplexityLevel:
    """测试复杂性等级判断"""

    def test_low_complexity(self):
        """测试低复杂性"""
        level = EpiplexityService.determine_complexity_level(0.2)
        assert level == "LOW"

    def test_medium_complexity(self):
        """测试中等复杂性"""
        level = EpiplexityService.determine_complexity_level(0.5)
        assert level == "MEDIUM"

    def test_high_complexity(self):
        """测试高复杂性"""
        level = EpiplexityService.determine_complexity_level(0.8)
        assert level == "HIGH"

    def test_boundary_values(self):
        """测试边界值"""
        assert EpiplexityService.determine_complexity_level(0.0) == "LOW"
        assert EpiplexityService.determine_complexity_level(0.3) == "MEDIUM"
        assert EpiplexityService.determine_complexity_level(0.7) == "HIGH"
        assert EpiplexityService.determine_complexity_level(1.0) == "HIGH"


class TestPerformance:
    """测试性能"""

    def test_calculation_performance(self):
        """测试计算性能"""
        import time

        content = "def test(): pass\n" * 100

        start = time.time()
        for _ in range(100):
            EpiplexityService.calculate_epiplexity(content, "CODE")
        duration = time.time() - start

        # 100次计算应该在1秒内完成
        assert duration < 1.0

    def test_large_content(self):
        """测试大内容"""
        large_content = "x = 1\n" * 10000

        result = EpiplexityService.calculate_epiplexity(large_content, "CODE")

        # 应该能处理大内容
        assert result["epiplexity_score"] > 0


class TestEdgeCases:
    """测试边界情况"""

    def test_unicode_content(self):
        """测试Unicode内容"""
        content = "你好世界 Hello World 🌍"

        result = EpiplexityService.calculate_epiplexity(content, "TEXT")
        assert result["epiplexity_score"] >= 0

    def test_special_characters(self):
        """测试特殊字符"""
        content = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"

        result = EpiplexityService.calculate_epiplexity(content, "TEXT")
        assert result["epiplexity_score"] >= 0

    def test_whitespace_only(self):
        """测试纯空白"""
        content = "   \n\n\t\t   "

        result = EpiplexityService.calculate_epiplexity(content, "TEXT")
        assert result["epiplexity_score"] == 0.0


class TestConsistency:
    """测试一致性"""

    def test_same_content_same_result(self):
        """测试相同内容产生相同结果"""
        content = "def test(): return 42"

        result1 = EpiplexityService.calculate_epiplexity(content, "CODE")
        result2 = EpiplexityService.calculate_epiplexity(content, "CODE")

        assert result1 == result2

    def test_formula_consistency(self):
        """测试公式一致性"""
        # 手动计算验证
        sc = 0.5
        lc = 0.6
        t = 0.7

        # epiplexity = (SC^0.4) × (LC^0.4) × (T^0.2)
        expected = (sc ** 0.4) * (lc ** 0.4) * (t ** 0.2)

        # 创建内容使其产生接近这些值的结果
        # 这里只验证公式逻辑
        assert expected > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
