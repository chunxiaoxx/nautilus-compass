foreach ($p in @(17588,28060,13604,13112,23324)) {
  $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$p" -ErrorAction SilentlyContinue
  if ($proc) {
    "=== bash $p (created {0}, {1:N0}MB) ===" -f $proc.CreationDate.ToString('MM-dd HH:mm'), ($proc.WorkingSetSize/1MB)
    $proc.CommandLine
  } else { "=== bash $p gone ===" }
}
