# Compass watchdog v2 (2026-09-01) · 一次性脚本 · 由计划任务每 5min 跑。
# 两段:
#   [daemon]  本地 9876 ping 探活(ping 免鉴权)→ 死则 daemon_start.sh 拉起 → 复验。
#             补 6/29 起 watchdog 计划任务消失、SessionStart hook 之外无人守望的缺口
#             (8/31 daemon 静默死 4.4h 实证)。
#   [forward] 9877 隧道 → 云 compass-mcp-tcp:env 有 COMPASS_CLOUD_TOKEN 时发 MCP
#             initialize 强验证;无 env 只做 TCP connect 弱验证(避免无 token 被拒误报)。
#             死则 ssh 起远程 service → 仍死则重生隧道。
# 旧版问题(2026-05-27 G13):明文 token 硬编码(本次删除,token 只从 env 读)。
$ErrorActionPreference = 'Continue'
$Log = 'C:\Users\chunx\.claude\plugins\nautilus-compass\.cache\forward_watchdog.log'
$Port = 9877
$CloudHost = 'cloud'
$Token = $env:COMPASS_CLOUD_TOKEN
$GitBash = 'C:\Program Files\Git\bin\bash.exe'
$DaemonStart = 'C:\Users\chunx\.claude\plugins\nautilus-compass\daemon_start.sh'

function Write-Log([string]$m) {
    $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    try { [System.IO.File]::AppendAllText($Log, "$ts $m`r`n", [System.Text.Encoding]::UTF8) } catch {}
}

# ─── 段 1 · 本地 daemon 9876 ──────────────────────────────────────
function Test-Daemon {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        $t = $c.ConnectAsync('127.0.0.1', 9876)
        if (-not $t.Wait(2000)) { return $false }
        $s = $c.GetStream(); $s.WriteTimeout = 3000; $s.ReadTimeout = 3000
        $p = [System.Text.Encoding]::UTF8.GetBytes('{"action":"ping"}' + "`n")
        $s.Write($p, 0, $p.Length)
        $buf = New-Object byte[] 256
        $n = $s.Read($buf, 0, $buf.Length)
        return ($n -gt 0 -and [System.Text.Encoding]::UTF8.GetString($buf, 0, $n) -match 'pong')
    } catch { return $false } finally { $c.Close() }
}

if (Test-Daemon) {
    Write-Log '[daemon] OK'
} else {
    Write-Log '[daemon] DOWN · starting via daemon_start.sh'
    if (Test-Path $GitBash) {
        Start-Process -FilePath $GitBash -ArgumentList @($DaemonStart) -WindowStyle Hidden
    } else {
        Start-Process -FilePath 'bash' -ArgumentList @($DaemonStart) -WindowStyle Hidden
    }
    Start-Sleep -Seconds 20
    if (Test-Daemon) { Write-Log '[daemon] UP after start' } else { Write-Log '[daemon] STILL DOWN · needs manual check (BGE cold load may take longer)' }
}

# ─── 段 2 · 9877 forward → 云 compass-mcp-tcp ─────────────────────
function Test-Forward {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        $t = $c.ConnectAsync('127.0.0.1', $Port)
        if (-not $t.Wait(2000)) { return $false }
        if (-not $Token) { return $true }   # 弱验证:端口在听即可(无 env token 时)
        $s = $c.GetStream(); $s.WriteTimeout = 5000; $s.ReadTimeout = 5000
        $obj = @{ jsonrpc = '2.0'; id = 1; method = 'initialize'; params = @{ authToken = $Token; protocolVersion = '2024-11-05'; capabilities = @{}; clientInfo = @{ name = 'fwd-wd'; version = '2' } } }
        $req = ($obj | ConvertTo-Json -Compress -Depth 6) + "`n"
        $p = [System.Text.Encoding]::UTF8.GetBytes($req)
        $s.Write($p, 0, $p.Length)
        $buf = New-Object byte[] 2048
        $n = $s.Read($buf, 0, $buf.Length)
        if ($n -le 0) { return $false }
        return ([System.Text.Encoding]::UTF8.GetString($buf, 0, $n) -match '"result"')
    } catch { return $false } finally { $c.Close() }
}

if (Test-Forward) { Write-Log '[forward] OK'; exit 0 }

Write-Log '[forward] DOWN · starting remote compass-mcp-tcp.service'
& ssh -o ConnectTimeout=10 -o BatchMode=yes $CloudHost 'sudo systemctl start compass-mcp-tcp.service' 2>$null
Start-Sleep -Seconds 3
if (Test-Forward) { Write-Log '[forward] UP after remote service start'; exit 0 }

Write-Log '[forward] still down after remote start · respawning tunnel'
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match '-R\s+9876:' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
Start-Process -FilePath 'ssh' -WindowStyle Hidden -ArgumentList @(
    '-fN', '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
    '-o', 'ExitOnForwardFailure=yes', '-L', '9877:127.0.0.1:9877', '-R', '9876:127.0.0.1:9876', 'cloud'
)
Start-Sleep -Seconds 3
if (Test-Forward) { Write-Log '[forward] UP after tunnel respawn' } else { Write-Log '[forward] STILL DOWN after all heals · needs manual check' }
