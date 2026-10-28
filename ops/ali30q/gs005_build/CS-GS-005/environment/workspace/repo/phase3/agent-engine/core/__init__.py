"""Core agent engine modules."""
from .engine import AgentEngine, AgentState

# Lazy imports to avoid circular dependency with backend models
try:
    from .learning import LearningSystem
    from .state_persistence import StatePersistence
    __all__ = ['AgentEngine', 'AgentState', 'LearningSystem', 'StatePersistence']
except ImportError:
    __all__ = ['AgentEngine', 'AgentState']
