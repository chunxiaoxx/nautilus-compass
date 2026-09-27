Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Sort-Object WorkingSetSize -Descending | Select-Object -First 12 | ForEach-Object {
  $c = ($_.CommandLine -replace '\s+',' ')
  '{0,7} {1,6:N0}MB  {2}' -f $_.ProcessId, ($_.WorkingSetSize/1MB), $c.Substring(0,[Math]::Min(130,$c.Length))
}
Write-Output '--- scheduled tasks ---'
Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'} | ForEach-Object {
  $a = $_.Actions | Select-Object -First 1
  if ($a.Execute -match 'python|bash' -or $_.TaskName -match 'nautilus|compass|daemon|hud|watch|v5') { $_.TaskName + '  =>  ' + $a.Execute + ' ' + $a.Arguments }
}
