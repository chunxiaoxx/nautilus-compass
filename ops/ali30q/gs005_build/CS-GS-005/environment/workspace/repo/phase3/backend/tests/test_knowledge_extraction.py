"""
测试知识提取服务 - Task 5.2
"""

import pytest
import ast
from services.knowledge_extraction_service import KnowledgeExtractionService


@pytest.fixture
def extraction_service():
    """创建知识提取服务实例"""
    return KnowledgeExtractionService()


class TestKnowledgeExtractionService:
    """测试知识提取服务"""

    def test_extract_singleton_pattern(self, extraction_service):
        """测试提取Singleton模式"""
        code = """
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        singleton_patterns = [p for p in patterns if p["pattern_name"] == "Singleton"]
        assert len(singleton_patterns) > 0
        assert singleton_patterns[0]["confidence"] >= 0.8

    def test_extract_factory_pattern(self, extraction_service):
        """测试提取Factory模式"""
        code = """
def create_user(user_type):
    if user_type == "admin":
        return AdminUser()
    elif user_type == "regular":
        return RegularUser()
    else:
        return GuestUser()
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        factory_patterns = [p for p in patterns if p["pattern_name"] == "Factory"]
        assert len(factory_patterns) > 0
        assert factory_patterns[0]["confidence"] >= 0.8

    def test_extract_builder_pattern(self, extraction_service):
        """测试提取Builder模式"""
        code = """
class QueryBuilder:
    def __init__(self):
        self.query = ""

    def select(self, fields):
        self.query += f"SELECT {fields} "
        return self

    def from_table(self, table):
        self.query += f"FROM {table} "
        return self

    def where(self, condition):
        self.query += f"WHERE {condition}"
        return self

    def build(self):
        return self.query
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        builder_patterns = [p for p in patterns if p["pattern_name"] == "Builder"]
        assert len(builder_patterns) > 0
        assert builder_patterns[0]["metadata"]["chainable_methods"] >= 2

    def test_extract_observer_pattern(self, extraction_service):
        """测试提取Observer模式"""
        code = """
class Subject:
    def __init__(self):
        self.observers = []

    def subscribe(self, observer):
        self.observers.append(observer)

    def notify(self, event):
        for observer in self.observers:
            observer.update(event)
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        observer_patterns = [p for p in patterns if p["pattern_name"] == "Observer"]
        assert len(observer_patterns) > 0
        assert observer_patterns[0]["confidence"] >= 0.8

    def test_extract_strategy_pattern(self, extraction_service):
        """测试提取Strategy模式"""
        code = """
class SortStrategy:
    def execute(self, data):
        pass

class QuickSortStrategy(SortStrategy):
    def execute(self, data):
        return sorted(data)
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        strategy_patterns = [p for p in patterns if p["pattern_name"] == "Strategy"]
        assert len(strategy_patterns) > 0

    def test_extract_decorator_pattern(self, extraction_service):
        """测试提取Decorator模式"""
        code = """
@cache_result
@log_execution
@validate_input
def expensive_computation(x, y):
    return x * y
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        decorator_patterns = [p for p in patterns if p["pattern_name"] == "Decorator"]
        assert len(decorator_patterns) > 0
        assert decorator_patterns[0]["confidence"] == 1.0
        assert len(decorator_patterns[0]["metadata"]["decorators"]) == 3

    def test_extract_adapter_pattern(self, extraction_service):
        """测试提取Adapter模式"""
        code = """
class LegacySystemAdapter:
    def __init__(self, legacy_system):
        self.legacy_system = legacy_system

    def new_interface_method(self):
        return self.legacy_system.old_method()
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        adapter_patterns = [p for p in patterns if p["pattern_name"] == "Adapter"]
        assert len(adapter_patterns) > 0

    def test_extract_recursive_algorithm(self, extraction_service):
        """测试提取递归算法"""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        recursive_patterns = [p for p in patterns if p["pattern_name"] == "Recursion"]
        assert len(recursive_patterns) == 2
        assert all(p["confidence"] == 1.0 for p in recursive_patterns)

    def test_extract_dynamic_programming(self, extraction_service):
        """测试提取动态规划模式"""
        code = """
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci_dp(n):
    if n <= 1:
        return n
    return fibonacci_dp(n-1) + fibonacci_dp(n-2)

