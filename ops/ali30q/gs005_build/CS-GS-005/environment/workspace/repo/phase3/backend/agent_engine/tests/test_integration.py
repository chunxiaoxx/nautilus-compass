"""
Nautilus Phase 3 - Agent Engine Integration Tests

Tests for agent engine, executors, learning system, and state persistence.
"""

import pytest
import asyncio
from core.engine import AgentEngine
from executors.code_executor import CodeExecutor
from executors.data_executor import DataExecutor
from executors.compute_executor import ComputeExecutor
from core.learning import LearningSystem
from core.state_persistence import StatePersistence


class TestCodeExecutor:
    """Test code executor with Docker sandbox"""

    @pytest.mark.asyncio
    async def test_execute_python_code(self):
        """Test executing Python code"""
        executor = CodeExecutor()
        code = """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
"""
        result = await executor.execute(code, language="python")
        assert result["success"] is True
        assert "3" in result["output"]

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self):
        """Test code execution timeout"""
        executor = CodeExecutor()
        code = """
import time
time.sleep(10)
"""
        result = await executor.execute(code, language="python", timeout=2)
        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_with_error(self):
        """Test code execution with error"""
        executor = CodeExecutor()
        code = """
raise ValueError("Test error")
"""
        result = await executor.execute(code, language="python")
        assert result["success"] is False
        assert "ValueError" in result["error"]


class TestDataExecutor:
    """Test data executor"""

    @pytest.mark.asyncio
    async def test_validate_json_schema(self):
        """Test JSON schema validation"""
        executor = DataExecutor()
        data = {"name": "John", "age": 30}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["name", "age"]
        }
        result = await executor.validate(data, schema)
        assert result["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_invalid_data(self):
        """Test validation with invalid data"""
        executor = DataExecutor()
        data = {"name": "John"}  # Missing age
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["name", "age"]
        }
        result = await executor.validate(data, schema)
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_analyze_data_quality(self):
        """Test data quality analysis"""
        executor = DataExecutor()
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": None},
            {"name": "Bob", "age": 25}
        ]
        result = await executor.analyze_quality(data)
        assert result["total_records"] == 3
        assert result["missing_values"] > 0


class TestComputeExecutor:
    """Test compute executor"""

    @pytest.mark.asyncio
    async def test_evaluate_expression(self):
        """Test mathematical expression evaluation"""
        executor = ComputeExecutor()
        result = await executor.evaluate("2 + 2")
        assert result["success"] is True
        assert result["result"] == 4

    @pytest.mark.asyncio
    async def test_evaluate_complex_expression(self):
        """Test complex expression"""
        executor = ComputeExecutor()
        result = await executor.evaluate("(10 + 5) * 2 - 8")
        assert result["success"] is True
        assert result["result"] == 22

    @pytest.mark.asyncio
    async def test_evaluate_with_functions(self):
        """Test expression with math functions"""
        executor = ComputeExecutor()
        result = await executor.evaluate("sqrt(16) + pow(2, 3)")
        assert result["success"] is True
        assert result["result"] == 12.0


class TestAgentEngine:
    """Test agent engine orchestration"""

    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """Test engine initialization"""
        engine = AgentEngine(agent_id=1)
        assert engine.agent_id == 1
        assert engine.max_concurrent_tasks == 3
        assert engine.graph is not None

    @pytest.mark.asyncio
    async def test_execute_code_task(self):
        """Test executing a code task"""
        engine = AgentEngine(agent_id=1)
        task = {
            "id": 1,
            "type": "CODE",
            "input_data": "def add(a, b): return a + b",
            "expected_output": "3"
        }
        result = await engine.execute_task(task)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self):
        """Test concurrent task limit"""
        engine = AgentEngine(agent_id=1, max_concurrent_tasks=2)

        # Start 2 tasks
        task1 = {"id": 1, "type": "COMPUTE", "input_data": "1+1"}
        task2 = {"id": 2, "type": "COMPUTE", "input_data": "2+2"}

        await engine.execute_task(task1)
        await engine.execute_task(task2)

        # Try to start 3rd task
        task3 = {"id": 3, "type": "COMPUTE", "input_data": "3+3"}
        result = await engine.execute_task(task3)

        assert result["success"] is False
        assert "concurrent" in result["error"].lower()


