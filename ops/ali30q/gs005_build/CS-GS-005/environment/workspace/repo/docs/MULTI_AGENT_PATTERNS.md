# Multi-Agent Coordination Patterns

> Practical patterns for building reliable multi-agent systems.

## Pattern 1: Orchestrator-Worker

One agent coordinates, others execute.

```
┌────────────────────────────────────────────────────┐
│                  Orchestrator                       │
│  - Decides task decomposition                       │
│  - Assigns subtasks to workers                     │
│  - Aggregates results                              │
│  - Handles failures                                 │
└────────────────────────────────────────────────────┘
        │              │              │
        ▼              ▼              ▼
   ┌────────┐    ┌────────┐    ┌────────┐
   │Worker A│    │Worker B│    │Worker C│
   └────────┘    └────────┘    └────────┘
```

**Use when**: Task can be cleanly decomposed into independent subtasks.

**Example**: 
- Orchestrator: "Split this PR review into code review, test coverage, docs review"
- Workers: Do each piece in parallel
- Orchestrator: Combine findings, write summary

**Nautilus implementation**: `nautilus-agent/gateway/scheduler.py` handles task dispatch.

## Pattern 2: Supervisor Chain

Agents pass work along a chain; each handles what it can.

```
┌────────┐     ┌────────┐     ┌────────┐     ┌────────┐
│ Entry  │────▶│Review A│────▶│Review B│────▶│ Exit   │
└────────┘     └────────┘     └────────┘     └────────┘
                     │              │
                     ▼              ▼
               [can handle]    [pass up]
```

**Use when**: Different agents have different specializations, and you want fallback.

**Example**:
- Entry Agent: Receives user request, does initial classification
- Review A: Checks code style (can handle most issues)
- Review B: Checks security (if Review A couldn't handle)
- Exit: Returns result or escalation

## Pattern 3: RAID-3 Consensus

Three agents analyze independently, judge picks the best.

```
         ┌─────────────────────────────────────┐
         │              Judge                   │
         │  (selects best analysis + reasoning)│
         └─────────────────────────────────────┘
              ▲          ▲          ▲
              │          │          │
         ┌────────┐ ┌────────┐ ┌────────┐
         │Analyst │ │Analyst │ │Analyst │
         │   1    │ │   2    │ │   3    │
         └────────┘ └────────┘ └────────┘
              │          │          │
              └──────────┼──────────┘
                         ▼
              [Same input, parallel analysis]
```

**Use when**: You need high confidence in analysis before taking action.

**Nautilus implementation**: `raid_engine` in the platform handles RAID-1 through RAID-5 consensus levels.

## Pattern 4: Message Bus (Pub/Sub)

Agents communicate via topics, not direct messages.

```
┌──────────────────────────────────────────────────────┐
│                    Message Bus                       │
│                                                      │
│   topics:                                            │
│   ├─ platform.events                                 │
│   ├─ task.created                                   │
│   ├─ agent.status                                   │
│   └─ anomaly.detected                               │
└──────────────────────────────────────────────────────┘
     ▲          ▲          ▲          ▲
     │          │          │          │
  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
  │Agent │  │Agent │  │Agent │  │Agent │
  │  1   │  │  2   │  │  3   │  │  4   │
  └──────┘  └──────┘  └──────┘  └──────┘
```

**Use when**: Loose coupling needed, agents join/leave dynamically.

**Example**: 
- Anomaly detector publishes to `anomaly.detected`
- Any interested agent subscribes and reacts
- No direct coupling between detector and reaction agents

## Pattern 5: Hierarchical Planning

High-level planner breaks down goals, lower-level executors handle details.

```
┌─────────────────────────────────────────────────────────┐
│                    Strategic Planner                    │
│  "Achieve Q4 revenue target of $1M"                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Tactical Planners                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Sales Planner │  │Ops Planner   │  │Mktg Planner  │  │
│  │"$500K from   │  │"Optimize      │  │"$200K from   │  │
│  │ existing     │  │ fulfillment"  │  │ campaigns"   │  │
│  │ customers"    │  │              │  │              │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Executors                             │
│  (Individual agents executing specific tasks)           │
└─────────────────────────────────────────────────────────┘
```

**Use when**: Complex goals requiring multi-level decomposition.

## Failure Handling

### Timeout Strategy

```python
class AgentTask:
    def __init__(self, agent_id: str, task_id: str):
        self.agent_id = agent_id
        self.task_id = task_id
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.max_retries = 3
        self.timeout_seconds = 30
    
    def handle_timeout(self):
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = TaskStatus.RETRYING
            # Re-dispatch to same or different agent
        else:
            self.status = TaskStatus.FAILED
            # Notify dependent tasks
```

### Dead Letter Queue

Tasks that fail after max retries go to DLQ for manual review.

```
Task fails → Retry (max 3) → Still fails → DLQ
                                              │
                                              ▼
                                    [Human review / Alert]
```

## Anti-Patterns to Avoid

### ❌ No Control Plane (Chaos)

```
All agents see all tasks
Agents fight over same task
No one knows who owns what
Result: Duplicate work, inconsistent state
```

### ❌ Too Much Centralization (Bottleneck)

```
One agent does everything
Single point of failure
Scales poorly
Result: System dies when central agent fails
```

### ❌ Tight Coupling

```
Agent A directly calls Agent B
B directly calls C
C directly calls A
Result: Any change cascades everywhere
```

## Choosing a Pattern

| Scenario | Best Pattern |
|----------|--------------|
| Independent parallel tasks | Orchestrator-Worker |
| Specialized handlers with fallback | Supervisor Chain |
| High-stakes decision requiring consensus | RAID-3 |
| Dynamic, loosely coupled system | Message Bus |
| Complex hierarchical goals | Hierarchical Planning |
| Most production systems | Combination of above |

## Nautilus Platform Support

- **Orchestrator-Worker**: Handled by `scheduler.py` + A2A protocol
- **Supervisor Chain**: Implemented in `task_router.py`
- **RAID-3**: Full implementation in `raid_engine`
- **Message Bus**: Via Redis pub/sub in `event_bus`
- **Hierarchical**: Via `proposal_intelligence` layer

See also: [docs/A2A_VS_MCP.md](A2A_VS_MCP.md) for protocol layer details.
