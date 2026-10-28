"""
Tests for multi-agent collaboration system.

Tests cover:
- Task complexity evaluation
- Agent selection logic
- Task routing
- Workload tracking
"""

import pytest
from unittest.mock import Mock, patch
from nautilus.agents.router import TaskRouter, TaskComplexity
from nautilus.agents.openclaw import OpenClawCoordinator, TaskComplexity as OpenClawComplexity
from nautilus.agents.claude_code import ClaudeCodeExecutor


class TestTaskRouter:
    """Test TaskRouter complexity evaluation and agent selection."""

    def test_simple_task_evaluation(self):
        """Test simple task complexity evaluation."""
        router = TaskRouter()

        # Simple task: no complex keywords, low hours
        complexity = router.evaluate_complexity(
            "Fix typo in README file",
            estimated_hours=2
        )

        assert complexity == TaskComplexity.SIMPLE

    def test_medium_task_by_hours(self):
        """Test medium complexity by estimated hours."""
        router = TaskRouter()

        # Medium task: 25 hours
        complexity = router.evaluate_complexity(
            "Implement user authentication",
            estimated_hours=25
        )

        assert complexity == TaskComplexity.MEDIUM

    def test_medium_task_by_keyword(self):
        """Test medium complexity by complex keyword."""
        router = TaskRouter()

        # Medium task: 1 complex keyword
        complexity = router.evaluate_complexity(
            "Implement blockchain data storage",
            estimated_hours=10
        )

        assert complexity == TaskComplexity.MEDIUM

    def test_complex_task_by_hours(self):
        """Test complex task by estimated hours."""
        router = TaskRouter()

        # Complex task: > 40 hours
        complexity = router.evaluate_complexity(
            "Build complete authentication system",
            estimated_hours=50
        )

        assert complexity == TaskComplexity.COMPLEX

    def test_complex_task_by_keywords(self):
        """Test complex task by multiple keywords."""
        router = TaskRouter()

        # Complex task: 2+ complex keywords
        complexity = router.evaluate_complexity(
            "Implement distributed consensus protocol with cryptography",
            estimated_hours=15
        )

        assert complexity == TaskComplexity.COMPLEX

    def test_custom_keywords(self):
        """Test custom complex keywords."""
        router = TaskRouter()

        # Add custom keywords
        complexity = router.evaluate_complexity(
            "Implement machine learning model",
            estimated_hours=10,
            keywords=['machine learning', 'neural network']
        )

        assert complexity == TaskComplexity.MEDIUM

    def test_agent_selection_simple(self):
        """Test agent selection for simple tasks."""
        router = TaskRouter()

        agent = router.select_agent(TaskComplexity.SIMPLE)

        assert agent == 'openclaw'

    def test_agent_selection_complex(self):
        """Test agent selection for complex tasks."""
        router = TaskRouter()

        agent = router.select_agent(TaskComplexity.COMPLEX)

        assert agent == 'claude_code'

    def test_agent_selection_medium_with_capacity(self):
        """Test medium task routing with Claude Code capacity."""
        router = TaskRouter()

        # Claude Code has capacity
        workload = {
            'claude_code': {
                'current_load': 3,
                'capacity': 10
            }
        }

        agent = router.select_agent(TaskComplexity.MEDIUM, workload)

        assert agent == 'claude_code'

    def test_agent_selection_medium_no_capacity(self):
        """Test medium task routing when Claude Code is full."""
        router = TaskRouter()

        # Claude Code at capacity
        workload = {
            'claude_code': {
                'current_load': 10,
                'capacity': 10
            }
        }

        agent = router.select_agent(TaskComplexity.MEDIUM, workload)

        assert agent == 'openclaw'

    def test_routing_history(self):
        """Test routing history tracking."""
        router = TaskRouter()

        # Evaluate multiple tasks
        router.evaluate_complexity("Simple task", 5)
        router.evaluate_complexity("Medium task with blockchain", 15)
        router.evaluate_complexity("Complex distributed system", 50)

        stats = router.get_routing_statistics()

        assert stats['total_tasks'] == 3
        assert 'simple' in stats['complexity_distribution']
        assert 'medium' in stats['complexity_distribution']
        assert 'complex' in stats['complexity_distribution']


