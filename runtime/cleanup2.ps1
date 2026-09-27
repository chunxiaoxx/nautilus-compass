# 1) 杀 5 个僵死 bash(卡在 scp 12h+,泄漏源)
foreach ($p in @(17588,28060,13604,13112,23324)) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$p" -ErrorAction SilentlyContinue
  if ($proc -and $proc.CommandLine -match 'http\.server 18099') {
    Stop-Process -Id $p -Force -Confirm:$false
    "killed stuck bash $p"
  } else { "bash $p gone or mismatch" }
}
# 2) 清剩余 http.server 18099
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -match 'http\.server 18099' } | ForEach-Object {
  Stop-Process -Id $_.ProcessId -Force -Confirm:$false
  "killed 18099 orphan $($_.ProcessId)"
}
Start-Sleep -Seconds 5
# 3) 验证是否重生
$left = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -match 'http\.server 18099' }
"after cleanup, 18099 procs left: $($left.Count)"
$bash = Get-CimInstance Win32_Process -Filter "Name like 'bash%'" | Where-Object { $_.CommandLine -match '18099' }
"stuck bash left: $($bash.Count)"
