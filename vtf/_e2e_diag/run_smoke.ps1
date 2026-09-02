# Smoke one ms question (idx 70) through the full Arm-A chain
Set-Location "C:\Users\chunx\Projects\nautilus-compass"
foreach ($line in Get-Content "$HOME\.claude\.cache\.fde_api_secrets.env") {
    if ($line -match '^(ARK_API_KEY|ARK_BASE_URL)=(.+)$') {
        Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2].Trim()
    }
}
$jk = "sk-tU6bGHCw6cMotQvtAa502W4hEtMJe4PSkWbWWY5iuv0f4Bgf"
Remove-Item Env:all_proxy -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
$setChain = "set ZMM_UTTERANCE_RETRIEVE=1&& set ZMM_HYBRID=1&& set ZMM_DATE_ANCHOR=1&& " +
  "set ZMM_UTTERANCE_TYPES=single-session-user,single-session-preference,knowledge-update,temporal-reasoning&& " +
  "set ZMM_SSU_UTTERANCE=1&& " +
  "set ZMM_SSU_UTT_TYPES=single-session-user,single-session-assistant,single-session-preference,knowledge-update&& " +
  "set ZMM_LOAD_RERANKER=1&& set ZMM_LONGMEMEVAL_PATH=vtf/_e2e_diag/longmemeval_s&& " +
  "set ZMM_LLM_PROVIDER=openai&& set ZMM_LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3&& set ZMM_LLM_API_KEY=$env:ARK_API_KEY&& " +
  "set ZMM_SUBJECT_MODEL=doubao-seed-2-0-pro-260215&& " +
  "set ZMM_JUDGE_PROVIDER=openai&& set ZMM_JUDGE_BASE_URL=https://newapi.07211996.xyz/v1&& " +
  "set ZMM_JUDGE_API_KEY=$jk&& set ZMM_JUDGE_MODEL=glm-5.3-flash&& " +
  "set ZMM_SUMMARY_LAYER=1&& set ZMM_SUMMARY_CACHE=vtf/_e2e_diag/session_summaries.json&& "
Start-Process -NoNewWindow -FilePath cmd -ArgumentList '/c', "$setChain python -u tests/eval_longmemeval_accuracy.py --pipeline=m3-only --full --start 70 --end 71 > vtf/_e2e_diag/smoke_q70.log 2>&1"
Write-Output "SMOKE_LAUNCHED"
