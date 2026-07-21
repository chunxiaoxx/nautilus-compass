param(
    [string]$Python = $env:PYTHON,
    [ValidateSet("smoke", "full")]
    [string]$Suite = "smoke"
)

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $PSScriptRoot
Set-Location $RepoDir

$Model = if ($env:ZMM_EMBEDDER_MODEL) { $env:ZMM_EMBEDDER_MODEL } else { "(default in daemon.py)" }
$safeModel = $Model -replace "[\\/]", "_"
$ProfileDir = ".cache/bench-profile-$(Get-Date -Format yyyyMMdd-HHmmss)-$safeModel"
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

Write-Host "[bench_profile.ps1] start run_all profile"
Write-Host "[bench_profile.ps1] model: $Model"
Write-Host "[bench_profile.ps1] suite: $Suite"
Write-Host "[bench_profile.ps1] output: $ProfileDir"

$runAllLog = Join-Path $ProfileDir "run_all.log"
& "$PSScriptRoot/run_all.ps1" -OutDir $ProfileDir -Python $Python -Suite $Suite 2>&1 | Tee-Object -FilePath $runAllLog
if ($LASTEXITCODE -ne 0) {
    throw "run_all.ps1 failed; see $runAllLog"
}

$manifestPath = Join-Path $ProfileDir "eval-manifest.json"
if (-not (Test-Path $manifestPath)) {
    throw "manifest missing: $manifestPath"
}

$manifest = Get-Content -Path $manifestPath -Raw | ConvertFrom-Json
if ($manifest.overall_exit_code -ne 0) {
    throw "manifest reports failure: $manifestPath"
}

$recallStep = $manifest.steps | Where-Object { $_.name -eq "03_recall" } | Select-Object -First 1
$hintStep = $manifest.steps | Where-Object { $_.name -eq "04_recall_tuning_hint" } | Select-Object -First 1
if (-not $recallStep -or -not $hintStep) {
    throw "required recall steps missing from manifest"
}
if (-not (Test-Path $recallStep.artifact) -or -not (Test-Path $hintStep.artifact)) {
    throw "required recall artifacts missing"
}

$profileHint = Join-Path $ProfileDir "eval_recall_tuning_hint_profile.json"
& $manifest.python "ops/eval_recall_tuning_hint.py" --artifact $recallStep.artifact --out $profileHint > (Join-Path $ProfileDir "tuning_hint_profile.log") 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "profile tuning hint generation failed"
}

$recall = Get-Content -Path $recallStep.artifact -Raw | ConvertFrom-Json
$hint = Get-Content -Path $profileHint -Raw | ConvertFrom-Json
$summary = [ordered]@{
    run_at = $manifest.run_at
    python = $manifest.python
    python_version = $manifest.python_version
    embedder = $manifest.embedder
    suite = $manifest.suite
    out_dir = $manifest.out_dir
    n_memories = $recall.meta.n_memories
    result_summary = $recall.result_summary
    recommendations_count = @($recall.recommendations).Count
    tuning_risk = $hint.risk
    tuning_next_actions = @($hint.next_actions).Count
}

$summaryPath = Join-Path $ProfileDir "summary.json"
$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "[bench_profile.ps1] done"
Write-Host "  manifest: $manifestPath"
Write-Host "  summary:  $summaryPath"
