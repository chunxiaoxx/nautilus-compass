"""
Task routing module for Nautilus multi-agent system.

Provides task complexity evaluation and agent selection logic.
"""

from typing import Dict, List, Optional
from enum import Enum


class TaskComplexity(Enum):
    """Task complexity levels based on Nautilus specification."""
    SIMPLE = "simple"      # D/C level: < 20 hours, no complex keywords
    MEDIUM = "medium"      # B level: 20-40 hours, or 1 complex keyword
    COMPLEX = "complex"    # A/S level: > 40 hours, or 2+ complex keywords


class TaskRouter:
    """
    Routes tasks to appropriate agents based on complexity.

    Routing rules:
    - SIMPLE tasks → OpenClaw (local execution)
    - MEDIUM tasks → Claude Code or OpenClaw (based on load)
    - COMPLEX tasks → Claude Code (required)
    """

    # Complex keywords for task evaluation
    COMPLEX_KEYWORDS = [
        'blockchain', 'smart contract', 'consensus', 'cryptography',
        'distributed', 'multi-agent', 'architecture', 'security',
        'optimization', 'algorithm', 'protocol', 'integration'
    ]

    def __init__(self):
        """Initialize task router."""
        self.routing_history = []

    def evaluate_complexity(
        self,
        task_description: str,
        estimated_hours: float = 0,
        keywords: Optional[List[str]] = None
    ) -> TaskComplexity:
        """
        Evaluate task complexity.

        Args:
            task_description: Task description text
            estimated_hours: Estimated completion time in hours
            keywords: Optional additional complex keywords

        Returns:
            TaskComplexity enum
        """
        description_lower = task_description.lower()

        # Combine default and custom keywords
        all_keywords = self.COMPLEX_KEYWORDS + (keywords or [])

        # Count complex keywords
        complex_count = sum(
            1 for keyword in all_keywords
            if keyword.lower() in description_lower
        )

        # Evaluate based on time and keywords
        if estimated_hours > 40 or complex_count >= 2:
            complexity = TaskComplexity.COMPLEX
        elif estimated_hours > 20 or complex_count >= 1:
            complexity = TaskComplexity.MEDIUM
        else:
            complexity = TaskComplexity.SIMPLE

        # Record routing decision
        self.routing_history.append({
            'description': task_description[:100],
            'estimated_hours': estimated_hours,
            'complex_count': complex_count,
            'complexity': complexity.value
        })

        return complexity

    def select_agent(
        self,
        complexity: TaskComplexity,
        agent_workload: Optional[Dict[str, Dict]] = None
    ) -> str:
        """
        Select appropriate agent based on complexity and workload.

        Args:
            complexity: Task complexity level
            agent_workload: Optional workload information for agents

        Returns:
            Agent name ('openclaw', 'claude_code', etc.)
        """
        if complexity == TaskComplexity.SIMPLE:
            return 'openclaw'

        elif complexity == TaskComplexity.MEDIUM:
            # Check Claude Code availability
            if agent_workload and 'claude_code' in agent_workload:
                claude_info = agent_workload['claude_code']
                current_load = claude_info.get('current_load', 0)
                capacity = claude_info.get('capacity', 10)

                # Use Claude Code if available
                if current_load < capacity:
                    return 'claude_code'

            # Fallback to OpenClaw
            return 'openclaw'

        else:  # COMPLEX
            return 'claude_code'

    def get_routing_statistics(self) -> Dict:
        """
        Get routing statistics.

        Returns:
            Dictionary with routing statistics
        """
        if not self.routing_history:
            return {
                'total_tasks': 0,
                'complexity_distribution': {}
            }

        complexity_counts = {}
        for record in self.routing_history:
            complexity = record['complexity']
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1

        return {
            'total_tasks': len(self.routing_history),
            'complexity_distribution': complexity_counts,
            'avg_complex_keywords': sum(
                r['complex_count'] for r in self.routing_history
            ) / len(self.routing_history)
        }
