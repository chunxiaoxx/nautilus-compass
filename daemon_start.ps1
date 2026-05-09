# daemon_start.ps1 · v1.0 · Windows PowerShell equivalent of daemon_start.sh
# Starts the V5 Memory Daemon in the background. Idempotent: noop if already up.
#
# Run from any dir:  powershell -ExecutionPolicy Bypass -File daemon_start.ps1

$ErrorActionPreference = "Stop"

$PluginDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Resolve a python interpreter
$Python = $null
foreach ($c in @("python", "py -3")) {
    try {
        $null = & cmd /c "$c --version" 2>$null
        if ($LASTEXITCODE -eq 0) { $Python = $c; break }
    } catch { }
}
if (-not $Python) {
    Write-Host "no python found on PATH" -ForegroundColor Red
    exit 1
}

# Already alive?
& cmd /c "$Python `"$PluginDir\daemon.py`" ping" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "V5 Memory Daemon already running (port 9876)" -ForegroundColor Green
    exit 0
}

Write-Host "Starting V5 Memory Daemon..."

# Spawn detached. Output discarded; daemon writes its own log under .cache/
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = "cmd.exe"
$startInfo.Arguments = "/c $Python `"$PluginDir\daemon.py`" > NUL 2>&1"
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($startInfo)
Write-Host "PID: $($proc.Id) · waiting for BGE load (~30s)..."

# Poll ping up to 60s
for ($i = 1; $i -le 60; $i++) {
    Start-Sleep -Seconds 1
    & cmd /c "$Python `"$PluginDir\daemon.py`" ping" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "V5 Memory Daemon ready (took ${i}s)" -ForegroundColor Green
        Write-Host "   port 9876 · PID file: $PluginDir\.cache\daemon.pid"
        Write-Host "   log: $PluginDir\.cache\daemon.log"
        exit 0
    }
}

Write-Host "daemon did not come up within 60s · see $PluginDir\.cache\daemon.log" -ForegroundColor Red
exit 1
