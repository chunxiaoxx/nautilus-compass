# Detached summary-card generation (survives the bash 120s window)
# Git-bash passes both ALL_PROXY and all_proxy -> Start-Process env dict clash
Remove-Item Env:all_proxy -ErrorAction SilentlyContinue
Remove-Item Env:http_proxy -ErrorAction SilentlyContinue
Remove-Item Env:https_proxy -ErrorAction SilentlyContinue
$envFile = "$HOME\.claude\.cache\.fde_api_secrets.env"
foreach ($line in Get-Content $envFile) {
    if ($line -match '^ARK_API_KEY=(.+)$') { $env:OPENAI_API_KEY = $Matches[1].Trim() }
}
if (-not $env:OPENAI_API_KEY) { throw "ARK_API_KEY not found" }
Set-Location "C:\Users\chunx\Projects\nautilus-compass"
Start-Process -NoNewWindow -FilePath python `
  -ArgumentList '-u','vtf/build_session_summaries.py',
    '--dataset','vtf/_e2e_diag/longmemeval_s',
    '--ids-file','vtf/_e2e_diag/summary_ids.txt',
    '--workers','6' `
  -RedirectStandardOutput 'vtf/_e2e_diag/summary_gen.log' `
  -RedirectStandardError 'vtf/_e2e_diag/summary_gen.err'
Write-Output "LAUNCHED"
