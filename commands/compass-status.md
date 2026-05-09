# /compass-status — Combined Compass Health Snapshot

One-shot overview combining Merkle chain integrity, drift trend, BGE daemon liveness, and project memory size. Use this when you want to know "is compass working right now and is the memory I'm about to recall on trustworthy?" without firing four separate commands.

## When to use

- Session start — quick green/yellow/red on memory health
- Before relying on a recall hit for a high-stakes decision
- Incident triage — one screen for "what's wrong"
- Before publishing a session summary or signing off a phase

## How to run

`/compass-status` has no required arguments. `$ARGUMENTS` accepts:

- `--days N` → drift window (default `7`)
- `--project <prefix>` → restrict drift summary to a project key prefix

Run all four checks via Bash, in this order, capturing each section. Continue even if a step fails — partial output is more useful than an aborted run.

```bash
# 1. BGE daemon liveness (sub-second)
echo '{"action":"ping"}' | python -c "
import socket, sys, json
try:
    s = socket.socket(); s.settimeout(2)
    s.connect(('127.0.0.1', 9876))
    s.sendall(sys.stdin.buffer.read())
    print(s.recv(1024).decode().strip())
except Exception as e:
    print(f'DOWN: {e}')
" 2>&1

# 2. Merkle chain — current project
python ~/.claude/plugins/nautilus-compass/compass_verify.py 2>&1

# 3. Drift summary — last N days (default 7)
python ~/.claude/plugins/nautilus-compass/drift_history.py 7 2>&1

# 4. Memory entry count for the active project
python -c "
from pathlib import Path
import sys
sys.path.insert(0, str(Path.home() / '.claude' / 'plugins' / 'nautilus-compass'))
from recall import find_active_project_memory_dir
mem = find_active_project_memory_dir()
if not mem:
    print('memory: no active project memory dir for current cwd')
else:
    md = sorted(mem.glob('*.md'))
    print(f'memory: {mem.parent.name} · {len(md)} entries')
"
```

## What to report back

Surface a 4-line headline first, then expand each section only if it's not green:

```
compass status · 2026-MM-DD HH:MM
  daemon  : ✓ pong (BGE-m3 ready)        | DOWN (metadata-only mode)
  chain   : ✓ <project>                  | TAMPERED · N files
  drift   : G:84% Y:13% R:2% (last 7d)   | RED bursts · last red MM-DD
  memory  : <project> · N entries        | empty / no active dir
```

Color logic:
- **All ✓** → one-line "everything green" report
- **Any ✗ or DOWN** → emit the headline + the failing section's full output + a 1-sentence "what to do" hint

## Hints to embed when reporting

- Daemon DOWN → tell user to run `bash ~/.claude/plugins/nautilus-compass/daemon_start.sh` (recall falls back to metadata mode in the meantime)
- Chain TAMPERED → stop relying on the listed memory files; surface the file list verbatim; suggest auditing diffs before regenerating chain
- Drift red ≥ 5% → investigate via `/compass-drift 30 --top 10`
- Memory empty → user is in a fresh project or a cwd that doesn't map to a project; recall hits will be empty
