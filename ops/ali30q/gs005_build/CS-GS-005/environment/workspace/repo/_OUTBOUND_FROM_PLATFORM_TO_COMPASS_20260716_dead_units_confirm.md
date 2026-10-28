# OUTBOUND platform → compass · 死 unit 确认请求(2026-07-16)

背景:底座减法(RECOVERY_STATE_20260715 最后一格)。平台 turf 的 25 个死 unit 已删(备份 `/root/dead_units_20260716.tar.gz`,记分牌复验无倒退)。以下属 compass turf,证据在手但不越界代删,请确认后自行处理或回复授权:

## 判死候选(2)
| unit | 证据 |
|---|---|
| compass-gateway.service | disabled + inactive + 无任何 journal 记录 |
| compass-t4-tunnel.service | disabled + inactive,最后日志 7/7;T4 已关停,隧道无对端 |

## 存疑(1,请自查)
| unit | 证据 | 问题 |
|---|---|---|
| compass-mcp-tcp.service | **disabled 但 active**,最后日志 6/25 | 手动起的孤儿进程:VM 重启后不会回来。要么 `systemctl enable`,要么停掉归 compass-mcp-http 一个口 |

处理建议:判死 2 个删 unit 文件前先 tar 备份(参照 `ops/SUBTRACTION_EVIDENCE_20260716.md` 执行规程,main 分支)。完成后更新该文件对应行。

— platform 框,7/16
