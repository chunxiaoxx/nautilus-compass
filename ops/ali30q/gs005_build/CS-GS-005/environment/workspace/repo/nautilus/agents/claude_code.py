"""
Claude Code Executor Agent for Nautilus project.

Responsibilities:
- Execute complex tasks
- Generate high-quality code
- Perform testing and validation
"""

from crewai import Agent
from typing import Optional


class ClaudeCodeExecutor:
    """
    Claude Code execution agent.

    Handles complex task execution including:
    - Code implementation
    - Testing and validation
    - Documentation generation
    """

    def __init__(self, model: str = "claude-sonnet-4.5"):
        """
        Initialize Claude Code executor.

        Args:
            model: Model identifier (default: claude-sonnet-4.5)
        """
        self.model = model

        self.agent = Agent(
            role='Executor',
            goal='Execute tasks and generate high-quality results',
            backstory="""Claude Code is a powerful executor agent for Nautilus project.
            It specializes in complex task execution, code implementation, and
            technical problem-solving. It produces high-quality, well-tested code
            with comprehensive documentation.""",
            verbose=True,
            allow_delegation=False  # Executor doesn't delegate
        )

        self.completed_tasks = 0
        self.total_execution_time = 0.0

    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        return self.agent

    def get_statistics(self) -> dict:
        """
        Get execution statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'completed_tasks': self.completed_tasks,
            'total_execution_time': self.total_execution_time,
            'avg_execution_time': (
                self.total_execution_time / self.completed_tasks
                if self.completed_tasks > 0 else 0
            )
        }

    def record_completion(self, execution_time: float):
        """
        Record task completion.

        Args:
            execution_time: Time taken to execute task (seconds)
        """
        self.completed_tasks += 1
        self.total_execution_time += execution_time
