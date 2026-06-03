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

$null = New-Item -ItemType Directory -Path (Split-Path $LogPath) -Force

# /SC MINUTE /MO 30 · runs as the registering (current) user · /F overwrites.
# Redirect both streams to the log; the poller itself never prints secrets.
$cmd = "py -3 `"$PyScript`" >> `"$LogPath`" 2>&1"
& schtasks.exe /Create /TN $TaskName /TR $cmd /SC MINUTE /MO $IntervalMinutes /F | Out-Null

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
