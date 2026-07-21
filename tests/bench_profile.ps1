param(
    [string]$Python = $env:PYTHON,
    [ValidateSet("smoke", "full")]
    [string]$Suite = "smoke"
)

$ErrorActionPreference = "Stop"

function Invoke-ProfilePythonLog {
    param(
        [string]$PythonBin,
        [string[]]$ScriptArgs,
        [string]$Log,
        [string]$FailureMessage
    )

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = & $PythonBin @ScriptArgs 2>&1
    $rc = $LASTEXITCODE
    $ErrorActionPreference = $oldErrorActionPreference

    $outputText = $output | ForEach-Object { "$_" }
    $outputText | Set-Content -Path $Log -Encoding UTF8

    if ($rc -ne 0) {
        throw $FailureMessage
    }
}

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
Invoke-ProfilePythonLog -PythonBin $manifest.python `
    -ScriptArgs @("ops/eval_recall_tuning_hint.py", "--artifact", $recallStep.artifact, "--out", $profileHint) `
    -Log (Join-Path $ProfileDir "tuning_hint_profile.log") `
    -FailureMessage "profile tuning hint generation failed"

$guardedRecall = Join-Path $ProfileDir "eval_recall_guarded.json"
Invoke-ProfilePythonLog -PythonBin $manifest.python `
    -ScriptArgs @("tests/eval_recall.py", "--mode", "all", "--signal-policy", "guarded", "--out", $guardedRecall) `
    -Log (Join-Path $ProfileDir "eval_recall_guarded.log") `
    -FailureMessage "guarded recall evaluation failed"

$guardedHint = Join-Path $ProfileDir "eval_recall_guarded_tuning_hint.json"
Invoke-ProfilePythonLog -PythonBin $manifest.python `
    -ScriptArgs @("ops/eval_recall_tuning_hint.py", "--artifact", $guardedRecall, "--out", $guardedHint) `
    -Log (Join-Path $ProfileDir "eval_recall_guarded_tuning_hint.log") `
    -FailureMessage "guarded tuning hint generation failed"

$routedRecall = Join-Path $ProfileDir "eval_recall_routed.json"
Invoke-ProfilePythonLog -PythonBin $manifest.python `
    -ScriptArgs @("tests/eval_recall.py", "--mode", "all", "--signal-policy", "routed", "--out", $routedRecall) `
    -Log (Join-Path $ProfileDir "eval_recall_routed.log") `
    -FailureMessage "routed recall evaluation failed"

$routedHint = Join-Path $ProfileDir "eval_recall_routed_tuning_hint.json"
Invoke-ProfilePythonLog -PythonBin $manifest.python `
    -ScriptArgs @("ops/eval_recall_tuning_hint.py", "--artifact", $routedRecall, "--out", $routedHint) `
    -Log (Join-Path $ProfileDir "eval_recall_routed_tuning_hint.log") `
    -FailureMessage "routed tuning hint generation failed"

$policyGatePath = Join-Path $ProfileDir "recall_policy_gate.json"
Invoke-ProfilePythonLog -PythonBin $manifest.python `
    -ScriptArgs @("ops/recall_policy_gate.py", "--raw", $recallStep.artifact, "--guarded", $guardedRecall, "--routed", $routedRecall, "--out", $policyGatePath) `
    -Log (Join-Path $ProfileDir "recall_policy_gate.log") `
    -FailureMessage "recall policy gate generation failed"

$policyGate = Get-Content -Path $policyGatePath -Raw | ConvertFrom-Json
$policyRecommended = $policyGate.promotion.recommended_default
$policyPreflightPath = Join-Path $ProfileDir "recall_policy_preflight.json"
Invoke-ProfilePythonLog -PythonBin $manifest.python `
    -ScriptArgs @("ops/recall_policy_preflight.py", "--policy-gate", $policyGatePath, "--target-policy", $policyRecommended, "--out", $policyPreflightPath) `
    -Log (Join-Path $ProfileDir "recall_policy_preflight.log") `
    -FailureMessage "recall policy preflight failed"

$recall = Get-Content -Path $recallStep.artifact -Raw | ConvertFrom-Json
$guarded = Get-Content -Path $guardedRecall -Raw | ConvertFrom-Json
$routed = Get-Content -Path $routedRecall -Raw | ConvertFrom-Json
$hint = Get-Content -Path $profileHint -Raw | ConvertFrom-Json
$policyPreflight = Get-Content -Path $policyPreflightPath -Raw | ConvertFrom-Json
$summary = [ordered]@{
    run_at = $manifest.run_at
    python = $manifest.python
    python_version = $manifest.python_version
    embedder = $manifest.embedder
    suite = $manifest.suite
    out_dir = $manifest.out_dir
    n_memories = $recall.meta.n_memories
    result_summary = $recall.result_summary
    raw_recall_artifact = $recallStep.artifact
    guarded_recall_artifact = $guardedRecall
    routed_recall_artifact = $routedRecall
    guarded_result_summary = $guarded.result_summary
    routed_result_summary = $routed.result_summary
    recommendations_count = @($recall.recommendations).Count
    tuning_risk = $hint.risk
    tuning_next_actions = @($hint.next_actions).Count
    policy_gate_artifact = $policyGatePath
    policy_gate = $policyGate.gate
    policy_recommended_default = $policyGate.promotion.recommended_default
    raw_lifecycle_allowed = $policyGate.promotion.raw_lifecycle_allowed
    policy_preflight_artifact = $policyPreflightPath
    policy_preflight = $policyPreflight.status
    policy_preflight_target = $policyPreflight.target_policy
}

$summaryPath = Join-Path $ProfileDir "summary.json"
$summary | ConvertTo-Json -Depth 8 | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "[bench_profile.ps1] done"
Write-Host "  manifest: $manifestPath"
Write-Host "  summary:  $summaryPath"
