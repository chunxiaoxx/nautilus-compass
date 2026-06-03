# compass · L4 cross-agent outcome poller · Windows Task Scheduler registration
# ---------------------------------------------------------------------------
# Registers a scheduled task that runs ops/cross_agent_outcome_poller.py every
# 30 minutes (ssh tunnel -> read-only platform DB -> _l4_cross_agent/memory).
# Idempotent + has --dry-run; safe to run repeatedly (/F overwrites the task).
#
# Run once (as the CURRENT user, NOT SYSTEM — Task Scheduler under SYSTEM has the
# wrong ~/.ssh path and no ssh-agent):
#     powershell -ExecutionPolicy Bypass -File ops\setup-l4-poller-task.ps1
# Unregister:
#     schtasks /Delete /TN compass-l4-cross-agent-poller /F
#
# Prerequisites (see report):
#   - passwordless ssh key for `Host cloud` (Task Scheduler has no ssh-agent)
#   - .soul_db_secret present (else the poller safely no-ops and exits 0)
#   - `py -3` resolves python 3 with psycopg2 installed
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$TaskName  = "compass-l4-cross-agent-poller"
$PyScript  = Join-Path $PSScriptRoot "cross_agent_outcome_poller.py"
$LogPath   = Join-Path $env:USERPROFILE ".cache\compass\l4-cross-agent-poller.log"
$IntervalMinutes = 30

if (-not (Test-Path $PyScript)) {
    Write-Error "poller script not found next to this file: $PyScript"
    exit 1
}

# Resolve a python that actually has psycopg2 — `py -3` may pick a different
# interpreter (e.g. 3.14) WITHOUT psycopg2. Prefer $COMPASS_PYTHON, else the
# `python` on PATH that imports psycopg2, else fall back to a full path. Task
# Scheduler has a minimal PATH, so we bake the absolute exe into the task.
$Python = $env:COMPASS_PYTHON
if (-not $Python) {
    foreach ($cand in @((Get-Command python -ErrorAction SilentlyContinue).Source,
                        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
                        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe")) {
        if ($cand -and (Test-Path $cand)) {
            & $cand -c "import psycopg2" 2>$null
            if ($LASTEXITCODE -eq 0) { $Python = $cand; break }
        }
    }
}
if (-not $Python) {
    Write-Error "no python with psycopg2 found; set `$env:COMPASS_PYTHON to a python.exe that has psycopg2"
    exit 1
}
Write-Output "[compass-l4] using python: $Python"

$null = New-Item -ItemType Directory -Path (Split-Path $LogPath) -Force

# /SC MINUTE /MO 30 · runs as the registering (current) user · /F overwrites.
# schtasks runs /TR directly (no shell), so `>>` redirection must go through
# `cmd /c`. Inner quotes are doubled for the schtasks arg parser. The poller
# never prints secrets, so logging both streams is safe.
$cmd = "cmd /c `"`"`"$Python`"`" `"`"$PyScript`"`" >> `"`"$LogPath`"`" 2>&1`""
& schtasks.exe /Create /TN $TaskName /TR $cmd /SC MINUTE /MO $IntervalMinutes /F | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error "schtasks /Create failed (exit $LASTEXITCODE) · run this in a normal (non-sandboxed) PowerShell, as the current user"
    exit $LASTEXITCODE
}

Write-Output "[compass-l4] registered scheduled task"
Write-Output "  task:   $TaskName"
Write-Output "  script: $PyScript"
Write-Output "  every:  $IntervalMinutes min"
Write-Output "  log:    $LogPath"
Write-Output ""
Write-Output "verify:   schtasks /Query /TN $TaskName /V"
Write-Output "run now:  schtasks /Run /TN $TaskName   (then check the log)"
Write-Output "remove:   schtasks /Delete /TN $TaskName /F"
Write-Output ""
Write-Output "NOTE · reconciler (ops/poi_reconcile_cron.py) is intentionally NOT"
Write-Output "scheduled here — it has no candidates to settle until L3 candidate"
Write-Output "firing is activated in the live plugin. Schedule it after activation."
