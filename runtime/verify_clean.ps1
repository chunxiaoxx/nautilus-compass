$srv = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -match 'http\.server 18099' }
"18099 after 20s: $($srv.Count)"
$bash = Get-CimInstance Win32_Process -Filter "Name='bash.exe'" | Where-Object { $_.CommandLine -match 'http\.server 18099' }
"stuck bash left: $($bash.Count)"
if ($bash) { $bash | ForEach-Object { "  bash $($_.ProcessId) created $($_.CreationDate.ToString('MM-dd HH:mm'))" } }
$py = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Sort-Object WorkingSetSize -Descending | Select-Object -First 6 | ForEach-Object { '{0,7} {1,6:N0}MB  {2}' -f $_.ProcessId, ($_.WorkingSetSize/1MB), (($_.CommandLine -replace '\s+',' ').Substring(0,[Math]::Min(80,$_.CommandLine.Length))) }
$py
$tot = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Measure-Object WorkingSet64 -Sum
"python total: {0:N2} GB in {1} procs" -f ($tot.Sum/1GB), $tot.Count
