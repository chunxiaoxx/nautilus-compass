# Nautilus Phase 3 - Agent Engine

Intelligent agent engine for autonomous task execution.

## Features

- ✅ LangGraph-based task orchestration
- ✅ Multi-step task execution workflow
- ✅ Task executors (CODE, DATA, COMPUTE)
- ✅ State persistence (PostgreSQL + Redis)
- ✅ Learning system
- ✅ Concurrent task management
- ✅ Docker sandbox for code execution

## Architecture

```
AgentEngine
├── Core
│   ├── engine.py           # Main orchestration
│   ├── state_persistence.py # State management
│   └── learning.py         # Learning system
├── Executors
│   ├── code_executor.py    # Code tasks
│   ├── data_executor.py    # Data tasks
│   └── compute_executor.py # Compute tasks
└── Tools
    └── (future tools)
```

## Task Execution Workflow

```
1. Evaluate Task
   ↓
2. Plan Execution
   ↓
3. Execute Task
   ↓
4. Verify Result
   ↓
5. Learn from Execution
```

## Executors

### CodeExecutor
- Executes Python code in Docker sandbox
- Resource limits: 512MB RAM, 1 CPU core
- Network isolation
- Timeout protection

### DataExecutor
- JSON schema validation
- Data quality checks
- Missing value detection
- Duplicate detection

### ComputeExecutor
- Mathematical computations
- Numerical simulations
- Result verification with tolerance

## State Persistence

### Redis (Short-term)
- Current task state
- Execution progress
- Temporary data
- TTL: 1-2 hours

### PostgreSQL (Long-term)
- Task history
- Agent statistics
- Learning data
- Permanent storage

## Learning System

Learns from:
- ✅ Successful executions
- ✅ Failed executions
- ✅ Performance metrics
- ✅ Verification feedback

Improves:
- ✅ Execution strategies
- ✅ Timeout adjustments
- ✅ Retry policies
- ✅ Task preferences

## Usage

### Initialize Agent

```python
from core.engine import AgentEngine

# Create agent engine
engine = AgentEngine(agent_id=1, max_concurrent_tasks=3)

# Execute task
task_data = {
    "task_id": 123,
    "task_type": "CODE",
    "description": "Write a function to calculate fibonacci",
    "input_data": "def fibonacci(n): pass",
    "expected_output": "fibonacci(10) == 55"
}

result = await engine.execute_task(task_data)
```

### Check Agent Status

```python
status = await engine.get_status()
print(status)
# {
#     "agent_id": 1,
#     "current_tasks": 2,
#     "max_concurrent_tasks": 3,
#     "available_capacity": 1
# }
```

### Get Performance Metrics

```python
from core.learning import LearningSystem
from core.state_persistence import StatePersistence

persistence = StatePersistence()
learning = LearningSystem(agent_id=1, persistence=persistence)

metrics = await learning.get_performance_metrics()
print(metrics)
# {
#     "total_tasks": 100,
#     "successful_tasks": 85,
#     "failed_tasks": 15,
#     "success_rate": 0.85,
#     "average_execution_time": 45.2
# }
```

## Configuration

Environment variables:
- `REDIS_URL`: Redis connection URL
- `DATABASE_URL`: PostgreSQL connection URL
- `DOCKER_HOST`: Docker daemon URL (optional)

## Dependencies

```bash
pip install langchain langgraph docker redis pandas jsonschema numpy
```

## Testing

```bash
pytest tests/test_agent_engine.py -v
```

## Security

- ✅ Docker sandbox isolation
- ✅ Resource limits (CPU, memory)
- ✅ Network isolation
- ✅ Timeout protection
- ✅ Safe expression evaluation

## Performance

- Concurrent tasks: 3 per agent (configurable)
- Code execution timeout: 5 minutes
- State sync interval: 5 minutes
- Learning data retention: 100 executions

## Future Enhancements

- [ ] Multi-agent collaboration (Phase 4)
- [ ] Self-improvement (Phase 4)
- [ ] Real-world tool integration (Phase 4)
- [ ] Advanced learning algorithms
- [ ] GPU support for ML tasks

## License

MIT
