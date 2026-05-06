## What changed

(One sentence)

## Why

(Background · linked issue · roadmap reference)

## Type

- [ ] bugfix
- [ ] feature
- [ ] refactor
- [ ] docs
- [ ] benchmark / paper data
- [ ] performance
- [ ] security

## Testing

- [ ] `python tests/test_compass_v09.py` passes
- [ ] `python sdk/a2a_adapter.py selftest` passes
- [ ] `node npm/bin/cli.js --selftest` passes (if touching MCP server)
- [ ] Re-ran LongMemEval subset (if changing pipeline)
- [ ] Manual smoke test in (Claude Desktop / Cline / Cursor) (if touching MCP)

## Drift impact

Does this change affect AI drift detection or self-audit?
- [ ] No
- [ ] Yes · explained below

## Breaking changes

- [ ] None
- [ ] CHANGELOG.md updated
- [ ] Migration guide added (if schema change)

## Checklist

- [ ] My code follows existing style (ruff check passes)
- [ ] I added tests for new behavior
- [ ] I updated docs if user-visible
- [ ] My commit messages are descriptive (≥1 imperative sentence)
