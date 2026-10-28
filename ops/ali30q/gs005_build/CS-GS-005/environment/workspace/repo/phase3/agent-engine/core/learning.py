"""
Learning system for agent improvement.
"""
from typing import Dict, List, Any
from datetime import datetime
import json
import logging

from core.state_persistence import StatePersistence

logger = logging.getLogger(__name__)


class LearningSystem:
    """
    Agent learning system.

    Learns from:
    - Successful task executions
    - Failed task executions
    - Verification feedback
    - Performance metrics
    """

    def __init__(self, agent_id: int, persistence: StatePersistence):
        """
        Initialize learning system.

        Args:
            agent_id: Agent ID
            persistence: State persistence manager
        """
        self.agent_id = agent_id
        self.persistence = persistence
        logger.info(f"LearningSystem initialized for agent {agent_id}")

    async def record_execution(self, task_id: int, execution_data: Dict[str, Any]):
        """
        Record task execution for learning.

        Args:
            task_id: Task ID
            execution_data: Execution data including result, logs, metrics
        """
        logger.info(f"Recording execution for task {task_id}")

        # Create execution record
        record = {
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "task_type": execution_data.get("task_type"),
            "success": execution_data.get("success", False),
            "execution_time": execution_data.get("execution_time"),
            "error": execution_data.get("error"),
            "logs": execution_data.get("logs", [])
        }

        # Save to Redis
        key = f"agent:{self.agent_id}:learning:executions"
        self.persistence.redis_client.lpush(key, json.dumps(record))
        self.persistence.redis_client.ltrim(key, 0, 99)  # Keep last 100 executions

        # Analyze and learn
        await self.analyze_execution(record)

    async def analyze_execution(self, record: Dict[str, Any]):
        """
        Analyze execution record and extract learnings.

        Args:
            record: Execution record
        """
        if record["success"]:
            await self._learn_from_success(record)
        else:
            await self._learn_from_failure(record)

    async def _learn_from_success(self, record: Dict[str, Any]):
        """
        Learn from successful execution.

        Args:
            record: Execution record
        """
        logger.info(f"Learning from successful task {record['task_id']}")

        # Extract successful patterns
        pattern = {
            "task_type": record["task_type"],
            "execution_time": record["execution_time"],
            "timestamp": record["timestamp"]
        }

        # Save pattern
        key = f"agent:{self.agent_id}:learning:success_patterns"
        self.persistence.redis_client.lpush(key, json.dumps(pattern))
        self.persistence.redis_client.ltrim(key, 0, 49)  # Keep last 50 patterns

    async def _learn_from_failure(self, record: Dict[str, Any]):
        """
        Learn from failed execution.

        Args:
            record: Execution record
        """
        logger.info(f"Learning from failed task {record['task_id']}")

        # Analyze failure reason
        failure_analysis = {
            "task_type": record["task_type"],
            "error": record["error"],
            "timestamp": record["timestamp"],
            "logs": record["logs"][-10:]  # Last 10 log entries
        }

        # Save failure analysis
        key = f"agent:{self.agent_id}:learning:failure_analysis"
        self.persistence.redis_client.lpush(key, json.dumps(failure_analysis))
        self.persistence.redis_client.ltrim(key, 0, 49)  # Keep last 50 failures

        # Update strategy based on failure
        await self._update_strategy(failure_analysis)

    async def _update_strategy(self, failure_analysis: Dict[str, Any]):
        """
        Update execution strategy based on failure analysis.

        Args:
            failure_analysis: Failure analysis data
        """
        logger.info("Updating execution strategy")

        # Get current strategy
        key = f"agent:{self.agent_id}:learning:strategy"
        strategy_json = self.persistence.redis_client.get(key)

        if strategy_json:
            strategy = json.loads(strategy_json)
        else:
            strategy = {
                "task_type_preferences": {},
                "timeout_adjustments": {},
                "retry_strategies": {}
            }

        # Adjust strategy based on failure
        task_type = failure_analysis["task_type"]

        # Increase timeout for this task type
        if task_type not in strategy["timeout_adjustments"]:
            strategy["timeout_adjustments"][task_type] = 1.0

        strategy["timeout_adjustments"][task_type] *= 1.2  # Increase by 20%

        # Save updated strategy
        self.persistence.redis_client.set(key, json.dumps(strategy))

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.

        Returns:
            Performance metrics
        """
        # Get execution records
        key = f"agent:{self.agent_id}:learning:executions"
        records_json = self.persistence.redis_client.lrange(key, 0, -1)

        records = [json.loads(r) for r in records_json]

        if not records:
            return {
                "total_tasks": 0,
                "success_rate": 0,
                "average_execution_time": 0
            }

        # Calculate metrics
        total_tasks = len(records)
        successful_tasks = sum(1 for r in records if r["success"])
        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0

        execution_times = [r["execution_time"] for r in records if r.get("execution_time")]
        average_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        return {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": total_tasks - successful_tasks,
            "success_rate": success_rate,
            "average_execution_time": average_execution_time
        }

    async def get_recommendations(self) -> List[str]:
        """
        Get recommendations for improvement.

        Returns:
            List of recommendations
        """
        metrics = await self.get_performance_metrics()
        recommendations = []

        # Analyze success rate
        if metrics["success_rate"] < 0.7:
            recommendations.append("Success rate is below 70%. Consider reviewing failed tasks and updating strategies.")

        # Analyze execution time
        if metrics["average_execution_time"] > 300:  # 5 minutes
            recommendations.append("Average execution time is high. Consider optimizing task execution.")

        # Get failure patterns
        key = f"agent:{self.agent_id}:learning:failure_analysis"
        failures_json = self.persistence.redis_client.lrange(key, 0, 9)  # Last 10 failures

        if len(failures_json) > 5:
            recommendations.append("Multiple recent failures detected. Review error logs and adjust strategies.")

        return recommendations