class TestOpenClawCoordinator:
    """Test OpenClaw coordinator functionality."""

    @patch('nautilus.agents.openclaw.Agent')
    def test_coordinator_initialization(self, mock_agent):
        """Test coordinator initialization."""
        mock_agent.return_value = Mock()
        coordinator = OpenClawCoordinator()

        assert coordinator.agent is not None
        assert len(coordinator.service_agents) == 0
        assert len(coordinator.agent_workload) == 0

    @patch('nautilus.agents.openclaw.Agent')
    @patch('nautilus.agents.claude_code.Agent')
    def test_service_agent_registration(self, mock_claude_agent, mock_openclaw_agent):
        """Test service agent registration."""
        mock_openclaw_agent.return_value = Mock()
        mock_claude_agent.return_value = Mock()

        coordinator = OpenClawCoordinator()
        executor = ClaudeCodeExecutor()

        coordinator.register_service_agent('claude_code', executor.get_agent(), capacity=5)

        assert 'claude_code' in coordinator.service_agents
        assert coordinator.agent_workload['claude_code']['capacity'] == 5
        assert coordinator.agent_workload['claude_code']['current_load'] == 0

    @patch('nautilus.agents.openclaw.Agent')
    def test_complexity_evaluation_simple(self, mock_agent):
        """Test simple task evaluation."""
        mock_agent.return_value = Mock()
        coordinator = OpenClawCoordinator()

        complexity = coordinator.evaluate_complexity("Fix bug in login", 3)

        assert complexity == OpenClawComplexity.SIMPLE

    @patch('nautilus.agents.openclaw.Agent')
    def test_complexity_evaluation_medium(self, mock_agent):
        """Test medium task evaluation."""
        mock_agent.return_value = Mock()
        coordinator = OpenClawCoordinator()

        complexity = coordinator.evaluate_complexity(
            "Implement blockchain storage",
            15
        )

        assert complexity == OpenClawComplexity.MEDIUM

    @patch('nautilus.agents.openclaw.Agent')
    def test_complexity_evaluation_complex(self, mock_agent):
        """Test complex task evaluation."""
        mock_agent.return_value = Mock()
        coordinator = OpenClawCoordinator()

        complexity = coordinator.evaluate_complexity(
            "Build distributed consensus with smart contract integration",
            30
        )

        assert complexity == OpenClawComplexity.COMPLEX

    @patch('nautilus.agents.openclaw.Agent')
    def test_agent_selection_simple_task(self, mock_agent):
        """Test agent selection for simple task."""
        mock_agent.return_value = Mock()
        coordinator = OpenClawCoordinator()

        agent_name = coordinator.select_agent(OpenClawComplexity.SIMPLE)

        assert agent_name == 'openclaw'

    @patch('nautilus.agents.openclaw.Agent')
    @patch('nautilus.agents.claude_code.Agent')
    def test_agent_selection_complex_task(self, mock_claude_agent, mock_openclaw_agent):
        """Test agent selection for complex task."""
        mock_openclaw_agent.return_value = Mock()
        mock_claude_agent.return_value = Mock()

        coordinator = OpenClawCoordinator()
        executor = ClaudeCodeExecutor()
        coordinator.register_service_agent('claude_code', executor.get_agent())

        agent_name = coordinator.select_agent(OpenClawComplexity.COMPLEX)

        assert agent_name == 'claude_code'

    @patch('nautilus.agents.openclaw.Agent')
    def test_agent_selection_complex_no_executor(self, mock_agent):
        """Test complex task without Claude Code registered."""
        mock_agent.return_value = Mock()
        coordinator = OpenClawCoordinator()

        with pytest.raises(ValueError, match="Complex task requires Claude Code"):
            coordinator.select_agent(OpenClawComplexity.COMPLEX)

    @patch('nautilus.agents.openclaw.Agent')
    @patch('nautilus.agents.claude_code.Agent')
    def test_workload_statistics(self, mock_claude_agent, mock_openclaw_agent):
        """Test workload statistics."""
        mock_openclaw_agent.return_value = Mock()
        mock_claude_agent.return_value = Mock()

        coordinator = OpenClawCoordinator()
        executor = ClaudeCodeExecutor()
        coordinator.register_service_agent('claude_code', executor.get_agent())

        # Simulate workload
        coordinator.agent_workload['claude_code']['completed_tasks'] = 5

        stats = coordinator.get_workload_stats()

        assert stats['total_completed'] == 5
        assert 'claude_code' in stats['agents']


