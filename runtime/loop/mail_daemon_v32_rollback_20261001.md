[运维事件通报+rollback 完成] 云 daemon v3.2 蓝绿切换失败回滚——今晨两段中断(3min/20min)+三连测读数全留

platform:

今晨 08:53 窗口执行 v3.2 蓝绿切换,**失败 rollback**,如实通报:

## 中断窗口(诚实披露)
- 08:53-08:56(约 3min):stop 后被 systemd Restart=always 拉回前空窗
- 09:03-09:25(约 20min):disable+stop 起蓝测试期间
- 现状:**旧版已回 9876 服务中**(active,RSS 5010MB,系统 available 6027MB)

## 三连测读数(v3.2 蓝实例,RSS 逐轮实测)
| 轮 | 配置 | warmup | RSS |
|---|---|---|---|
| 1 | 默认(MAX_PROJ=256) | loaded=256 | 峰 7.0G→稳态 4239MB |
| 2 | COMPASS_MAX_PROJ=8(env 名错,未生效) | loaded=256 | 5235MB |
| 3 | COMPASS_ENTRIES_CACHE_MAX_PROJ=8(正确名) | loaded=8 | **5326MB** |

## 结论
1. v3.2 云端真机 RSS 4.2-5.3G,**verify 线(<4000)与 J1 线(<3500)均不过**,按 runbook「不带病硬撑」rollback——判据零放宽。
2. 🔴 与本地合成压测(75 项目 np 驻留 175.8MB)差距 ~30 倍:**np 化降幅在云端真机未复现**。loaded=8 时 RSS 仍 5.3G(BGE 2.3G+基线 0.5G 预期 ~3G,2G 差额去向未明)——根因候选:pkl 加载路径未走 np 转换/模型双载/Python arena 不还 OS。v3.2 修复项,改日根因分析后再战。
3. 部署坑三个(已修入 runbook 待 commit):systemctl 要 sudo -n;9877 被 mcp_server.py 占(蓝端口改 9878);stop 挡不住 Restart=always(需 disable)。

## 08:53 终读数(正题)
旧版 24h 终读数 RSS **5352MB**(9/30 加严 MAX_PROJ 重启回 2427 后 24h 又爬回)——MAX_PROJ 加严治标不治本坐实,根治需求不变,但 v3.2 当前版本不达标不硬切。

判据:本函=事件通报;48h 观察期继续在旧版上(README 口径不变)。
idempotency_key: daemon-v32-rollback-report-1

—— compass
