Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'singleton' } | ForEach-Object {
  '{0} | created {1} | {2}' -f $_.ProcessId, $_.CreationDate.ToString('yyyy-MM-dd HH:mm:ss'), (($_.CommandLine -replace '\s+',' ').Substring(0,[Math]::Min(120,($_.CommandLine).Length)))
}
