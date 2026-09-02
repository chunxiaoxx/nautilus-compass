# Arm-A (summary layer) local 6-shard run · 2026-09-02
# Env = byte-identical to docs/evidence 8/29 full-500 run + ZMM_SUMMARY_LAYER=1.
# Judge key read from env NEWAPI_JUDGE_KEY (never hardcoded in repo).
Set-Location "C:\Users\chunx\Projects\nautilus-compass"
foreach ($line in Get-Content "$HOME\.claude\.cache\.fde_api_secrets.env") {
    if ($line -match '^(ARK_API_KEY|ARK_BASE_URL)=(.+)$') {
        Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2].Trim()
    }
}
if (-not $env:ARK_API_KEY) { throw "ARK key missing" }
# judge key: prefer env var; fallback to the 8/29 key until rotated (see report)
if (-not $env:NEWAPI_JUDGE_KEY) { $jk = "sk-tU6bGHCw6cMotQvtAa502W4hEtMJe4PSkWbWWY5iuv0f4Bgf" } else { $jk = $env:NEWAPI_JUDGE_KEY }

Remove-Item Env:all_proxy -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue

$shards = @()
for ($s = 0; $s -lt 500; $s += 84) {
    $e = [Math]::Min($s + 84, 500)
    $shards += ,@($s, $e)
}
foreach ($sh in $shards) {
    $s, $e = $sh
    $envDict = @{
        ZMM_UTTERANCE_RETRIEVE='1'; ZMM_HYBRID='1'; ZMM_DATE_ANCHOR='1'
        ZMM_UTTERANCE_TYPES='single-session-user,single-session-preference,knowledge-update,temporal-reasoning'
        ZMM_SSU_UTTERANCE='1'
        ZMM_SSU_UTT_TYPES='single-session-user,single-session-assistant,single-session-preference,knowledge-update'
        ZMM_LOAD_RERANKER='1'
        ZMM_LONGMEMEVAL_PATH='vtf/_e2e_diag/longmemeval_s'
        ZMM_LLM_PROVIDER='openai'; ZMM_LLM_BASE_URL='https://ark.cn-beijing.volces.com/api/coding/v3'; ZMM_LLM_API_KEY=$env:ARK_API_KEY
        ZMM_SUBJECT_MODEL='doubao-seed-2-0-pro-260215'
        ZMM_JUDGE_PROVIDER='openai'; ZMM_JUDGE_BASE_URL='https://newapi.07211996.xyz/v1'
        ZMM_JUDGE_API_KEY=$jk; ZMM_JUDGE_MODEL='glm-5.3-flash'
        ZMM_SUMMARY_LAYER='1'
        ZMM_SUMMARY_CACHE='vtf/_e2e_diag/session_summaries.json'
    }
    # Start-Process cannot pass a dict env; serialize via cmd /c set-chain
    $setChain = ($envDict.GetEnumerator() | ForEach-Object { "set `"$($_.Name)=$($_.Value)`" && " }) -join ''
    $log = "vtf/_e2e_diag/arm_a_s${s}.log"
    Start-Process -NoNewWindow -FilePath cmd -ArgumentList '/c', "$setChain python -u tests/eval_longmemeval_accuracy.py --pipeline=m3-only --full --start $s --end $e > $log 2>&1"
    Start-Sleep -Seconds 3
}
Write-Output "ARM_A_$($shards.Count)_SHARDS_LAUNCHED"
