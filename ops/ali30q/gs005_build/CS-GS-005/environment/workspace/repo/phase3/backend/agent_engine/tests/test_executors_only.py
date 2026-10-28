"""
Simplified executor tests - testing executors independently
"""

import pytest
import asyncio
from executors.code_executor import CodeExecutor
from executors.data_executor import DataExecutor
from executors.compute_executor import ComputeExecutor


class TestCodeExecutor:
    """Test code executor with Docker sandbox"""

    @pytest.mark.asyncio
    async def test_docker_client_initialization(self):
        """Test Docker client initialization"""
        executor = CodeExecutor()
        assert executor.docker_client is not None, "Docker client should be initialized"


class TestDataExecutor:
    """Test data executor"""

    @pytest.mark.asyncio
    async def test_validate_schema_valid(self):
        """Test JSON schema validation with valid data"""
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
        result = await executor.validate_schema(data, schema)
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_schema_invalid(self):
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
        result = await executor.validate_schema(data, schema)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_data_quality(self):
        """Test data quality analysis"""
        executor = DataExecutor()
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": None},
            {"name": "Bob", "age": 25}
        ]
        result = await executor.check_data_quality(data)
        assert result["total_records"] == 3
        assert result["missing_values"] > 0


class TestComputeExecutor:
    """Test compute executor"""

    @pytest.mark.asyncio
    async def test_compute_simple_expression(self):
        """Test simple mathematical expression"""
        executor = ComputeExecutor()
        result = await executor.compute("2 + 2")
        assert result == 4.0

    @pytest.mark.asyncio
    async def test_compute_complex_expression(self):
        """Test complex expression"""
        executor = ComputeExecutor()
        result = await executor.compute("(10 + 5) * 2 - 8")
        assert result == 22.0

    @pytest.mark.asyncio
    async def test_compute_with_functions(self):
        """Test expression with math functions"""
        executor = ComputeExecutor()
        result = await executor.compute("sqrt(16) + pow(2, 3)")
        assert result == 12.0

    @pytest.mark.asyncio
    async def test_verify_result(self):
        """Test result verification"""
        executor = ComputeExecutor()
        # Within tolerance
        assert await executor.verify_result(10.0, 10.05, tolerance=0.01) is True
        # Outside tolerance
        assert await executor.verify_result(10.0, 11.0, tolerance=0.01) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
