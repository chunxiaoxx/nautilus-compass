# daemon_start.ps1 · v1.1 · Windows PowerShell equivalent of daemon_start.sh
# Starts the V5 Memory Daemon in the background. Idempotent: noop if already up.
#
# v1.1 2026-09-01: race fix (mirror of daemon_start.sh fix):
#   旧逻辑 ping 不通 -> spawn。但新 daemon 冷加载 BGE ~30s 内 ping 必失败,
#   并发调用各自拉一份 -> 2026-08-30 一晚 18 份 x 870MB ≈ 15.7GB 的灾难。
#   修复: ① 独占句柄锁串行化 (持锁者崩溃时 OS 自动关句柄, 天然无 stale lock)
#         ② 锁内复查 ping  ③ spawn 后 120s 冷加载豁免 (marker 文件)
#
# Run from any dir:  powershell -ExecutionPolicy Bypass -File daemon_start.ps1

$ErrorActionPreference = "Stop"

$PluginDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Resolve a python interpreter
$Python = $null
foreach ($c in @("python", "py -3")) {
    try {
        $null = & cmd /c "$c --version" 2>$null
        if ($LASTEXITCODE -eq 0) { $Python = $c; break }
    } catch { }
}
if (-not $Python) {
    Write-Host "no python found on PATH" -ForegroundColor Red
    exit 1
}

# Already alive?
& cmd /c "$Python `"$PluginDir\daemon.py`" ping" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "V5 Memory Daemon already running (port 9876)" -ForegroundColor Green
    exit 0
}

# ---- race protection (v1.1) ----
$CacheDir = Join-Path $PluginDir ".cache"
New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
$LockFile = Join-Path $CacheDir "daemon_start.lock"
$MarkerFile = Join-Path $CacheDir "daemon_started_at"
$GraceSeconds = 120

# 冷加载豁免: <120s 前刚 spawn 的 daemon 还在加载 BGE (ping 失败是预期行为)
if (Test-Path $MarkerFile) {
    $age = (Get-Date) - (Get-Item $MarkerFile).LastWriteTime
    if ($age.TotalSeconds -lt $GraceSeconds) {
        Write-Host ("daemon spawned {0:N0}s ago (BGE cold-load ~30s) · skip duplicate start" -f $age.TotalSeconds)
        exit 0
    }
}

# 独占句柄锁: FileShare.None 保证同一时刻只有一个调用者在检查+拉起
try {
    $lockStream = [System.IO.File]::Open($LockFile, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
} catch {
    Write-Host "another daemon_start is holding the lock · skip"
    exit 0
}

try {
    # 锁内复查: 排队期间前一个调用可能已拉起
    & cmd /c "$Python `"$PluginDir\daemon.py`" ping" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "V5 Memory Daemon already running (port 9876)" -ForegroundColor Green
        exit 0
    }

    Write-Host "Starting V5 Memory Daemon..."

    # Spawn detached. Output discarded; daemon writes its own log under .cache/
    # 2026-08-30: 移除 PYTHONPATH=C:\pylibs 注入。8/23 的 torch 短路径方案已过时——
    # Store Python site-packages 现有完整 torch 2.11.0+cpu + transformers 5.16.1 + st 6.0.0
    # (实测 BGE-m3 LOAD_OK)。C:\pylibs 是 2026-07 时代的旧库快照,注入后 daemon 反而加载
    # 旧库组合 → `Could not import module 'PreTrainedModel'`(lazy import 炸),
    # 1322 次 conn handler fail 即此根因。C:\pylibs 目录保留不删(可回滚)。
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = "cmd.exe"
    $startInfo.Arguments = "/c $Python `"$PluginDir\daemon.py`" > NUL 2>&1"
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $proc = [System.Diagnostics.Process]::Start($startInfo)
    Set-Content -Path $MarkerFile -Value (Get-Date).ToString("o")
    Write-Host "PID: $($proc.Id) · waiting for BGE load (~30s)..."

    # Poll ping up to 60 iterations (lock held; concurrent callers take the skip branch)
    for ($i = 1; $i -le 60; $i++) {
        Start-Sleep -Seconds 1
        & cmd /c "$Python `"$PluginDir\daemon.py`" ping" 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "V5 Memory Daemon ready (took ${i}s)" -ForegroundColor Green
            Write-Host "   port 9876 · PID file: $PluginDir\.cache\daemon.pid"
            Write-Host "   log: $PluginDir\.cache\daemon.log"
            exit 0
        }
    }

    Write-Host "daemon did not come up within 60s · see $PluginDir\.cache\daemon.log" -ForegroundColor Red
    exit 1
} finally {
    $lockStream.Close()
}
