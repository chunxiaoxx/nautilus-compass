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
    "nautilus"   = "C:\Users\chunx\Projects\nautilus-core"
    "vdr"        = "C:\Users\chunx\venture_daily_report"
    "venture"    = "C:\Users\chunx\venture_daily_report"
    "zen"        = "C:\Users\chunx\quantum-buddha-project"
    "zenmind"    = "C:\Users\chunx\quantum-buddha-project"
    "chunx"      = "C:\Users\chunx"
    "compass"    = "C:\Users\chunx"
    "hr"         = "C:\Users\chunx"
    "agent"      = "C:\Users\chunx\Projects\nautilus-v5"
    "superagent" = "C:\Users\chunx\Projects\nautilus-v5"
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
    Write-Host "[compass] starting SSH tunnel to $($script:CompassCloudHost) (-L 9877 MCP · daemon on cloud CPU box)" -ForegroundColor Cyan
    #   -L 9877 · local→cloud  · MCP TCP transport (Claude Code uses)
    # (2026-07-14) compass daemon now runs on the `cloud` CPU server itself
    #   (T4 GPU box retired). Reverse tunnel -R 9876 removed: there is no local
    #   GPU BGE daemon to expose, and with ExitOnForwardFailure=yes that stale
    #   reverse forward also killed the tunnel outright.
    # keepalive · prevents NAT/firewall from killing idle tunnel
    # ExitOnForwardFailure · die fast if port already bound rather than silent zombie
    #
    # NOTE (2026-07-14): launch WITHOUT -Wait and WITHOUT -f. On Windows,
    #   `Start-Process ssh -f... -Wait` never returns — Start-Process keeps
    #   waiting on the backgrounded ssh and cstart hangs forever right after
    #   printing the line above. We run `-N` as a hidden background process and
    #   poll Test-CompassTunnel to confirm the forward bound.
    $args = @(
        "-N",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes",
        "-L", "$($script:CompassCloudPort):127.0.0.1:9877",
        $script:CompassCloudHost
    )
    Start-Process -WindowStyle Hidden -FilePath "ssh" -ArgumentList $args | Out-Null
    # poll up to ~6s for the local forward to come up
    for ($i = 0; $i -lt 12; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-CompassTunnel) {
            Write-Host "[compass] tunnel up on 127.0.0.1:$($script:CompassCloudPort) · MCP wire OK" -ForegroundColor Green
            return $true
        }
    }
    Write-Warning "[compass] tunnel did not come up · Claude Code will still launch but MCP will fail"
    return $false
}

function ctunnel {
    # mid-session tunnel revive · use when /mcp says Failed -32000 or × failed
    # then run `/mcp reconnect` in Claude Code without exiting the dialog
    if (Test-CompassTunnel) {
        Write-Host "[compass] tunnel already UP on 127.0.0.1:$($script:CompassCloudPort)" -ForegroundColor Green
        return
    }
    Start-CompassTunnel | Out-Null
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

# ────────────────────────────────────────────────────────────────────
# Top-level shortcuts · just type the project name to launch its dialog
#   nautilus  → C:\Users\chunx\Projects\nautilus-core\phase3
#   venture   → C:\Users\chunx\venture_daily_report      (创投日报)
#   zen       → C:\Users\chunx\quantum-buddha-project    (禅心)
#   chunx     → C:\Users\chunx                           (compass + HR)
# Each one auto-ensures the SSH tunnel to cloud:9877 then launches
# `claude --dangerously-skip-permissions`. Type /resume after launch.
# ────────────────────────────────────────────────────────────────────

function nautilus { cstart nautilus }
function venture  { cstart vdr      }
function zen      { cstart zen      }
function chunx    { cstart chunx    }
function hr       { cstart hr       }
function agent    { cstart agent    }

