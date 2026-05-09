# /compass-search — Search Past Sessions

Search compass session-summary frontmatter (`name`, `concept`, `type`, `drift`, body) across all recorded sessions. Returns ranked hits with timestamps and drift glyphs.

## When to use

- "When did we work on X?" — locate a past session by topic
- "Show me only red drift sessions touching Y" — filtered investigation
- Cross-project lookup — find a concept across multiple project keys

## How to run

Invoke `session_search.py` via Bash. The first positional arg is the query; subsequent flags filter further.

```bash
python ~/.claude/plugins/nautilus-compass/session_search.py $ARGUMENTS
```

`$ARGUMENTS` shape: `<query> [--drift green|yellow|red] [--type ...] [--days N] [--project <prefix>] [--top N]`

Examples:

```bash
# Plain query, last 60 days
python ~/.claude/plugins/nautilus-compass/session_search.py "merkle chain"

# Only red-drift sessions touching "rebase"
python ~/.claude/plugins/nautilus-compass/session_search.py "rebase" --drift red

# Last 14 days, top 10
python ~/.claude/plugins/nautilus-compass/session_search.py "agent design" --days 14 --top 10

# One project only
python ~/.claude/plugins/nautilus-compass/session_search.py "deploy" --project C-Users-chunx-Projects-nautilus
```

## What to report back

The CLI prints one block per hit:

- `[score]  MM-DD HH:MM  <drift-glyph> <drift>  [<project>]`
- `<name>` (concept summary)
- `type=<type> · concept=<concept>`
- file name pointer

Lead with hit count and the top hit's name. If nothing matched, say so explicitly with the filters used (so the user can relax them).
