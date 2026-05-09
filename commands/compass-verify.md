# /compass-verify — Memory Tamper Check

Verify the Merkle hash chain over `~/.claude/projects/<project>/memory/` and report any tampered or missing files.

## When to use

- Before relying on a recall hit ("did this memory get altered?")
- After a crash, conflict, or unexpected memory edit
- During incident response — chain mismatch is evidence of corruption or injection
- Periodically as a session-start sanity check

## How to run

The plugin ships `compass_verify.py`. Invoke it with the Bash tool:

```bash
# Verify the active project (default)
python ~/.claude/plugins/nautilus-compass/compass_verify.py

# Verify every project under ~/.claude/projects/
python ~/.claude/plugins/nautilus-compass/compass_verify.py --all

# Verify a specific encoded project key
python ~/.claude/plugins/nautilus-compass/compass_verify.py --project C-Users-chunx-Projects-foo
```

If `$ARGUMENTS` is provided, append it to the command (e.g. `--all`).

## What to report back

For each project the CLI prints:

- `[OK] ✓ <project>` — chain head matches every file's recorded hash
- `[TAMPERED] ✗ <project>` — list of `tampered_files` and/or `missing_files`
- `[SKIP] <project>` — no `memory/` dir or no `.chain.json` recorded yet

Surface the result to the user in two parts:
1. **Headline** — clean (✓ all OK), drift (some SKIP), or **alert** (any ✗).
2. **Action** — if tampered: stop relying on those files, escalate, optionally regenerate chain after auditing the diff.

## Exit codes

- `0` — all verified chains valid
- `1` — at least one tampered/missing file, or chain file missing for a queried project
- `2` — flag conflict (`--all` and `--project` together)

Pass the exit code through to the user's session — non-zero must NOT be silently swallowed.