def knapsack(weights, values, capacity):
    dp = [[0] * (capacity + 1) for _ in range(len(weights) + 1)]
    for i in range(1, len(weights) + 1):
        for w in range(1, capacity + 1):
            if weights[i-1] <= w:
                dp[i][w] = max(dp[i-1][w], values[i-1] + dp[i-1][w-weights[i-1]])
    return dp[-1][-1]
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        dp_patterns = [p for p in patterns if p["pattern_name"] == "Dynamic Programming"]
        assert len(dp_patterns) >= 1

    def test_extract_divide_and_conquer(self, extraction_service):
        """测试提取分治算法"""
        code = """
def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] < right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        dc_patterns = [p for p in patterns if p["pattern_name"] == "Divide and Conquer"]
        assert len(dc_patterns) > 0

    def test_extract_greedy_algorithm(self, extraction_service):
        """测试提取贪心算法"""
        code = """
def activity_selection(activities):
    activities.sort(key=lambda x: x[1])
    selected = []
    last_end = 0
    for start, end in activities:
        if start >= last_end:
            selected.append((start, end))
            last_end = end
    return selected
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        greedy_patterns = [p for p in patterns if p["pattern_name"] == "Greedy Algorithm"]
        assert len(greedy_patterns) > 0

    def test_extract_backtracking(self, extraction_service):
        """测试提取回溯算法"""
        code = """
def solve_n_queens(n):
    def backtrack(row, cols, diag1, diag2, board):
        if row == n:
            result.append(board[:])
            return
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            board.append(col)
            backtrack(row + 1, cols, diag1, diag2, board)
            board.pop()
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)

    result = []
    backtrack(0, set(), set(), set(), [])
    return result
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        backtrack_patterns = [p for p in patterns if p["pattern_name"] == "Backtracking"]
        assert len(backtrack_patterns) > 0

    def test_extract_repository_pattern(self, extraction_service):
        """测试提取Repository模式"""
        code = """
class UserRepository:
    def __init__(self, db):
        self.db = db

    def find_by_id(self, user_id):
        return self.db.query(User).filter_by(id=user_id).first()

    def find_all(self):
        return self.db.query(User).all()

    def create(self, user):
        self.db.add(user)
        self.db.commit()

    def update(self, user):
        self.db.commit()

    def delete(self, user):
        self.db.delete(user)
        self.db.commit()
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        repo_patterns = [p for p in patterns if p["pattern_name"] == "Repository"]
        assert len(repo_patterns) > 0
        assert len(repo_patterns[0]["metadata"]["crud_operations"]) >= 2

    def test_extract_service_layer(self, extraction_service):
        """测试提取Service层模式"""
        code = """
class UserService:
    def __init__(self, repository):
        self.repository = repository

    def register_user(self, username, email):
        user = User(username=username, email=email)
        return self.repository.create(user)

    def authenticate(self, username, password):
        user = self.repository.find_by_username(username)
        return user and user.check_password(password)
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        service_patterns = [p for p in patterns if p["pattern_name"] == "Service Layer"]
        assert len(service_patterns) > 0

    def test_extract_dependency_injection(self, extraction_service):
        """测试提取依赖注入模式"""
        code = """
class OrderService:
    def __init__(self, repository, payment_gateway, notification_service):
        self.repository = repository
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service

class PaymentService:
    def __init__(self, gateway, logger):
        self.gateway = gateway
        self.logger = logger
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        di_patterns = [p for p in patterns if p["pattern_name"] == "Dependency Injection"]
        assert len(di_patterns) > 0

    def test_extract_context_manager(self, extraction_service):
        """测试提取Context Manager"""
        code = """
class DatabaseConnection:
    def __enter__(self):
        self.conn = connect_to_db()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        cm_patterns = [p for p in patterns if p["pattern_name"] == "Context Manager"]
        assert len(cm_patterns) > 0
        assert cm_patterns[0]["confidence"] == 1.0

    def test_extract_list_comprehension(self, extraction_service):
        """测试提取列表推导式"""
        code = """
def process_data(items):
    squared = [x**2 for x in items if x > 0]
    return squared
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        comp_patterns = [p for p in patterns if "Comprehension" in p["pattern_name"]]
        assert len(comp_patterns) > 0

    def test_extract_generator(self, extraction_service):
        """测试提取生成器"""
        code = """
def fibonacci_generator(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

def read_large_file(filename):
    with open(filename) as f:
        for line in f:
            yield line.strip()
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        gen_patterns = [p for p in patterns if p["pattern_name"] == "Generator"]
        assert len(gen_patterns) == 2

    def test_extract_property_decorator(self, extraction_service):
        """测试提取Property装饰器"""
        code = """
