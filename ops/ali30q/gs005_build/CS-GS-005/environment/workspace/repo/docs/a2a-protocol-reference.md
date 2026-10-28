# A2A Is Not MCP: Why Production Multi-Agent Systems Need a Control Plane

## A2A vs MCP vs Control Plane

If you're building multi-agent systems in production, agent messaging, tool access, and execution orchestration are **not the same layer**.

| Protocol | Answers |
|----------|---------|
| A2A | Who talks to whom |
| MCP | How tools are exposed to an agent |
| Control Plane | What runs, where it runs, what happens when it fails, and how state is enforced |

---

## Why A2A Is Not Enough

A2A is a messaging protocol, not an execution runtime. It does not:
- Decide worker placement
- Persist task state
- Deduplicate retries
- Enforce multi-tenant execution boundaries

A system with only A2A is a **mailbox network**. It is not yet an operating system for agents.

## Why MCP Is Not Enough

MCP is excellent for standardized tool access. But MCP does not solve:
- Distributed task ownership
- Runtime recovery
- Scheduling
- Control-plane policy

A tool protocol is **not a scheduler**.

---

## What the Control Plane Must Do

1. **Task lifecycle management** — explicit state machine for every task
2. **Persistent state and execution logs** — survive scheduler restarts
3. **Isolation between agents, tenants, and workloads** — no cross-contamination
4. **Retries, backoff, and deduplication** — graceful degradation
5. **Observability and tracing** — know what ran, when, and why
6. **Policy enforcement and governance** — who can do what and when

---

## A More Stable Three-Layer Architecture

### 1. Gateway / Control Plane
- State machine transitions
- A2A message routing and authentication
- Task dispatch and event logging
- **Should NOT** directly run shell, Python, or modify core files

### 2. Logic Nodes
- Task decomposition
- Plan review and dependency analysis
- Best for planning-type agents (KAIROS)

### 3. Execution Nodes
- Code generation and tool invocation
- File mutation and fast verification
- Best for high-frequency execution agents (MiniMax)

---

## Execution Isolation Is Non-Negotiable

The real risk: **agents executing failures at speed**.

Without isolation:
1. Agent generates problematic code
2. System binds execution to main process
3. One bad execution pollutes global state

With isolation:
- Worker node crash ≠ system crash
- Failed tool call ≠ control plane failure
- Bad output can be audited, retried, rolled back

---

## Architecture: Nautilus Control Plane

### A. Single-Threaded Master Loop
- Control plane runs in safe single-threaded event loop
- All input becomes Event, uniformly queued
- All state changes go through same state machine path

### B. Bridge Mode & Worker Nodes
- Dangerous actions dispatched to isolated Worker Nodes
- Control Plane only dispatches, never executes
- Worker failures return structured error to control plane

### C. A2A Neural Hub
- KAIROS: logic node for task decomposition and plan review
- MiniMax: execution node for code generation and tool invocation
- Control Plane: routes standardized JSON protocol between them

---

## Engineering Checklist

1. **Separate concerns first** — protocol, scheduling, execution
2. **Establish state machine** — every task has explicit lifecycle
3. **Implement execution isolation** — high-risk actions in Worker/Sandbox
4. **Add observability** — log events, failures, results
5. **Then expand capabilities** — without control plane, expansion amplifies failures

---

## The Production Test

If your system has any of these:
- "Execute tool in main process upon message receipt"
- "Protocol handles routing + scheduling + execution + rollback"
- "Bad agent output corrupts global state"

**You don't have a production multi-agent architecture.**

Real production systems must answer:
1. **How are messages routed?** → A2A
2. **How are tasks scheduled?** → Control Plane
3. **How is execution isolated?** → Control Plane

Three distinct problems. Three distinct solutions. Protocol convergence ≠ architectural maturity.