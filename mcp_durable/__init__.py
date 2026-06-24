"""mcp_durable · durable MCP transport layer.

Provides a server-side EventStore that tags every outbound message with a
monotonic global id and a bounded (size + ttl) history, so a reconnecting
client can replay exactly what it missed with zero message loss.

Task 1 ships only the pure EventStore — no sockets, no I/O. Real time is
injected (``now_fn``) so the eviction logic stays deterministic under test.
"""
