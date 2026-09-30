# v3.2 蓝绿部署 Runbook(2026-09-30 备好 · 窗口执行)

> 执行窗口:**10/1 08:53 记忆判据终读数之后**(勿在读数前动生产)。
> 脚本:`ops/v32_bluegreen_deploy.sh`(upload/blue/verify/switch/rollback 五步独立幂等)。
> 判据正本:CLOUD_DAEMON_ROOTCURE_PLAN_20260930.md §四(J1-J7)。
> 本地验证已齐(9/30):单测 5/5 + 合成压测 3 PASS(np 驻留 175.8MB/8.0x 降幅/零逐出)。

## 前置事实(9/30 定格)

- 生产现状:v3.1.1+MAX_PROJ=8(systemd compass-bge-daemon),RSS 5.1G,churn 持续(55min 371 evict),overload 拒连
- 系统可用内存 4.3G——**蓝实例需 ≥4G**(模型 2.3G+np 缓存 ~0.2G+余量),脚本 blue 步内置 <4000MB 熔断
- SSH:`~/.ssh/config Host cloud`(43.160.239.61:24860)
- cache 目录孤儿 pkl(10261 个/1469MB):**本轮不动**,切换稳定后另行盘点移档(刀 D 单独走,需列清单确认)

## 执行序

| 步 | 命令 | 时机 | 判绿标准 |
|---|---|---|---|
| ① upload | `bash ops/v32_bluegreen_deploy.sh upload` | 任何时候 | compile OK + md5 一致 |
| ② blue | `... blue` | 窗口内,可用内存 ≥4G | PID 起,无 ABORT |
| ③ verify | `... verify` | blue 后 5s~15min | J5-listen PASS(秒级 ping);status rss_mb<4000 |
| ④ switch | `... switch` | verify 绿 | v32 上 9876,蓝退役 |
| ⑤ 观察 20min | 手动 | switch 后 | J1 RSS<3.5G · J2 evict≤5/h · J3 overload=0(daemon.log) |
| 回退 | `... rollback` | 任何时候不绿 | 原版 systemd 拉起,零确认 |

## 48h 观察期(J1-J3 连续绿后才算关单)

- 10/1 切换+20min 观察;10/2 复查 RSS/evict/overload 三读数
- 全绿 → 刀 D 孤儿 pkl 盘点(列清单→用户确认→移档 /tmp 留 7 天)→ ROOTCURE_PLAN 关单
- 不绿 → rollback + 读数留档 + 根因分析(不带病硬撑)

## 风险与回退

- 切换后 systemd unit 仍指旧 daemon.py(不冲突:unit 已 stop;后续把 unit ExecStart 改指 daemon_v32.py 作为永久化,观察期后做)
- 回退永远一步:rollback 杀 v32 → systemctl start 原版
- 10/1 08:53 读数走 ssh cloud,与蓝绿脚本同一通道,读数完再动手
