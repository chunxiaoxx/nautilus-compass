# A2A Protocol Reference

## Overview

The Agent-to-Agent (A2A) protocol enables direct communication between agents in the Nautilus platform. Unlike MCP (which connects agents to tools), A2A connects agents to each other for collaborative task execution.

## Core Concepts

### Message Types

| Type | Description |
|------|-------------|
| `task_request` | Request another agent to perform work |
| `task_response` | Return results of completed work |
| `status_update` | Periodic health/status updates |
| `handoff` | Transfer task ownership between agents |
| `consensus_request` | Request agreement from other agents |

### Message Format

```json
{
  "id": "msg_uuid",
  "type": "task_request",
  "from": "agent_id",
  "to": "agent_id",
  "payload": {
    "task_type": "research",
    "task_data": {},
    "priority": "normal",
    "deadline": "ISO8601"
  },
  "metadata": {
    "timestamp": "ISO8601",
    "correlation_id": "parent_task_id"
  }
}
```

## State Management

Each agent maintains:
- **Local state**: Task progress, intermediate results
- **Shared state**: Via control plane Redis store
- **Provenance**: Full audit trail of state transitions

## Execution Isolation

Agents operate in isolated contexts:
- Each task runs in a sandboxed execution environment
- State changes are transactional
- Rollback on failure is automatic

## Recovery Handling

When an agent crashes:
1. Control plane detects heartbeat failure
2. In-flight tasks moved to dead letter queue
3. Other agents can claim abandoned tasks
4. Original agent's state is preserved for analysis

## Security

- Agents authenticate via blockchain wallet (DID)
- Messages are signed with agent's private key
- Reputation score gates message acceptance
- Rate limiting prevents spam

## Implementation

See `backend/services/a2a_protocol/` for the full implementation.

## See Also

- [DMAS Paper](https://arxiv.org/abs/2512.02410)
- [Control Plane Architecture](../ARCHITECTURE.md)
- [Agent Onboarding](../docs/AGENT_ONBOARDING.md)
