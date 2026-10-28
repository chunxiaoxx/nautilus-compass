# A2A Is Not MCP: Protocols Route Messages, Control Planes Schedule Work

Production multi-agent systems often fail for a simple reason: teams confuse **message transport** with **work execution**.

A2A and MCP are useful protocols, but neither one is a scheduler, a state machine, or an isolation boundary. If you treat a protocol as the operating system for agents, you get pretty demos and fragile production behavior.

## The core distinction

A protocol answers questions like:

- How does one agent call another?
- How is capability described?
- What is the message format?
- How are results returned?

A production control plane answers very different questions:

- Which tasks are allowed to run right now?
- What state transition is valid from here?
- Which agent owns the task lease?
- What happens on timeout, retry, or partial failure?
- How do we prevent duplicate execution?
- How do we isolate tools, budgets, and side effects?

These are not the same layer.

## A2A is about routing, not scheduling

A2A is valuable because it gives agents a standard way to communicate with each other. That matters. It improves interoperability, delegation, and capability discovery.

But **routing a request** is not the same as **deciding whether work should execute**.

If Agent A sends Agent B a request, a real system still needs to decide:

1. Is the request authenticated?
2. Does it match a valid task state?
3. Does Agent B have the lease to execute it?
4. Is the execution idempotent?
5. What resource budget applies?
6. Where is the result persisted?
7. What happens if Agent B crashes halfway through?

A protocol packet does not answer those questions. A control plane does.

## MCP is not a workforce manager either

MCP is useful for tool access and structured context exchange. It standardizes how models interact with external tools and data sources.

That still does **not** make it a multi-agent runtime.

MCP can help an agent call tools. It does not, by itself:

- enforce ownership of long-running tasks
- serialize conflicting actions
- arbitrate competing agents
- track durable execution state
- guarantee replay safety
- contain blast radius when tools fail

If you need reliable operations, you still need an execution layer above the protocol layer.

## What production systems actually need

In practice, robust multi-agent systems converge on a control plane with at least four properties.

### 1. Explicit task state

Every task needs a lifecycle such as:

`queued -> leased -> running -> succeeded|failed|expired`

Without explicit state, agents create duplicate work, lose accountability, and overwrite each other.

### 2. Lease-based execution

A task should have a clear executor for a bounded period.

That lease prevents the classic failure mode where two agents both believe they own the same work after a retry storm or network partition.

### 3. Isolation boundaries

Production agents need isolation across:

- tool permissions
- credentials
- runtime sandboxes
- token/cost budgets
- memory scopes
- side effects

Without isolation, “collaboration” becomes shared corruption.

### 4. Auditable transitions

You need receipts:

- who accepted the task
- which tool ran
- what changed
- what output was produced
- why the state transitioned

Otherwise governance becomes storytelling instead of evidence.

## A simple mental model

Use this stack:

### Protocol layer
Handles:
- message format
- capability advertisement
- request/response transport

Examples: A2A, MCP, API contracts

### Control plane
Handles:
- task queueing
- state transitions
- retries
- leases
- policy
- budgets
- observability

Examples: scheduler, orchestrator, workflow engine, execution policy service

### Data plane
Handles:
- actual tool execution
- sandboxed code runs
- file/network side effects
- artifact generation

Confusing these layers is one of the fastest ways to build a system that looks agentic but behaves unreliably.

## Why this matters now

The current agent wave makes it easy to over-focus on protocol compatibility. Compatibility is good, but production reliability comes from **execution discipline**, not just wire format agreement.

If your agents can talk but cannot:

- hold leases
- survive retries
- prove ownership
- isolate failures
- persist state
- emit auditable receipts

then you do not have a production multi-agent system. You have distributed prompt passing.

## Design recommendation

Treat A2A and MCP as interfaces, not as the operating model.

Build a control plane that:

1. validates every incoming request against task state
2. assigns bounded ownership with leases
3. records durable receipts for every side effect
4. enforces isolation across tools and credentials
5. retries safely with idempotent semantics
6. exposes observability for operators and governance

Then use protocols at the edges where they belong.

## Final point

Protocols make agents **interoperable**.

Control planes make agents **operational**.

You need both. But if you have to choose where to be rigorous first, choose the layer that prevents duplicate execution, silent failure, and uncontrolled side effects.

That layer is not the protocol.

It is the control plane.
