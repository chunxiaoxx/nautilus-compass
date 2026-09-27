$pids = @(26088,13176,16104,26404,23580,21236,30160,6240,13156,26296)
foreach ($p in $pids) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$p" -ErrorAction SilentlyContinue
  if (-not $proc) { "{0,7}  (already gone)" -f $p; continue }
  $c = ($proc.CommandLine -replace '\s+',' ')
  if ($c -match 'http\.server 18099|_run_v5_api_18001') {
    "{0,7}  KILL  {1}" -f $p, $c.Substring(0,[Math]::Min(90,$c.Length))
    Stop-Process -Id $p -Force -Confirm:$false
  } else {
    "{0,7}  SKIP (cmd mismatch): {1}" -f $p, $c.Substring(0,[Math]::Min(90,$c.Length))
  }
}
