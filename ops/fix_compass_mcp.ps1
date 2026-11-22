# fix_compass_mcp.ps1 — 把 ~/.claude.json 的 nautilus-compass 指到公网 compass MCP
# 用法:所有 Claude Code 对话框【全部关闭后】跑一次,再开新对话框。
# 原理:Claude Code 进程退出时会用内存快照回写 .claude.json,踩掉外部编辑——
#       所以必须在"无任何对话框存活"的窗口期执行才不会被回滚。
# 校验:改完自动打印结果;退出码 0=成功。
$ErrorActionPreference = 'Stop'
$p = "$env:USERPROFILE\.claude.json"
Copy-Item $p "$p.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"   # 自动备份
$j = Get-Content $p -Raw | ConvertFrom-Json
$j.mcpServers.'nautilus-compass' = [pscustomobject]@{
    type    = 'http'
    url     = 'https://compass.nautilus.social/mcp/'
    headers = [pscustomobject]@{ Authorization = 'Bearer cmp_laptop_55921184bf9b81a957d6af6827faca43' }
}
$j | ConvertTo-Json -Depth 100 | Set-Content $p -Encoding UTF8
$chk = (Get-Content $p -Raw | ConvertFrom-Json).mcpServers.'nautilus-compass'
if ($chk.url -eq 'https://compass.nautilus.social/mcp/') {
    Write-Host "[OK] nautilus-compass -> $($chk.url)" -ForegroundColor Green
    # 实弹一发
    try {
        $code = curl.exe -s -o NUL -w "%{http_code}" -X POST $chk.url `
            -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" `
            -H "Authorization: Bearer cmp_laptop_55921184bf9b81a957d6af6827faca43" `
            -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"0.1"}}}' `
            --max-time 30 2>$null
        Write-Host "[probe] HTTP $code (200=通)" -ForegroundColor $(if($code -eq '200'){'Green'}else{'Yellow'})
    } catch { Write-Host "[probe] 跳过:$_" -ForegroundColor Yellow }
} else { Write-Host "[FAIL] 写入未生效" -ForegroundColor Red; exit 1 }
