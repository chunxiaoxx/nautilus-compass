# Forward-path watchdog (2026-05-27 · G13) · 一次性脚本 · 由计划任务每 5min 跑。
# 补 compass_watchdog.ps1 的缺口:它看本地 daemon 9876 + 隧道端口在听 + 反向 9876 zombie,
# 但不探 9877 forward→远程 compass-mcp-tcp.service 是否活(端口在听不代表远程 service 活)。
# 本脚本:发 MCP initialize 探往返 → 死则 ssh 起远程 service → 仍死则重起隧道。
# 一次性(非 infinite loop)· 计划任务调度 · 无进程堆积。
$ErrorActionPreference = 'Continue'
$Log = 'C:\Users\chunx\.claude\plugins\nautilus-compass\.cache\forward_watchdog.log'
$Port = 9877
$CloudHost = 'cloud'
$Token = $env:COMPASS_CLOUD_TOKEN
if (-not $Token) { $Token = 'cmp_claude_code_compass_dialog_58f2e85353fa90b0500e84d6880a1fc0' }

function Write-Log([string]$m) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    try { [System.IO.File]::AppendAllText($Log, "$ts $m`r`n", [System.Text.Encoding]::UTF8) } catch {}
}

function Test-Forward {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        $t = $c.ConnectAsync('127.0.0.1', $Port)
        if (-not $t.Wait(2000)) { return $false }
        $s = $c.GetStream(); $s.WriteTimeout = 5000; $s.ReadTimeout = 5000
        $obj = @{ jsonrpc = '2.0'; id = 1; method = 'initialize'; params = @{ authToken = $Token; protocolVersion = '2024-11-05'; capabilities = @{}; clientInfo = @{ name = 'fwd-wd'; version = '1' } } }
        $req = ($obj | ConvertTo-Json -Compress -Depth 6) + "`n"
        $p = [System.Text.Encoding]::UTF8.GetBytes($req)
        $s.Write($p, 0, $p.Length)
        $buf = New-Object byte[] 2048
        $n = $s.Read($buf, 0, $buf.Length)
        if ($n -le 0) { return $false }
        return ([System.Text.Encoding]::UTF8.GetString($buf, 0, $n) -match '"result"')
    } catch { return $false } finally { $c.Close() }
}

if (Test-Forward) { Write-Log 'forward OK'; exit 0 }

Write-Log 'forward DOWN · starting remote compass-mcp-tcp.service'
& ssh -o ConnectTimeout=10 -o BatchMode=yes $CloudHost 'sudo systemctl start compass-mcp-tcp.service' 2>$null
Start-Sleep -Seconds 3
if (Test-Forward) { Write-Log 'forward UP after remote service start'; exit 0 }

Write-Log 'still down after remote start · respawning tunnel'
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match '-R\s+9876:' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
Start-Process -FilePath 'ssh' -WindowStyle Hidden -ArgumentList @(
    '-fN', '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
    '-o', 'ExitOnForwardFailure=yes', '-L', '9877:127.0.0.1:9877', '-R', '9876:127.0.0.1:9876', 'cloud'
)
Start-Sleep -Seconds 3
if (Test-Forward) { Write-Log 'forward UP after tunnel respawn' } else { Write-Log 'STILL DOWN after all heals · needs manual check' }
