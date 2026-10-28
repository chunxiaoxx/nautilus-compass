# nginx systemd 正式交接 runbook(2026-10-09 深夜窗 · 用户已批,豁免 22:00 纪律)

> 背景:compass #10841 警告 + 台账 10/10 nginx 70 分钟事故根因收尾。
> 用户批语:按原计划深夜执行,瞬断 2 秒影响最小。

## 侦察实测(20:28Z,与 compass 函描述的差异以本节为准)

| 项 | 实测 |
|---|---|
| 手工 master | PID 18826,今晨 10:14:36 起,PPID=1,4 worker(10:32:50 reload 换代),**无 -c 参数=用 /etc/nginx/nginx.conf 同一份 conf** |
| systemd unit | **enabled 非 masked**;Drop-In override.conf=`Restart=on-failure/RestartSec=10/StartLimitIntervalSec=0` |
| systemd 现态 | **auto-restart 死循环进行中**:每 10s bind 443/80/8443 失败(被 18826 占),journal 刷屏 |
| /run/nginx.pid | 不存在(手工启动未写)——ExecStop 的 pidfile 方式不杀伤手工 master |
| 拉起源 | cron/rc.local/cron.d **均无**——一次性人工拉起,交接后不复发 |
| certbot | snap.certbot.renew.timer 22:25 有一次,10:20 已跑过,无端口冲突 |

**风险本质**:双引擎并存(unit enabled+手工实例),端口先到先得,重启时序不可控。

## 执行序

```bash
# 步0 基线(已完成 20:22 本地):五站 200×5(主站/app/bench/data/compass)
# 步1 停 systemd restart 循环(清 pending restart)
systemctl stop nginx
# 步2 优雅停手工 master(QUIT=排空当前请求;空闲时段 <2s;无 pidfile 故直接对 PID)
kill -QUIT 18826
# 轮询确认退出(最多 5s);未退则中止观察,禁 -9(排空中强杀=瞬断拉长)
for i in 1..5: ps -p 18826 || break; sleep 1
# 步3 systemd 接管
systemctl start nginx; sleep 2; systemctl is-active nginx   # 期望 active
# 步4 验证
ss: 新 master PID(≠18826) 持有 443/8443/80
本地 curl: 五站 200×5 + app 危险面 403(门禁) + 主域 /api/bootstrap/run 405(已知活洞,白窗 10/11 修,不在本窗范围)
```

## 回滚预案(步 3 is-active≠active 时执行)

```bash
nohup /usr/sbin/nginx >/dev/null 2>&1 &   # 恢复手工态(与 10:14 同方式)
sleep 2; ss -tlnp | grep ':443 '           # 确认监听恢复
systemctl stop nginx                        # 再停 restart 循环防竞态,天亮排查
```

- 注:即使一次 start 撞 bind 失败,override 的 10s 无限 retry 会自愈接管(循环反而兜底);回滚预案仅在 20s 后仍 inactive 时启动。
- 失败后禁盲目重复 start——看 journalctl -u nginx -n 20 定位再动。

## 验收判据

1. systemctl is-active nginx = active,主 PID 唯一,无 18826 残留
2. 五站 200×5(基线持平)
3. app 域危险面 403 门禁不破
4. 重启安全:enable 已在(enabled),下次服务器重启 systemd 自动拉起,无双实例

—— platform · NGINX-SYSTEMD-HANDOFF · 2026-10-09 深夜窗
