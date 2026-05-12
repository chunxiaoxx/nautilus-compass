# Local BGE daemon launcher · for Windows Task Scheduler / service
# ================================================================
# Spawns daemon.py on local GPU · keeps it running across logoff
#
# Usage (one-shot · foreground for debug):
#   . 'C:\Users\chunx\.claude\plugins\nautilus-compass\ops\local_daemon_start.ps1'
#   Start-LocalCompassDaemon -Foreground
#
# Usage (background · production):
#   Start-LocalCompassDaemon
#
# Usage (Task Scheduler at logon):
#   Action: powershell.exe
#   Arguments: -NoProfile -WindowStyle Hidden -File "C:\Users\chunx\.claude\plugins\nautilus-compass\ops\local_daemon_start.ps1" -Start
#   Trigger: At log on (with delay 30s)

param(
    [switch]$Foreground,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status
)

$script:DaemonScript = "C:\Users\chunx\.claude\plugins\nautilus-compass\.cache\cloud-daemon.py"
$script:CacheDir     = "C:\Users\chunx\.claude\plugins\nautilus-compass\.cache"
$script:LogFile      = Join-Path $script:CacheDir "local-daemon.log"
$script:PidFile      = Join-Path $script:CacheDir "local-daemon.pid"
$script:DaemonPort   = 9876

# Env passed to daemon (matches cloud production · CUDA auto-pick)
$script:DaemonEnv = @{
    PYTHONIOENCODING        = "utf-8"
    PYTHONUTF8              = "1"
    PYTHONUNBUFFERED        = "1"
    ZMM_NEG_HIT_THRESHOLD   = "0.65"     # matches cloud
    # ZMM_DEVICE not set · daemon auto-picks cuda (line 130)
    # ZMM_EMBEDDER_MODEL not set · daemon defaults to BAAI/bge-m3
}


function Test-LocalDaemonAlive {
    $c = New-Object System.Net.Sockets.TcpClient
    try {
        $t = $c.ConnectAsync("127.0.0.1", $script:DaemonPort)
        if ($t.Wait(1500)) { return $c.Connected }
        return $false
    } catch {
        return $false
    } finally { $c.Close() }
}


function Start-LocalCompassDaemon {
    [CmdletBinding()]
    param([switch]$Foreground)

    if (Test-LocalDaemonAlive) {
        Write-Host "[compass-local] daemon already alive on 127.0.0.1:$($script:DaemonPort)" -ForegroundColor Green
        return
    }

    if (-not (Test-Path $script:DaemonScript)) {
        Write-Warning "[compass-local] daemon script missing: $($script:DaemonScript)"
        return
    }

    if (-not (Test-Path $script:CacheDir)) {
        New-Item -ItemType Directory -Path $script:CacheDir -Force | Out-Null
    }

    $py = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $py) {
        Write-Warning "[compass-local] python not on PATH"
        return
    }

    # Apply env
    foreach ($k in $script:DaemonEnv.Keys) {
        Set-Item -Path "env:$k" -Value $script:DaemonEnv[$k]
    }

    if ($Foreground) {
        Write-Host "[compass-local] foreground · log goes to console + $($script:LogFile)" -ForegroundColor Cyan
        & $py $script:DaemonScript
        return
    }

    Write-Host "[compass-local] starting daemon · log: $($script:LogFile)" -ForegroundColor Cyan
    $args = @($script:DaemonScript)
    $p = Start-Process -FilePath $py `
                       -ArgumentList $args `
                       -WorkingDirectory $script:CacheDir `
                       -WindowStyle Hidden `
                       -RedirectStandardOutput $script:LogFile `
                       -RedirectStandardError ($script:LogFile + ".err") `
                       -PassThru

    Start-Sleep -Seconds 3
    if ($p.HasExited) {
        Write-Warning "[compass-local] daemon exited immediately (code $($p.ExitCode)) · check $($script:LogFile).err"
        return
    }
    $p.Id | Out-File -FilePath $script:PidFile -Encoding ascii

    # Wait up to 60s for model load + port bind
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        if (Test-LocalDaemonAlive) {
            Write-Host "[compass-local] daemon UP · pid=$($p.Id) · port $($script:DaemonPort)" -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 2
    }
    Write-Warning "[compass-local] daemon spawned (pid $($p.Id)) but port $($script:DaemonPort) not listening after 60s · BGE model load may still be running · check log"
}


function Stop-LocalCompassDaemon {
    if (Test-Path $script:PidFile) {
        $daemonPid = Get-Content $script:PidFile -ErrorAction SilentlyContinue
        if ($daemonPid) {
            Stop-Process -Id $daemonPid -Force -ErrorAction SilentlyContinue
            Remove-Item $script:PidFile -ErrorAction SilentlyContinue
            Write-Host "[compass-local] stopped pid=$daemonPid" -ForegroundColor Yellow
            return
        }
    }
    Write-Host "[compass-local] no pid file · daemon may not be running" -ForegroundColor DarkGray
}


function Get-LocalCompassDaemonStatus {
    if (Test-LocalDaemonAlive) {
        $daemonPid = if (Test-Path $script:PidFile) { Get-Content $script:PidFile -ErrorAction SilentlyContinue } else { "?" }
        Write-Host "[compass-local] UP · pid=$daemonPid · port=$($script:DaemonPort)" -ForegroundColor Green
        if (Test-Path $script:LogFile) {
            Write-Host "[compass-local] recent log:" -ForegroundColor DarkGray
            Get-Content $script:LogFile -Tail 5 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
        }
    } else {
        Write-Host "[compass-local] DOWN · port $($script:DaemonPort) not listening" -ForegroundColor Yellow
    }
}


# Dispatch when run as script
if ($Start)      { Start-LocalCompassDaemon; return }
if ($Stop)       { Stop-LocalCompassDaemon; return }
if ($Status)     { Get-LocalCompassDaemonStatus; return }
if ($Foreground) { Start-LocalCompassDaemon -Foreground; return }