class TestLearningSystem:
    """Test learning system"""

    @pytest.mark.asyncio
    async def test_record_execution(self):
        """Test recording execution history"""
        learning = LearningSystem(agent_id=1)
        await learning.record_execution(
            task_id=1,
            task_type="CODE",
            success=True,
            execution_time=5.0
        )
        history = await learning.get_history()
        assert len(history) == 1
        assert history[0]["success"] is True

    @pytest.mark.asyncio
    async def test_analyze_patterns(self):
        """Test pattern analysis"""
        learning = LearningSystem(agent_id=1)

        # Record multiple executions
        for i in range(10):
            await learning.record_execution(
                task_id=i,
                task_type="CODE",
                success=i % 2 == 0,  # 50% success rate
                execution_time=5.0
            )

        patterns = await learning.analyze_patterns()
        assert "success_rate" in patterns
        assert patterns["success_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get_recommendations(self):
        """Test getting recommendations"""
        learning = LearningSystem(agent_id=1)

        # Record some failures
        for i in range(5):
            await learning.record_execution(
                task_id=i,
                task_type="CODE",
                success=False,
                execution_time=5.0,
                error="Timeout"
            )

        recommendations = await learning.get_recommendations()
        assert len(recommendations) > 0


class TestStatePersistence:
    """Test state persistence"""

    @pytest.mark.asyncio
    async def test_save_and_load_state(self):
        """Test saving and loading state"""
        persistence = StatePersistence(agent_id=1)

        state = {
            "current_task": 1,
            "status": "executing",
            "progress": 50
        }

        await persistence.save_state(state)
        loaded_state = await persistence.load_state()

        assert loaded_state["current_task"] == 1
        assert loaded_state["status"] == "executing"
        assert loaded_state["progress"] == 50

    @pytest.mark.asyncio
    async def test_restore_from_failure(self):
        """Test restoring state after failure"""
        persistence = StatePersistence(agent_id=1)

        # Save state before failure
        state = {
            "current_task": 1,
            "status": "executing",
            "checkpoint": "step_3"
        }
        await persistence.save_state(state)

        # Simulate failure and restore
        restored_state = await persistence.restore()

        assert restored_state["current_task"] == 1
        assert restored_state["checkpoint"] == "step_3"


class TestEndToEnd:
    """End-to-end agent engine tests"""

    @pytest.mark.asyncio
    async def test_complete_task_execution_workflow(self):
        """Test complete task execution workflow"""
        engine = AgentEngine(agent_id=1)

        # 1. Receive task
        task = {
            "id": 1,
            "type": "COMPUTE",
            "description": "Calculate 10 + 20",
            "input_data": "10 + 20",
            "expected_output": "30"
        }

        # 2. Execute task
        result = await engine.execute_task(task)

        # 3. Verify result
        assert result["success"] is True
        assert result["result"] == "30"

        # 4. Check learning system updated
        learning = engine.learning_system
        history = await learning.get_history()
        assert len(history) > 0

        # 5. Check state persisted
        persistence = engine.state_persistence
        state = await persistence.load_state()
        assert state is not None

    @pytest.mark.asyncio
    async def test_task_failure_and_retry(self):
        """Test task failure and retry mechanism"""
        engine = AgentEngine(agent_id=1)

        # Task that will fail
        task = {
            "id": 1,
            "type": "CODE",
            "input_data": "invalid python code {{{",
            "expected_output": "error"
        }

        # Execute with retry
        result = await engine.execute_with_retry(task, max_retries=3)

        # Should fail after retries
        assert result["success"] is False
        assert result["retries"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
