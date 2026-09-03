# Re-judge 71 judge-disconnect questions (task #40) - same env as retry shards
foreach ($line in Get-Content "$HOME\.claude\.cache\.fde_api_secrets.env") {
    if ($line -match '^(ARK_API_KEY)=(.+)$') { Set-Item -Path "Env:ARK_API_KEY" -Value $Matches[2].Trim() }
}
Remove-Item Env:all_proxy -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
Set-Location "C:\Users\chunx\Projects\nautilus-compass"
$chain = "set ZMM_LLM_PROVIDER=openai&& set ZMM_LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/coding/v3&& set ZMM_LLM_API_KEY=$env:ARK_API_KEY&& " +
  "set ZMM_JUDGE_PROVIDER=openai&& set ZMM_JUDGE_BASE_URL=https://newapi.07211996.xyz/v1&& " +
  "set ZMM_JUDGE_API_KEY=sk-tU6bGHCw6cMotQvtAa502W4hEtMJe4PSkWbWWY5iuv0f4Bgf&& set ZMM_JUDGE_MODEL=glm-5.3-flash&& "
Start-Process -NoNewWindow -FilePath cmd -ArgumentList '/c', "${chain}python -u tools/rejudge_errors.py > vtf/_e2e_diag/rejudge_71.log 2>&1"
Write-Output "REJUDGE_LAUNCHED"
