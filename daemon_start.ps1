# daemon_start.ps1 · Windows launcher for one explicit Compass runtime.
#
# Run from any directory:
#   powershell -ExecutionPolicy Bypass -File daemon_start.ps1
#
# Set COMPASS_PYTHON to pin the interpreter. Otherwise the launcher prefers
# the repository-local .venv before falling back to python on PATH.

$ErrorActionPreference = "Stop"

$PluginDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DaemonPath = Join-Path $PluginDir "daemon.py"
$DoctorPath = Join-Path $PluginDir "doctor.py"

function Resolve-CompassPython {
    if ($env:COMPASS_PYTHON) {
        return (Resolve-Path -LiteralPath $env:COMPASS_PYTHON -ErrorAction Stop).Path
    }

    $LocalPython = Join-Path $PluginDir ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $LocalPython) {
        return (Resolve-Path -LiteralPath $LocalPython).Path
    }

    $PathPython = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if ($PathPython) {
        return $PathPython.Source
    }

    throw "no python found; set COMPASS_PYTHON or create $PluginDir\.venv"
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
$Process = Start-Process `
    -FilePath $Python `
    -ArgumentList @($DaemonPath) `
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
    exit 1
}

Write-Host "daemon did not become functionally ready within 60s; see $StderrPath" -ForegroundColor Red
exit 1
