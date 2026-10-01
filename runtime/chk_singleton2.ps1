Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'singleton' -and $_.Name -match 'python|cmd' } | ForEach-Object {
  $c = ($_.CommandLine -replace '\s+',' ')
  '{0} | created {1} | {2}' -f $_.ProcessId, $_.CreationDate.ToString('yyyy-MM-dd HH:mm:ss'), $c.Substring(0, [Math]::Min(130, $c.Length))
}
