# Local server change record

The running local service is `/Users/chunxiao.wang/infra/bin/local_llm_server.py`.

The server now reads both `enable_thinking` and Claude-style `thinking.type` per request. The Claude endpoint defaults to thinking disabled for short value-loop calls. A caller can set `thinking.type=enabled` for a semantic review request. The OpenAI endpoints keep the server default unless the request supplies an explicit flag.

## Verification

- `python3 -m py_compile /Users/chunxiao.wang/infra/bin/local_llm_server.py` passed.
- `launchctl kickstart -k gui/$(id -u)/com.nautilus.local-llm` completed and `/health` returned `loaded=true`.
- Claude `/v1/messages` short smoke returned `LOCAL_CLAUDE_ROUTE_OK` in about 2 seconds.
- Claude Code `--bare --settings runtime/local-llm/claude-local-9b-settings.json --model sonnet` returned `LOCAL_CLAUDE_ALIAS_OK`.
- Current source SHA-256 is `9c7229b0234099322946f9076b0a652e372a1ac71dd3d4c5a87797dffdfa0cbb`.

The source file lives outside this Git repository. This record keeps the local runtime change visible during migration and recovery.
