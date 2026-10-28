# A2A Protocol Implementation Guide

## Overview

This document covers A2A (Agent-to-Agent) protocol implementation patterns for Nautilus platform agents. A2A handles inter-agent communication, task delegation, and coordination — but NOT task scheduling or execution isolation.

## Core A2A Concepts

### What A2A IS
- Message routing between agents
- Payload exchange for task delegation
- Coordination acknowledgments
- State synchronization across nodes

### What A2A is NOT
- Task scheduling (use platform task queue)
- Execution isolation (use control plane)
- State enforcement (use Raft/consensus)
- Context management (use MCP)

## Message Format

```json
{
  "task_id": "self_abc123",
  "source_agent": "nautilus",
  "target_agent": "kairos",
  "action": "delegate|acknowledge|sync|report",
  "payload": {...},
  "timestamp": "ISO-8601",
  "signature": "agent_wallet_signature"
}
```

## Verified Patterns

### 1. Task Delegation
```
Agent A                    Agent B
   |--- delegate(task) ----->|
   |<-- acknowledge() -------|
   |--- get_result() -------->|
   |<-- result(payload) ------|
```

### 2. Parallel Coordination
```
                    [Orchestrator]
                    /     |     \
               task1   task2   task3
                  \     |     /
                   aggregate() -> combined_result
```

### 3. Acknowledgment Flow
Every A2A message should receive an acknowledgment. If no ack within timeout:
- Retry with exponential backoff (max 3 retries)
- Log failure for audit
- Escalate to control plane if persistent

## Security Considerations

1. **Wallet as DID**: Agent identity is their wallet address
2. **Message Signing**: All inter-agent messages should be cryptographically signed
3. **Payload Validation**: Verify schema before processing
4. **Replay Protection**: Include monotonic counters or timestamps

## Failure Modes

| Failure | Detection | Recovery |
|---------|-----------|----------|
| No acknowledgment | Timeout | Retry + escalate |
| Invalid payload | Schema validation | Reject + report |
| Agent unreachable | Health check | Reassign task |
| State divergence | Version vectors | Full sync |

## Implementation Status

- ✅ Basic message routing
- ✅ Acknowledgment protocol
- ✅ Task delegation
- 🔄 Parallel task aggregation
- 🔄 Cross-region sync
- ⬜ Formal state machine

## References

- DMAS Paper: arXiv:2512.02410
- Nautilus Architecture: ARCHITECTURE.md
- Self-Bootstrap Demo: docs/SELF_BOOTSTRAP_DEMO.md
