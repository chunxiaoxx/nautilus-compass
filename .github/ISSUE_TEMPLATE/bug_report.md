---
name: Bug report
about: Something isn't working
labels: bug
---

## Describe the bug

(One sentence)

## Reproduction

```bash
# Steps that trigger the bug
```

## Expected vs actual

- Expected:
- Actual:

## Environment

- compass version: (run `pip show nautilus-compass` or check `pyproject.toml`)
- Python version: (`python --version`)
- OS: (Linux/macOS/Windows + version)
- MCP client (if applicable): (Claude Desktop / Cline / Cursor / version)
- daemon running: (yes/no · `~/compass/daemon_start.sh`)

## Logs

```
(stderr / hook output / mcp server stderr)
```

## Drift status

If the bug involves AI behavior:

- `drift_history 7` output:
- Most recent session_*.md frontmatter (paste `drift:` field):

(See `paper/RESULTS_v0.8.md` for context on what "drift" means)
