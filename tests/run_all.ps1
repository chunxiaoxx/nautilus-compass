param(
    [string]$OutDir = "",
    [string]$Python = $env:PYTHON,
    [ValidateSet("smoke", "full")]
    [string]$Suite = "full"
)

$ErrorActionPreference = "Stop"

function Resolve-CompassPython {
    param([string]$Requested)

    $candidates = @()
    if ($Requested) { $candidates += $Requested }

    $localPythonRoot = Join-Path $env:LOCALAPPDATA "Programs/Python"
    if (Test-Path $localPythonRoot) {
        $candidates += Get-ChildItem -Path $localPythonRoot -Directory -Filter "Python*" |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "python.exe" }
    }

    foreach ($cmdName in @("python", "python3", "py")) {
        try {
            $resolved = & where.exe $cmdName 2>$null
            if ($LASTEXITCODE -eq 0) {
                $candidates += $resolved
            }
        } catch {
            continue
        }
    }

    foreach ($candidate in $candidates) {
        try {
            $cmd = Get-Command $candidate -ErrorAction Stop
            $exe = $cmd.Source
            if ($exe -like "*\WindowsApps\*") {
                continue
            }
            $probe = & $exe -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $exe
            }
        } catch {
            continue
        }
    }

    throw "Unable to resolve Python 3.10+ interpreter. Set PYTHON to a valid Python path."
}

function Run-Step {
    param(
        [string]$Name,
        [string]$Artifact,
        [string[]]$ScriptArgs
    )

    Write-Host ""
    Write-Host "=== $Name ==="
    $log = Join-Path $OutDir "$Name.log"

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & $PythonBin @ScriptArgs 2>&1
    $rc = $LASTEXITCODE
    $ErrorActionPreference = $oldErrorActionPreference

    $outputText = $output | ForEach-Object { "$_" }
    $outputText | Set-Content -Path $log -Encoding UTF8
    $outputText | ForEach-Object { Write-Host $_ }

    if ($rc -ne 0) {
        Write-Host "[run_all.ps1] ERROR: $Name failed (exit $rc)"
    }

    return [ordered]@{
        name = $Name
        log = $log
        artifact = $Artifact
        status = $rc
    }
}

$RepoDir = Split-Path -Parent $PSScriptRoot
Set-Location $RepoDir

$PythonBin = Resolve-CompassPython -Requested $Python
$pyVersion = & $PythonBin --version

$Model = if ($env:ZMM_EMBEDDER_MODEL) { $env:ZMM_EMBEDDER_MODEL } else { "(default in daemon.py)" }
if (-not $OutDir) {
    $safeModel = $Model -replace "[\\/]", "_"
    $OutDir = ".cache/eval-$(Get-Date -Format yyyyMMdd-HHmmss)-$safeModel"
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "==========================================="
Write-Host "  nautilus-compass eval suite"
Write-Host "  python:   $pyVersion ($PythonBin)"
Write-Host "  embedder: $Model"
Write-Host "  suite:    $Suite"
Write-Host "  output:   $OutDir"
Write-Host "==========================================="

$steps = @()
$steps += Run-Step -Name "00_selftest" -Artifact "" -ScriptArgs @("selftest.py")

if ($Suite -eq "full") {
    $steps += Run-Step -Name "01_calibrate" -Artifact "" -ScriptArgs @("tests/eval_calibrate.py")
    $steps += Run-Step -Name "02_drift" -Artifact "" -ScriptArgs @("tests/eval_drift.py")
}

$recallArtifact = Join-Path $OutDir "eval_recall.json"
$steps += Run-Step -Name "03_recall" -Artifact $recallArtifact -ScriptArgs @("tests/eval_recall.py", "--mode", "all", "--out", $recallArtifact)

$hintArtifact = Join-Path $OutDir "eval_recall_tuning_hint.json"
if (($steps | Where-Object { $_.name -eq "03_recall" }).status -eq 0) {
    $steps += Run-Step -Name "04_recall_tuning_hint" -Artifact $hintArtifact -ScriptArgs @("ops/eval_recall_tuning_hint.py", "--artifact", $recallArtifact, "--out", $hintArtifact)
} else {
    $skipLog = Join-Path $OutDir "04_recall_tuning_hint.log"
    "[run_all.ps1] skipped 04_recall_tuning_hint because 03_recall failed" | Tee-Object -FilePath $skipLog
    $steps += [ordered]@{
        name = "04_recall_tuning_hint"
        log = $skipLog
        artifact = $hintArtifact
        status = 99
    }
}

$overall = if (($steps | Where-Object { $_.status -ne 0 }).Count -gt 0) { 1 } else { 0 }
$manifestPath = Join-Path $OutDir "eval-manifest.json"
$manifest = [ordered]@{
    run_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    python = $PythonBin
    python_version = $pyVersion
    embedder = $Model
    suite = $Suite
    out_dir = $OutDir
    overall_exit_code = $overall
    steps = $steps
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Path $manifestPath -Encoding UTF8

Write-Host ""
Write-Host "manifest: $manifestPath"
if ($overall -ne 0) {
    exit 1
}

Write-Host "[run_all.ps1] recall artifacts:"
Write-Host "  - $recallArtifact"
Write-Host "  - $hintArtifact"
Write-Host "==========================================="
Write-Host "  done"
Write-Host "==========================================="