class User:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        prop_patterns = [p for p in patterns if p["pattern_name"] == "Property Decorator"]
        assert len(prop_patterns) > 0

    def test_filter_by_epiplexity(self, extraction_service):
        """测试Epiplexity过滤"""
        code = """
class ComplexService:
    def __init__(self, repo, cache, logger):
        self.repo = repo
        self.cache = cache
        self.logger = logger

    def process(self, data):
        if data in self.cache:
            return self.cache[data]
        result = self.repo.fetch(data)
        self.cache[data] = result
        return result
"""
        # 低阈值
        patterns_low = extraction_service.extract_code_patterns(code, min_epiplexity=0.1)
        # 高阈值
        patterns_high = extraction_service.extract_code_patterns(code, min_epiplexity=0.8)

        # 高阈值应该过滤掉更多模式
        assert len(patterns_low) >= len(patterns_high)

    def test_pattern_confidence_scores(self, extraction_service):
        """测试模式置信度评分"""
        code = """
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        # 所有模式应该有置信度
        for pattern in patterns:
            assert "confidence" in pattern
            assert 0.0 <= pattern["confidence"] <= 1.0

    def test_pattern_metadata(self, extraction_service):
        """测试模式元数据"""
        code = """
@cache
@log
def compute(x):
    return x * 2
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        decorator_patterns = [p for p in patterns if p["pattern_name"] == "Decorator"]
        assert len(decorator_patterns) > 0
        assert "metadata" in decorator_patterns[0]
        assert "decorators" in decorator_patterns[0]["metadata"]

    def test_multiple_patterns_in_code(self, extraction_service):
        """测试识别多个模式"""
        code = """
class UserService:
    def __init__(self, repository):
        self.repository = repository

    @property
    def user_count(self):
        return len(self.repository.find_all())

    def create_user(self, user_type):
        if user_type == "admin":
            return AdminUser()
        return RegularUser()

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        # 应该识别多种模式
        pattern_names = [p["pattern_name"] for p in patterns]
        assert "Service Layer" in pattern_names
        assert "Property Decorator" in pattern_names
        assert "Factory" in pattern_names
        assert "Recursion" in pattern_names

    def test_pattern_categories(self, extraction_service):
        """测试模式分类"""
        code = """
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

class UserRepository:
    def find_all(self):
        pass
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        categories = set(p["pattern_category"] for p in patterns)
        assert "Creational" in categories or "Algorithm" in categories or "Architecture" in categories

    def test_combined_score_calculation(self, extraction_service):
        """测试综合评分计算"""
        code = """
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        for pattern in patterns:
            if "combined_score" in pattern:
                # 综合评分应该是置信度和Epiplexity的平均
                expected = (pattern["confidence"] + pattern["epiplexity"]) / 2
                assert abs(pattern["combined_score"] - expected) < 0.01

    def test_empty_code(self, extraction_service):
        """测试空代码"""
        patterns = extraction_service.extract_code_patterns("", min_epiplexity=0.0)
        assert patterns == []

    def test_invalid_syntax(self, extraction_service):
        """测试无效语法"""
        code = "def invalid syntax here"
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)
        assert patterns == []

    def test_complex_real_world_code(self, extraction_service):
        """测试复杂真实代码"""
        code = """
from functools import lru_cache

class CacheService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.cache = {}

    @property
    def size(self):
        return len(self.cache)

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        self.cache[key] = value

class UserRepository:
    def __init__(self, db):
        self.db = db

    def find_by_id(self, user_id):
        return self.db.query(User).filter_by(id=user_id).first()

    def create(self, user):
        self.db.add(user)
        self.db.commit()

class UserService:
    def __init__(self, repository, cache):
        self.repository = repository
        self.cache = cache

    @lru_cache(maxsize=128)
    def get_user(self, user_id):
        cached = self.cache.get(user_id)
        if cached:
            return cached
        user = self.repository.find_by_id(user_id)
        self.cache.set(user_id, user)
        return user
"""
        patterns = extraction_service.extract_code_patterns(code, min_epiplexity=0.0)

        # 应该识别多种模式
        assert len(patterns) >= 5
        pattern_names = [p["pattern_name"] for p in patterns]
        assert "Singleton" in pattern_names
        assert "Repository" in pattern_names
        assert "Service Layer" in pattern_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
