foreach ($p in @(6956,27956,22264,12292,7944)) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$p" -ErrorAction SilentlyContinue
  if ($proc) {
    $par = Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.ParentProcessId)" -ErrorAction SilentlyContinue
    "child {0} <- parent {1} [{2}] {3}" -f $p, $proc.ParentProcessId, ($par.CreationDate.ToString('MM-dd HH:mm')), (($par.CommandLine -replace '\s+',' ').Substring(0,[Math]::Min(110,($par.CommandLine).Length)))
  }
}
