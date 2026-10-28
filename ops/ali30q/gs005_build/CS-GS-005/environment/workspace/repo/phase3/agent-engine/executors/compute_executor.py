"""
Compute Executor - Executes computational tasks.
"""
import math
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ComputeExecutor:
    """
    Execute computational tasks.

    Supports:
    - Mathematical computations
    - Numerical simulations
    - Result verification
    """

    def __init__(self):
        """Initialize compute executor."""
        logger.info("ComputeExecutor initialized")

    async def execute(self, state) -> str:
        """
        Execute compute task.

        Args:
            state: Agent state with task information

        Returns:
            Execution result
        """
        logger.info(f"Executing compute task {state.task_id}")

        # Parse input
        try:
            # Assume input is a mathematical expression or computation request
            input_data = state.input_data

            # Execute computation
            result = await self.compute(input_data)

            # Verify result if expected output is provided
            if state.expected_output:
                expected = float(state.expected_output)
                actual = float(result)
                relative_error = abs(actual - expected) / abs(expected) if expected != 0 else abs(actual)

                if relative_error < 0.01:  # 1% tolerance
                    logger.info(f"Result verified: {actual} ≈ {expected}")
                else:
                    logger.warning(f"Result mismatch: {actual} vs {expected} (error: {relative_error:.2%})")

            return str(result)

        except Exception as e:
            logger.error(f"Computation failed: {e}")
            raise RuntimeError(f"Computation failed: {str(e)}")

    async def compute(self, expression: str) -> float:
        """
        Compute mathematical expression.

        Args:
            expression: Mathematical expression

        Returns:
            Computation result
        """
        # Safe evaluation of mathematical expressions
        # Only allow math functions and numpy
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
            "np": np
        }

        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return float(result)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")

    async def verify_result(self, actual: float, expected: float, tolerance: float = 0.01) -> bool:
        """
        Verify computation result.

        Args:
            actual: Actual result
            expected: Expected result
            tolerance: Relative error tolerance

        Returns:
            True if result is within tolerance
        """
        if expected == 0:
            return abs(actual) < tolerance
        else:
            relative_error = abs(actual - expected) / abs(expected)
            return relative_error < tolerance
