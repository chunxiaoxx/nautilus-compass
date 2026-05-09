# /compass-drift — Drift History Summary

Summarize drift signals (green / yellow / red) across recent sessions: distribution, timeline, top yellow signals, and red incident details.

## When to use

- Catching up after a break — "what was off recently?"
- Investigating a regression — "when did the noise start?"
- Periodic check — drift trend across the last N days

## How to run

Invoke `drift_history.py` via Bash. `$ARGUMENTS` accepts:

- A bare integer → number of days to look back (default `30`)
- `--project <prefix>` → restrict to projects whose key starts with `<prefix>`
- `--top <N>` → cap the red details listing (default `5`)

```bash
python ~/.claude/plugins/nautilus-compass/drift_history.py $ARGUMENTS
```

Examples:

```bash
# Default — last 30 days, all projects
python ~/.claude/plugins/nautilus-compass/drift_history.py

# Last 7 days only
python ~/.claude/plugins/nautilus-compass/drift_history.py 7

# Restrict to one project, show top 10 reds
python ~/.claude/plugins/nautilus-compass/drift_history.py 30 --project C-Users-chunx-Projects-nautilus --top 10
```

## What to report back

The CLI prints four blocks. Relay them concisely to the user:

1. **Summary** — green / yellow / red counts and ratios
2. **Timeline** — per-day drift glyphs (recent at the top)
3. **Top yellow signals** — most-seen yellow signal IDs with counts
4. **Red details** — for each red session: time, project, reason, top trigger

If everything is green, say so in one line. If reds dominate, lead with the headline count and the most recent red's reason.
