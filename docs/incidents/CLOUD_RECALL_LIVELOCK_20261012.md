# 事故档 · 云端 MCP 语义 recall 全局停摆 13.2h(fill 霸锁 livelock)

> 2026-10-12 · compass · 窗口 10/11 23:05:53 → 10/12 12:19:17 CST · 1809 次过载拒绝
> 用户报障原话:「compass 云端 MCP 的语义 recall 一直失败」

## 一、链路与症状

```
Claude Code → https://compass.nautilus.social/mcp/ (Bearer)
  → nginx 8443 → mcp_server.py :9877 (TCP) → daemon_v33.py :9876 (systemd: compass-bge-daemon)
```

- initialize / tools/list 全正常(Bearer 有效,serverInfo 3.1.0)——门与 token 无辜
- `tools/call recall` → **瞬时**(0.0s)返回 `daemon overloaded - retry`,非超时
- ping / status 正常(v3.2 MSG_PEEK 快道,过载时仍可探——该设计生效)

## 二、时间线 [实测]

| 时刻 | 事件 |
|---|---|
| 10/11 23:05:53 | journald 首条 `overload · reject conn (inflight cap 32)` |
| 10/12 12:12 | status 口:5min 窗 **0 成功 recall / 27 拒绝**;线程仅 15(<32 槽) |
| 10/12 12:15 | py-spy 抓旧进程(pid 941):8 个池 worker **全部**卡 `get_memory_entries:873` 等 `_mem_lock`,其中 1 线程在 http.client `getresponse`(正常嵌入读取) |
| 10/12 12:19:17 | systemctl restart → 立即恢复 |
| 10/12 12:18:31 | journald 末条 overload(共 **1809 条**) |

## 三、根因(证据链)

1. **同项目 fill 串行锁**:`get_memory_entries` 的 cache fill(逐条嵌入+pkl flush)持 `_mem_lock(proj_key)`,v3.0.3 设计。
2. **fill 无时间预算**:大项目冷 fill(千级条目 × 每条嵌入 + 每 50 条 flush 全量 pkl,池 pkl 总量 1040MB)单次可霸锁分钟级。
3. **重试风暴填队列**:信号量 = 线程池×4 = 32(故意放深队列吸收突发),24 个排队位被重试请求填满。
4. **槽全局耗尽→全局死锁**:槽是全局资源,A 项目的慢 fill 拖死所有项目的 recall——**别人的慢,杀死了所有人**。
5. **排除项** [实测]:embed 代理(A100 隧道 19987→8400)全程健康(/health 200/0.34s,实测嵌入 200/0.27s);journald 零条 `embed proxy fail`——代理/隧道无辜。timeout=8 在运行代码内(文件 mtime 10/08 早于进程启动 10/09),单次调用无法挂 13h。

## 四、修复

- **恢复**:`systemctl restart compass-bge-daemon`(pkl 热缓存,重启秒级恢复)。
- **根修 v3.3.6**:`daemon_v33.py` fill 循环加**时间预算** `COMPASS_FILL_BUDGET_S`(默认 30s)——超时记日志(`fill budget exceed … partial n/m`)并 break,缺 embedding 的条目在下游两处打分点 `e.get("embedding")→None` 自动跳过(部分结果语义安全,与既有 except 路径同构)。单项目 fill 最长霸锁从分钟级收束到 ~30s。
- 备份:`daemon_v33.py.bak-fillbudget-20261012`(云端原地;该文件不在 git 仓,生产 ops 件)。
- **验证**:重启后云端 MCP 全链路双查询 recall 3.1s / 4.3s 各 2 hits,isError=False [实测 2026-10-12 12:33]。

## 五、遗留(如实)

1. **触发源未定谳**:journald 把 10/11 白天日志轮转掉了(unit 全天仅存 196 行),23:05 fill 洪峰的引信(哪次 ingest/哪个项目)无证据。候复发时第一时间 py-spy 抓现场。
2. `LOG_FILE`(CACHE_DIR/daemon.log)未落盘,log() 写文件静默失败——文件级日志缺失,journald 成为唯一日志面(已被轮转证明不可靠)。待查。
3. 本地 hook 报「daemon 未就绪」的判定口径与 ping 探活不一致(本地 9876 ping 全绿),非本次故障主因,待对齐。

—— compass · 云端 recall livelock 事故档 · 2026-10-12 · 证据全部 [实测]
