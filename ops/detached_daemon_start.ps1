# Detached daemon starter · 2026-09-15
# ================================================================
# 9/15 死因专项结论:daemon 三连死均为"宿主控制台连坐"(无崩溃记录/无 OOM 事件/
# 无 traceback,daemon 与 v5 python 同批蒸发)。旧链 nohup python 在 Windows 上
# 仍挂 bash 控制台对象,关窗/会话树关闭即连坐。
# 本启动器:pythonw(无控制台)+ Start-Process(独立进程对象)→ 控制台杀手免疫。
# 幂等:活着就退出;半死(端口在听无响应)先精确清场再拉起。
$ErrorActionPreference = 'Continue'
$Dir      = 'C:\Users\chunx\.claude\plugins\nautilus-compass'
$Pythonw  = "$env:LOCALAPPDATA\Microsoft\WindowsApps\pythonw.exe"
$LogFile  = Join-Path $Dir '.cache\detached_wd.log'
$TokenFile = Join-Path $HOME '.claude\.cache\compass_daemon_token'

function Write-Log([string]$m) {
  try { [System.IO.File]::AppendAllText($LogFile, "$(Get-Date -Format 'MM-dd HH:mm:ss') $m`r`n") } catch {}
}

function Test-DaemonAlive {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $t = $c.ConnectAsync('127.0.0.1', 9876); if (-not $t.Wait(1500)) { $c.Close(); return $false }
    $tok = (Get-Content $TokenFile -Raw).Trim()
    $s = $c.GetStream(); $s.ReadTimeout = 3000
    $req = ('{"action":"ping","token":"' + $tok + '"}' + "`n")   # ping 必带 \n(9/8 gotcha)
    $b = [System.Text.Encoding]::UTF8.GetBytes($req)
    $s.Write($b, 0, $b.Length)
    $buf = New-Object byte[] 2048
    $n = $s.Read($buf, 0, $buf.Length); $c.Close()
    return ([System.Text.Encoding]::UTF8.GetString($buf, 0, $n) -match '"ok"')
  } catch { return $false }
}

if (Test-DaemonAlive) { Write-Log 'alive · no-op'; exit 0 }

# 半死清场:端口在听但不响应 → 只杀持端口的那个 PID(精确,不按映像名)
$conn = Get-NetTCPConnection -LocalPort 9876 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn -and $conn.OwningProcess) {
  Write-Log ("half-dead PID {0} · precise kill" -f $conn.OwningProcess)
  Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
}

if (-not (Test-Path $Pythonw)) { Write-Log "pythonw missing: $Pythonw"; exit 1 }
Start-Process -FilePath $Pythonw -ArgumentList "`"$Dir\daemon.py`"" -WorkingDirectory $Dir -WindowStyle Hidden
Write-Log 'started detached (pythonw)'
