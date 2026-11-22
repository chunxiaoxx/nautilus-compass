# 审计席例行体检包装(计划任务 compass-audit-seat 每日 09:30 调用)
Set-Location "C:\Users\chunx\Projects\nautilus-compass"
New-Item -ItemType Directory -Force "runtime\audit" | Out-Null
& "C:\Python312\python.exe" "ops\audit_seat_round.py" *>> "runtime\audit\seat_task.log"
# 日志只留尾部 400 行,防无限增长
$log = Get-Content "runtime\audit\seat_task.log" -ErrorAction SilentlyContinue
if ($log -and $log.Count -gt 400) { $log[-400..-1] | Set-Content "runtime\audit\seat_task.log" -Encoding UTF8 }
