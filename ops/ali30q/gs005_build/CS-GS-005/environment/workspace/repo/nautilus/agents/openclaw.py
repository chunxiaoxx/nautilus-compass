"""
OpenClaw Coordinator Agent for Nautilus project.

Responsibilities:
- Task routing and distribution
- Agent selection based on complexity
- Multi-agent coordination
- Progress monitoring
"""

from crewai import Agent, Task, Crew
from typing import Dict, List, Optional
from enum import Enum


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = "simple"      # D/C level: < 20 hours
    MEDIUM = "medium"      # B level: 20-40 hours
    COMPLEX = "complex"    # A/S level: > 40 hours


class OpenClawCoordinator:
    """
    OpenClaw coordination agent.

    Acts as the central coordinator for multi-agent collaboration,
    routing tasks to appropriate agents based on complexity.
    """

    def __init__(self):
        """Initialize OpenClaw coordinator."""
        self.agent = Agent(
            role='Coordinator',
            goal='Coordinate multi-agent collaboration and task distribution',
            backstory="""OpenClaw is the coordination hub for Nautilus project.
            It analyzes tasks, evaluates complexity, and routes them to the most
            suitable agents. It ensures efficient resource utilization and
            optimal task execution.""",
            verbose=True,
            allow_delegation=True
        )

        # Track registered service agents
        self.service_agents = {}

        # Track agent workload
        self.agent_workload = {}

    def register_service_agent(self, name: str, agent: Agent, capacity: int = 10):
        """
        Register a service agent.

        Args:
            name: Agent name (e.g., 'claude_code', 'manus')
            agent: CrewAI Agent instance
            capacity: Maximum concurrent tasks
        """
        self.service_agents[name] = agent
        self.agent_workload[name] = {
            'capacity': capacity,
            'current_load': 0,
            'completed_tasks': 0
        }

    def evaluate_complexity(self, task_description: str, estimated_hours: float = 0) -> TaskComplexity:
        """
        Evaluate task complexity.

        Criteria:
        - Estimated time
        - Presence of complex keywords
        - Task description length

        Args:
            task_description: Task description text
            estimated_hours: Estimated completion time in hours

        Returns:
            TaskComplexity enum
        """
        description_lower = task_description.lower()

        # Complex keywords
        complex_keywords = [
            'blockchain', 'smart contract', 'consensus', 'cryptography',
            'distributed', 'multi-agent', 'architecture', 'security'
        ]

        # Count complex keywords
        complex_count = sum(1 for keyword in complex_keywords if keyword in description_lower)

        # Evaluate based on time and keywords
        if estimated_hours > 40 or complex_count >= 2:
            return TaskComplexity.COMPLEX
        elif estimated_hours > 20 or complex_count >= 1:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.SIMPLE

    def select_agent(self, complexity: TaskComplexity) -> str:
        """
        Select appropriate agent based on task complexity and workload.

        Routing rules:
        - SIMPLE: OpenClaw (local execution)
        - MEDIUM: Claude Code or OpenClaw (based on load)
        - COMPLEX: Claude Code (may require collaboration)

        Args:
            complexity: Task complexity level

        Returns:
            Agent name
        """
        if complexity == TaskComplexity.SIMPLE:
            # Simple tasks handled by OpenClaw
            return 'openclaw'

        elif complexity == TaskComplexity.MEDIUM:
            # Medium tasks: prefer Claude Code, fallback to OpenClaw
            if 'claude_code' in self.service_agents:
                claude_load = self.agent_workload.get('claude_code', {}).get('current_load', 0)
                claude_capacity = self.agent_workload.get('claude_code', {}).get('capacity', 10)

                if claude_load < claude_capacity:
                    return 'claude_code'

            return 'openclaw'

        else:  # COMPLEX
            # Complex tasks: Claude Code (required)
            if 'claude_code' in self.service_agents:
                return 'claude_code'
            else:
                raise ValueError("Complex task requires Claude Code agent, but it's not registered")

    def distribute_task(
        self,
        task_description: str,
        expected_output: str,
        estimated_hours: float = 0,
        context: Optional[List[str]] = None
    ) -> Dict:
        """
        Distribute task to appropriate agent.

        Args:
            task_description: Task description
            expected_output: Expected output description
            estimated_hours: Estimated completion time
            context: Optional context information

        Returns:
            Dictionary with task result and metadata
        """
        # Evaluate complexity
        complexity = self.evaluate_complexity(task_description, estimated_hours)

        # Select agent
        agent_name = self.select_agent(complexity)

        # Get agent
        if agent_name == 'openclaw':
            agent = self.agent
        else:
            agent = self.service_agents.get(agent_name)
            if not agent:
                raise ValueError(f"Service agent '{agent_name}' not found")

        # Update workload
        if agent_name in self.agent_workload:
            self.agent_workload[agent_name]['current_load'] += 1

        # Create CrewAI task
        crew_task = Task(
            description=task_description,
            agent=agent,
            expected_output=expected_output,
            context=context or []
        )

        # Execute task
        crew = Crew(
            agents=[agent],
            tasks=[crew_task],
            verbose=True
        )

        result = crew.kickoff()

        # Update workload
        if agent_name in self.agent_workload:
            self.agent_workload[agent_name]['current_load'] -= 1
            self.agent_workload[agent_name]['completed_tasks'] += 1

        return {
            'result': result,
            'agent': agent_name,
            'complexity': complexity.value,
            'status': 'completed'
        }

    def get_workload_stats(self) -> Dict:
        """
        Get workload statistics for all agents.

        Returns:
            Dictionary with workload information
        """
        return {
            'agents': self.agent_workload,
            'total_completed': sum(
                agent['completed_tasks']
                for agent in self.agent_workload.values()
            )
        }

    def get_agent(self) -> Agent:
        """Get the CrewAI agent instance."""
        return self.agent