class TestClaudeCodeExecutor:
    """Test Claude Code executor functionality."""

    @patch('nautilus.agents.claude_code.Agent')
    def test_executor_initialization(self, mock_agent):
        """Test executor initialization."""
        mock_agent.return_value = Mock()
        executor = ClaudeCodeExecutor()

        assert executor.model == "claude-sonnet-4.5"
        assert executor.agent is not None
        assert executor.completed_tasks == 0

    @patch('nautilus.agents.claude_code.Agent')
    def test_executor_custom_model(self, mock_agent):
        """Test executor with custom model."""
        mock_agent.return_value = Mock()
        executor = ClaudeCodeExecutor(model="claude-opus-4")

        assert executor.model == "claude-opus-4"

    @patch('nautilus.agents.claude_code.Agent')
    def test_record_completion(self, mock_agent):
        """Test task completion recording."""
        mock_agent.return_value = Mock()
        executor = ClaudeCodeExecutor()

        executor.record_completion(10.5)
        executor.record_completion(15.3)

        stats = executor.get_statistics()

        assert stats['completed_tasks'] == 2
        assert stats['total_execution_time'] == 25.8
        assert stats['avg_execution_time'] == 12.9

    @patch('nautilus.agents.claude_code.Agent')
    def test_statistics_no_tasks(self, mock_agent):
        """Test statistics with no completed tasks."""
        mock_agent.return_value = Mock()
        executor = ClaudeCodeExecutor()

        stats = executor.get_statistics()

        assert stats['completed_tasks'] == 0
        assert stats['total_execution_time'] == 0.0
        assert stats['avg_execution_time'] == 0


class TestIntegration:
    """Integration tests for multi-agent system."""

    def test_end_to_end_simple_task(self):
        """Test end-to-end simple task routing."""
        router = TaskRouter()

        # Evaluate task
        complexity = router.evaluate_complexity("Update documentation", 2)

        # Select agent
        agent = router.select_agent(complexity)

        assert complexity == TaskComplexity.SIMPLE
        assert agent == 'openclaw'

    def test_end_to_end_complex_task(self):
        """Test end-to-end complex task routing."""
        router = TaskRouter()

        # Evaluate task
        complexity = router.evaluate_complexity(
            "Implement distributed multi-agent architecture with blockchain",
            45
        )

        # Select agent
        agent = router.select_agent(complexity)

        assert complexity == TaskComplexity.COMPLEX
        assert agent == 'claude_code'

    @patch('nautilus.agents.openclaw.Agent')
    @patch('nautilus.agents.claude_code.Agent')
    def test_coordinator_with_executor(self, mock_claude_agent, mock_openclaw_agent):
        """Test coordinator with registered executor."""
        mock_openclaw_agent.return_value = Mock()
        mock_claude_agent.return_value = Mock()

        coordinator = OpenClawCoordinator()
        executor = ClaudeCodeExecutor()

        # Register executor
        coordinator.register_service_agent('claude_code', executor.get_agent(), capacity=10)

        # Evaluate and route task
        complexity = coordinator.evaluate_complexity(
            "Implement smart contract integration",
            20
        )
        agent_name = coordinator.select_agent(complexity)

        assert complexity == OpenClawComplexity.MEDIUM
        assert agent_name == 'claude_code'
        assert coordinator.agent_workload['claude_code']['current_load'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
