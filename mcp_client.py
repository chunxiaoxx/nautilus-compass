"""MCP JSON-RPC client with automatic reconnect · v1.0 (Task #46).

For long-lived A2A sessions where the TCP link may drop (server restart,
network blip, idle timeout). Caller never sees the reconnect — a call
just takes longer.

Usage:

    from mcp_client import MCPClient
    with MCPClient(host="127.0.0.1", port=8766, token="...") as c:
        tools = c.list_tools()
        result = c.call_tool("recall", {"query": "last auth change", "top_k": 5})
        # Server restart? Next call transparently reconnects.
        result = c.call_tool("drift_check", {"prompt": "..."})

Reconnect policy:
  - Triggered by ConnectionResetError, BrokenPipeError, socket.timeout, OSError
    on send or recv.
  - Exponential backoff: 0.1s, 0.2s, 0.4s, ... capped at `backoff_max_s`.
  - Gives up after `max_retries` consecutive failures and raises the last error.
  - After a successful reconnect, re-runs `initialize` with the same token before
    replaying the caller's request.

Not thread-safe · one client per thread. The server's TCP loop is
per-connection-threaded, so parallel callers should each hold their own
MCPClient.
"""
from __future__ import annotations

import json
import re
import socket
import time


class MCPClientError(RuntimeError):
    """Raised when the server returns a JSON-RPC error or we exhaust reconnects."""
    pass


_RETRY_RE = re.compile(r"retry in\s*([0-9]+(?:\.[0-9]+)?)\s*s", re.IGNORECASE)


def _parse_retry_after(msg: str, default: float = 1.0) -> float:
    """Extract `X.Ys` from the server's -32029 message. Fallback to 1s."""
    m = _RETRY_RE.search(msg or "")
    if not m:
        return default
    try:
        return max(0.0, float(m.group(1)))
    except ValueError:
        return default


class MCPClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8766,
        token: str | None = None,
        *,
        connect_timeout_s: float = 3.0,
        call_timeout_s: float = 10.0,
        max_retries: int = 5,
        backoff_base_s: float = 0.1,
        backoff_max_s: float = 2.0,
        rate_limit_retries: int = 0,
        rate_limit_multiplier: float = 1.5,
        tls: bool = False,
        tls_verify: bool = True,
        tls_ca_cert: str | None = None,
        tls_client_cert: str | None = None,
        tls_client_key: str | None = None,
        tls_server_hostname: str | None = None,
        client_name: str = "mcp-client",
    ) -> None:
        self.host = host
        self.port = port
        self.token = token
        self.connect_timeout_s = connect_timeout_s
        self.call_timeout_s = call_timeout_s
        self.max_retries = max_retries
        self.backoff_base_s = backoff_base_s
        self.backoff_max_s = backoff_max_s
        self.rate_limit_retries = rate_limit_retries
        self.rate_limit_multiplier = rate_limit_multiplier
        self.tls = tls
        self.tls_verify = tls_verify
        self.tls_ca_cert = tls_ca_cert
        self.tls_client_cert = tls_client_cert
        self.tls_client_key = tls_client_key
        self.tls_server_hostname = tls_server_hostname
        self.client_name = client_name

        self._sock: socket.socket | None = None
        self._buf = b""
        self._rid = 0
        # Telemetry · readable by callers for logging / dashboards.
        self.reconnect_count = 0
        self.last_reconnect_reason: str | None = None
        self.rate_limit_waits = 0
        self.last_rate_limit_wait_s: float = 0.0

    # ─── context manager sugar ────────────────────────────────────

    def __enter__(self) -> "MCPClient":
        self._connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
            self._buf = b""

    # ─── public API ───────────────────────────────────────────────

    def ping(self) -> float:
        """Return round-trip latency in ms."""
        t0 = time.perf_counter()
        self._call("ping")
        return (time.perf_counter() - t0) * 1000

    def list_tools(self) -> list[dict]:
        return self._call("tools/list").get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None,
                  progress_cb=None, log_cb=None) -> dict:
        """Invoke a tool.

        `progress_cb`: if set, the client injects a `_meta.progressToken`
        and dispatches any `notifications/progress` frames the server
        emits (one dict arg per frame: `{progress, total?, message?}`)
        before returning the final reply. Server-side tools must opt in
        to progress; non-progress tools ignore the token harmlessly.

        `log_cb`: if set, dispatches any `notifications/message` frames
        the server pushes during the call (one dict arg per frame:
        `{level, data, logger?}`). Use with `set_log_level` to control
        which records the server sends.
        """
        params = {"name": name, "arguments": arguments or {}}
        needs_notifier = progress_cb is not None or log_cb is not None
        if progress_cb is not None:
            params["_meta"] = {"progressToken": f"pt-{self._next_rid()}"}
        if needs_notifier:
            return self._call("tools/call", params,
                              notification_cb={"progress": progress_cb,
                                               "log": log_cb})
        return self._call("tools/call", params)

    def set_log_level(self, level: str) -> dict:
        """Ask the server to send only notifications/message records at
        `level` or higher on this connection. Valid levels · debug /
        info / notice / warning / error / critical / alert / emergency.
        The setting is session-scoped; a reconnect resets to info.
        """
        return self._call("logging/setLevel", {"level": level})

    def cancel(self, request_id, reason: str | None = None) -> None:
        """Send `notifications/cancelled` for a prior requestId.

        Notify-only · the server records the cancellation so
        progress-aware tools can bail between frames. In-flight sync
        tools still run to completion. No reply is expected.
        """
        assert self._sock is not None
        frame: dict = {
            "jsonrpc": "2.0",
            "method": "notifications/cancelled",
            "params": {"requestId": request_id},
        }
        if reason is not None:
            frame["params"]["reason"] = reason
        self._sock.sendall((json.dumps(frame) + "\n").encode("utf-8"))

    def status(self) -> dict:
        return self._call("server/status")

    def list_resources(self, limit: int | None = None) -> list[dict]:
        params = {"limit": limit} if limit is not None else None
        return self._call("resources/list", params).get("resources", [])

    def read_resource(self, uri: str) -> dict:
        """Return the first content block (dict with uri/mimeType/text)."""
        result = self._call("resources/read", {"uri": uri})
        contents = result.get("contents") or []
        if not contents:
            raise MCPClientError(f"resources/read returned no contents for {uri}")
        return contents[0]

    # ─── core transport ───────────────────────────────────────────

    def _next_rid(self) -> int:
        self._rid += 1
        return self._rid

    def _wrap_tls(self, sock: socket.socket) -> socket.socket:
        """Promote a plaintext TCP socket to TLS using the client's config."""
        import ssl
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                         cafile=self.tls_ca_cert)
        if not self.tls_verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        if self.tls_client_cert and self.tls_client_key:
            ctx.load_cert_chain(certfile=self.tls_client_cert,
                                keyfile=self.tls_client_key)
        server_hostname = self.tls_server_hostname or self.host
        # When not verifying · server_hostname is ignored anyway.
        return ctx.wrap_socket(sock, server_hostname=server_hostname
                               if self.tls_verify else None)

    def _connect(self) -> None:
        self.close()
        sock = socket.create_connection((self.host, self.port), timeout=self.connect_timeout_s)
        if self.tls:
            sock = self._wrap_tls(sock)
        sock.settimeout(self.call_timeout_s)
        self._sock = sock
        self._buf = b""
        init_params: dict = {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": self.client_name, "version": "1.0.0"},
        }
        if self.token:
            init_params["authToken"] = self.token
        reply = self._send_recv_raw("initialize", init_params)
        if "error" in reply:
            err = reply["error"]
            raise MCPClientError(f"initialize failed: {err.get('code')} {err.get('message')}")

    def _send_recv_raw(self, method: str, params: dict | None = None,
                       notification_cb=None) -> dict:
        """One send + one recv over the current socket · no reconnect logic.

        If `notification_cb` is set, intermediate `notifications/*` frames
        (no `id`) are dispatched to it and the loop keeps reading until a
        frame with an `id` matching our request shows up. progress frames
        from the server arrive on the same socket, not a side channel.

        Raises the underlying socket error on failure. _call wraps this.
        """
        assert self._sock is not None
        rid = self._next_rid()
        msg = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            msg["params"] = params
        self._sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))
        while True:
            while b"\n" not in self._buf:
                chunk = self._sock.recv(4096)
                if not chunk:
                    raise ConnectionResetError("server closed socket")
                self._buf += chunk
            line, _, self._buf = self._buf.partition(b"\n")
            frame = json.loads(line.decode("utf-8"))
            # Notifications carry `method` + no `id`. Dispatch and loop.
            if "id" not in frame and frame.get("method", "").startswith("notifications/"):
                method_name = frame.get("method", "")
                fparams = frame.get("params") or {}
                cb = None
                payload = None
                if method_name == "notifications/progress":
                    cb = (notification_cb or {}).get("progress") \
                        if isinstance(notification_cb, dict) else notification_cb
                    payload = {
                        "progress": fparams.get("progress"),
                        "total": fparams.get("total"),
                        "message": fparams.get("message"),
                        "progressToken": fparams.get("progressToken"),
                    }
                elif method_name == "notifications/message":
                    # logging/setLevel + notifications/message · Task #59.
                    # Only dispatched when caller passed a dict with "log".
                    if isinstance(notification_cb, dict):
                        cb = notification_cb.get("log")
                    payload = {
                        "level": fparams.get("level"),
                        "data": fparams.get("data"),
                        "logger": fparams.get("logger"),
                    }
                if cb is not None:
                    try:
                        cb(payload)
                    except Exception:
                        # User callback errors must not break the RPC · the
                        # reply is still in flight behind this frame.
                        pass
                continue
            return frame

    def _call(self, method: str, params: dict | None = None,
              notification_cb=None) -> dict:
        """Send a JSON-RPC call, reconnect + retry transparently on I/O error."""
        last_err: Exception | None = None
        rate_attempts = 0
        for attempt in range(self.max_retries + 1):
            if self._sock is None:
                try:
                    self._connect()
                except (ConnectionRefusedError, OSError, socket.timeout) as e:
                    last_err = e
                    self._sleep_backoff(attempt)
                    continue
            try:
                reply = self._send_recv_raw(method, params,
                                            notification_cb=notification_cb)
            except (ConnectionResetError, BrokenPipeError, socket.timeout, OSError) as e:
                last_err = e
                self.reconnect_count += 1
                self.last_reconnect_reason = f"{type(e).__name__}: {e}"
                self.close()
                self._sleep_backoff(attempt)
                continue
            if "error" in reply:
                err = reply["error"]
                code = err.get("code")
                msg = err.get("message", "")
                # Rate-limit backoff · opt-in via rate_limit_retries > 0.
                if code == -32029 and rate_attempts < self.rate_limit_retries:
                    rate_attempts += 1
                    wait_s = _parse_retry_after(msg) * self.rate_limit_multiplier
                    self.rate_limit_waits += 1
                    self.last_rate_limit_wait_s = wait_s
                    time.sleep(wait_s)
                    continue  # retry without counting against max_retries
                raise MCPClientError(f"{method} failed: {code} {msg}")
            return reply.get("result", {})
        raise MCPClientError(
            f"{method} exhausted {self.max_retries} retries · last error: {last_err}"
        )

    def _sleep_backoff(self, attempt: int) -> None:
        delay = min(self.backoff_base_s * (2 ** attempt), self.backoff_max_s)
        time.sleep(delay)
