# A2A vs MCP vs Control Plane

> Why these three are different and why it matters for multi-agent systems.

## TL;DR

| Layer | Question It Answers | Example |
|-------|---------------------|---------|
| **A2A Protocol** | "Agent 们，你们怎么对话？" | "Can you review this PR?" |
| **MCP** | "LLM，你怎么调用工具？" | `tools/call: github_create_issue` |
| **Control Plane** | "谁来决定做什么，什么时候做？" | Task scheduling, state consistency |

## A2A Protocol: Message Routing Between Agents

A2A (Agent-to-Agent) is a **message routing layer**. It handles how agents communicate with each other.

```
[Agent A] --A2A Message--> [Relay/Hub] --A2A Message--> [Agent B]
```

### What A2A Does

- Formats and serializes messages between agents
- Routes messages to the correct recipient agent
- Passes metadata (priority, deadline, reply channel)
- Propagates errors

### What A2A Does NOT Do

- **Does NOT** schedule tasks (that's the Control Plane)
- **Does NOT** maintain global state (that's the State Store)
- **Does NOT** execute tools (that's the agent's runtime)

### Correct Usage

```python
# ✅ A2A: Two agents coordinating
orchestrator.send_a2a(
    target="reviewer-agent",
    message="Please review PR #42. Link: github.com/.../42"
)

# ❌ NOT A2A: Tool invocation
# Wrong: using A2A to call GitHub API
```

## MCP: Tool Invocation for LLMs

MCP (Model Context Protocol) connects LLMs to external tools and data sources.

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "github_create_issue",
    "arguments": {"title": "Bug found", "body": "..."}
  }
}
```

MCP lets an LLM know:
- What tools are available
- How to call them
- What format responses come back in

### MCP Does NOT Handle

- Multi-agent coordination
- Task scheduling across agents
- State consistency between agents

## Control Plane: The Orchestrator

The Control Plane makes **scheduling decisions** and ensures **state consistency**.

### Core Responsibilities

1. **Task Scheduling**: Assigns unique task IDs, selects the right agent based on capability + load
2. **State Isolation**: Each agent has its own state, changes are transactional
3. **Execution Boundaries**: Handles timeouts, retries, and failure recovery

### Example: Control Plane Dispatch

```python
class ControlPlane:
    def dispatch(self, task: Task, agent_pool: List[Agent]) -> DispatchResult:
        # 1. Allocate unique task ID
        task_id = self._allocate_task_id(task)
        
        # 2. Select agent based on requirements + current load
        agent = self._select_agent(agent_pool, task.requirements)
        
        # 3. Register in state store
        self.state_store.register_task(task_id, agent.id)
        
        # 4. Send to agent
        agent.receive(TaskMessage(task_id=task_id, payload=task.payload))
        
        return DispatchResult(task_id=task_id, agent_id=agent.id)
    
    def handle_timeout(self, task_id: str) -> None:
        """Handle task timeout with retry or failure marking"""
        task = self.state_store.get_task(task_id)
        if task.retry_count < MAX_RETRIES:
            self._retry_task(task)
        else:
            self.state_store.mark_failed(task_id)
            self._notify_dependents(task_id)
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  Control Plane                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────┐  │
│  │ Task Sched. │    │ State Store │    │ Auth    │  │
│  └─────────────┘    └─────────────┘    └─────────┘  │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                    A2A Layer                        │
│         (message routing, not execution)            │
└─────────────────────────────────────────────────────┘
          │                           │
          ▼                           ▼
    ┌──────────┐               ┌──────────┐
    │ Agent A  │               │ Agent B  │
    │ (Review) │               │ (Coding) │
    └──────────┘               └──────────┘
          │                           │
          ▼                           ▼
    ┌──────────────────────────────────────────┐
    │              MCP Layer                    │
    │  (tool invocation, context injection)    │
    └──────────────────────────────────────────┘
          │         │         │         │
          ▼         ▼         ▼         ▼
      GitHub    Slack    Database   Filesystem
```

## Without Control Plane: What Happens

```
[User] → "Analyze this PR"
  │
  ├─→ [Reviewer Agent] → Starts analyzing...
  ├─→ [Coder Agent]   → Also starts analyzing... (duplicate work!)
  └─→ [Docs Agent]     → Waiting for results... (never notified)
```

**Result**: Reviewer and Coder did the same work. Docs never got notified. System is inconsistent.

## With Control Plane: What Happens

```
[User] → "Analyze this PR"
  │
  └─→ [Control Plane]
        │
        ├─→ Task #101 → Reviewer Agent
        ├─→ Task #102 → Coder Agent (different scope)
        └─→ Task #103 → Docs Agent (after #101 completes)
```

**Result**: Each agent has a unique, non-overlapping task. Dependencies are respected.

## Common Misconceptions

### "We use A2A to call tools"
No. A2A routes messages between agents. Use MCP or native tool invocation for tool calls.

### "Control Plane replaces A2A"
No. Control Plane makes decisions, A2A carries messages. They're complementary.

### "MCP handles multi-agent coordination"
No. MCP is for LLM-to-tool communication. Multi-agent coordination needs A2A + Control Plane.

## Summary

| Layer | Protocol | Responsibility | Doesn't Do |
|-------|----------|---------------|------------|
| **Control Plane** | Custom/Internal | Scheduling, state, retries | Message transport |
| **A2A** | A2A Protocol | Agent-to-agent messages | Tool calls, scheduling |
| **MCP** | MCP | LLM → Tools | Agent coordination |

**Three problems, three solutions. Don't mix them.**
