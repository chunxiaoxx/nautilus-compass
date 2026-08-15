# daemon_start.ps1 · Windows launcher for one explicit Compass runtime.
#
# Run from any directory:
#   powershell -ExecutionPolicy Bypass -File daemon_start.ps1
#
# Set COMPASS_PYTHON to pin the interpreter. Otherwise the launcher prefers
# a short user-level virtualenv path, then a repository-local .venv,
# then PATH.

$ErrorActionPreference = "Stop"

$PluginDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DaemonPath = Join-Path $PluginDir "daemon.py"
$DoctorPath = Join-Path $PluginDir "doctor.py"

function Resolve-CompassPython {
    if ($env:COMPASS_PYTHON) {
        return (Resolve-Path -LiteralPath $env:COMPASS_PYTHON -ErrorAction Stop).Path
    }

    if ($env:USERPROFILE) {
        $UserRuntimePython = Join-Path $env:USERPROFILE ".venvs\nautilus-compass\Scripts\python.exe"
        if (Test-Path -LiteralPath $UserRuntimePython) {
            return (Resolve-Path -LiteralPath $UserRuntimePython).Path
        }
    }

    $LocalPython = Join-Path $PluginDir ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $LocalPython) {
        return (Resolve-Path -LiteralPath $LocalPython).Path
    }

    $PathPython = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($PathPython) {
        return $PathPython.Source
    }

    throw "no python found; set COMPASS_PYTHON or create the Compass user runtime"
}

function Test-DaemonPing([string]$Python) {
    & $Python $DaemonPath ping 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Test-FunctionalDoctor([string]$Python) {
    $PreviousPluginDir = $env:COMPASS_PLUGIN_DIR
    try {
        $env:COMPASS_PLUGIN_DIR = $PluginDir
        & $Python $DoctorPath --json 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    }
    finally {
        $env:COMPASS_PLUGIN_DIR = $PreviousPluginDir
    }
}

function Stop-StartedCompassProcess([System.Diagnostics.Process]$Process) {
    try {
        $Running = Get-Process -Id $Process.Id -ErrorAction SilentlyContinue
        if ($Running -and $Running.StartTime -eq $Process.StartTime) {
            Stop-Process -Id $Process.Id -ErrorAction Stop
            $Running.WaitForExit(5000) | Out-Null
        }
    }
    catch {
        Write-Warning "could not clean up started Compass process $($Process.Id): $($_.Exception.Message)"
    }
}

try {
    $Python = Resolve-CompassPython
}
catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

& $Python -c "import torch; import sentence_transformers" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "dependency preflight failed for $Python" -ForegroundColor Red
    exit 1
}

if (Test-DaemonPing $Python) {
    if (Test-FunctionalDoctor $Python) {
        Write-Host "Compass daemon already running and functionally ready (port 9876)" -ForegroundColor Green
        exit 0
    }
    Write-Host "daemon pinged but functional doctor failed; stop the stale runtime explicitly before retrying" -ForegroundColor Red
    exit 1
}

$CacheDir = Join-Path $PluginDir ".cache"
New-Item -ItemType Directory -Force -Path $CacheDir | Out-Null
$StdoutPath = Join-Path $CacheDir "daemon.stdout.log"
$StderrPath = Join-Path $CacheDir "daemon.stderr.log"

Write-Host "Starting Compass daemon with $Python"
$DaemonArgument = '"' + $DaemonPath + '"'
$Process = Start-Process `
    -FilePath $Python `
    -ArgumentList @($DaemonArgument) `
    -WorkingDirectory $PluginDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $StdoutPath `
    -RedirectStandardError $StderrPath `
    -PassThru
Write-Host "PID: $($Process.Id); waiting for functional readiness"

for ($Attempt = 1; $Attempt -le 60; $Attempt++) {
    Start-Sleep -Seconds 1
    if (-not (Test-DaemonPing $Python)) {
        if ($Process.HasExited) {
            Write-Host "daemon exited before readiness; see $StderrPath" -ForegroundColor Red
            exit 1
        }
        continue
    }

    if (Test-FunctionalDoctor $Python) {
        Write-Host "Compass daemon functionally ready (took ${Attempt}s)" -ForegroundColor Green
        Write-Host "logs: $StdoutPath and $StderrPath"
        exit 0
    }

    Write-Host "daemon pinged but functional doctor failed; see $StderrPath" -ForegroundColor Red
    Stop-StartedCompassProcess $Process
    exit 1
}

Stop-StartedCompassProcess $Process
Write-Host "daemon did not become functionally ready within 60s; see $StderrPath" -ForegroundColor Red
exit 1
