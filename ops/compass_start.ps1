# compass-cloud quick start · PowerShell function
# ================================================
# Usage after install:
#   cstart                 → defaults to nautilus
#   cstart nautilus
#   cstart vdr             → venture_daily_report
#   cstart zen             → zenmind
#   cstart chunx           → C:\Users\chunx
#   cstart paths           → list current path map
#   cstop                  → kill the SSH tunnel (rarely needed)
#
# Flow per call:
#   1. test TCP 127.0.0.1:9877 · if dead, start `ssh -fN -L 9877:127.0.0.1:9877 cloud`
#   2. cd to project dir
#   3. exec `claude --dangerously-skip-permissions`
#
# Install (one time):
#   1. Edit $PROFILE to dot-source this file:
#        echo ". 'C:\Users\chunx\.claude\plugins\nautilus-compass\ops\compass_start.ps1'" >> $PROFILE
#   2. Reload profile or open new PowerShell:
#        . $PROFILE
#   3. Edit $CompassProjectPaths below if any path is wrong
#
# Note: After Claude Code launches, type /resume yourself to continue
#       the prior session (this script does not auto-/resume).

$script:CompassProjectPaths = @{
    "nautilus"   = "C:\Users\chunx\Projects\nautilus-core\phase3"
    "vdr"        = "C:\Users\chunx\venture_daily_report"
    "venture"    = "C:\Users\chunx\venture_daily_report"
    "zen"        = "C:\Users\chunx\quantum-buddha-project"
    "zenmind"    = "C:\Users\chunx\quantum-buddha-project"
    "chunx"      = "C:\Users\chunx"
    "compass"    = "C:\Users\chunx\.claude\plugins\nautilus-compass"
}

$script:CompassCloudPort = 9877
$script:CompassCloudHost = "cloud"

function Test-CompassTunnel {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $task = $client.ConnectAsync("127.0.0.1", $script:CompassCloudPort)
        if ($task.Wait(1500)) {
            return $client.Connected
        }
        return $false
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Start-CompassTunnel {
    if (Test-CompassTunnel) {
        Write-Host "[compass] tunnel already up on 127.0.0.1:$($script:CompassCloudPort)" -ForegroundColor DarkGray
        return $true
    }
    Write-Host "[compass] starting SSH tunnel to $($script:CompassCloudHost):9877..." -ForegroundColor Cyan
    $args = @("-fN", "-L", "$($script:CompassCloudPort):127.0.0.1:9877", $script:CompassCloudHost)
    Start-Process -WindowStyle Hidden -FilePath "ssh" -ArgumentList $args -Wait
    Start-Sleep -Milliseconds 800
    if (Test-CompassTunnel) {
        Write-Host "[compass] tunnel up" -ForegroundColor Green
        return $true
    }
    Write-Warning "[compass] tunnel did not come up · Claude Code will still launch but nautilus-compass-cloud MCP will fail to connect"
    return $false
}

function cstop {
    # ssh -fN forks a background daemon · find and kill on Windows by command line match
    $procs = Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "9877:127\.0\.0\.1:9877" }
    if (-not $procs) {
        Write-Host "[compass] no tunnel process found" -ForegroundColor DarkGray
        return
    }
    foreach ($p in $procs) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[compass] killed ssh tunnel PID $($p.ProcessId)" -ForegroundColor Yellow
    }
}

function cstart {
    [CmdletBinding()]
    param(
        [Parameter(Position=0)]
        [string]$Project = "nautilus"
    )

    if ($Project -eq "paths" -or $Project -eq "list") {
        Write-Host "Available projects:" -ForegroundColor Cyan
        foreach ($k in $script:CompassProjectPaths.Keys | Sort-Object) {
            $exists = if (Test-Path $script:CompassProjectPaths[$k]) { "[OK]" } else { "[MISSING]" }
            "  {0,-10} -> {1,-50} {2}" -f $k, $script:CompassProjectPaths[$k], $exists | Write-Host
        }
        return
    }

    if (-not $script:CompassProjectPaths.ContainsKey($Project)) {
        Write-Warning "[compass] unknown project '$Project'"
        Write-Host "Try: cstart paths" -ForegroundColor DarkGray
        return
    }

    $dir = $script:CompassProjectPaths[$Project]
    if (-not (Test-Path $dir)) {
        Write-Warning "[compass] path does not exist: $dir"
        Write-Host "Edit `$CompassProjectPaths in compass_start.ps1" -ForegroundColor DarkGray
        return
    }

    Start-CompassTunnel | Out-Null

    Write-Host "[compass] cd $dir" -ForegroundColor DarkGray
    Set-Location $dir

    Write-Host "[compass] launching Claude Code (type /resume to continue last session)" -ForegroundColor Green
    & claude --dangerously-skip-permissions
}

# Optional alias if `cstart` is too generic for you
Set-Alias -Name ccc -Value cstart -Description "Compass Cloud Claude shortcut"
