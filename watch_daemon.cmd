@echo off
rem nautilus-compass daemon watchdog wrapper (2026-09-08)
rem Runs the idempotent daemon_start.sh every 5min via Task Scheduler.
rem Fast path: daemon alive -> ping exits 0 in ~2s, no-op.
rem This detaches the daemon from any Claude Code session process tree
rem (root cause of "hook-spawned daemon dies with the hook").
"C:\Program Files\Git\bin\bash.exe" -c "exec bash 'C:/Users/chunx/.claude/plugins/nautilus-compass/daemon_start.sh' >> 'C:/Users/chunx/.claude/plugins/nautilus-compass/.cache/watchdog.log' 2>&1"
