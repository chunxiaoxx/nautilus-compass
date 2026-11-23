# Nagizaaz 安全报告回复草稿 · 2026-11-20

状态：待用户审阅，未发送。Gmail 草稿 ID：`1a1f72c912c39a97`。

## English draft

Hello Nagizaaz,

Thank you for the detailed follow-up on issue #66. We have received the report, appreciate the care in the technical details, and are treating it as a coordinated-disclosure security issue. We would be glad to continue the review together.

We completed a local source and negative-test recheck of the v14 recall and ingest paths. The current local result is:

- the v14 recall route requires a Bearer JWT and an explicit user-to-project map;
- the legacy `scope=user` path remains disabled until mapped-project filtering is implemented;
- unauthenticated requests to the local 8097 MCP HTTP boundary return HTTP 401;
- the targeted local MCP, daemon, auth, scope, and v14 boundary suites passed 26 tests in this recheck.

The production-facing 8770 probe timed out. We are treating that as an unresolved deployment check, not as evidence of a fix. We have not claimed that the issue is fully fixed or that a production deployment changed.

The remaining work is to configure and independently verify the production user-to-project map, repeat the negative probes against the deployed adapter, and then report the affected versions, remediation status, and exact evidence.

If you have a preferred negative-test fixture or deployment check for the next round, please share it. We will run it alongside our own checks and report the result in the same thread.

Thank you for providing the source locations and the suggested checks.

Best regards,
Chunxiao Wang
nautilus-compass
