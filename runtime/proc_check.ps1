Write-Output "=== Python processes (by memory) ==="
Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Sort-Object WorkingSetSize -Descending | Select-Object -First 12 | ForEach-Object {
  $mb = [math]::Round($_.WorkingSetSize/1MB)
  $cmd = ($_.CommandLine -replace '\s+',' ').Substring(0, [Math]::Min(120, $_.CommandLine.Length))
  "$($_.ProcessId) ${mb}MB $cmd"
}
Write-Output ""
Write-Output "=== Port listeners (18889/18001/9876/9224/9225) ==="
foreach ($port in @(18889, 18001, 9876, 9224, 9225)) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if ($conns) { foreach ($c in $conns) { "port $port -> PID $($c.OwningProcess)" } }
  else { "port $port -> free" }
}
Write-Output ""
Write-Output "=== Total python memory ==="
$pyTotal = (Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Measure-Object WorkingSet64 -Sum).Sum / 1MB
Write-Output ("Python total: {0:N0} MB" -f $pyTotal)
