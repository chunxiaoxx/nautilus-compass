# 事故档 · Compass recall 入口全停(本地 daemon 过载 livelock·10-12 云端同型复发)

> 2026-11-17 · compass · 本地 Mac daemon(:9876)· 窗口 19:2x → 19:4x EST
> 症状:会话启动 hook 报「daemon 未就绪·本轮跳过注入」+ MCP recall 返 `daemon overloaded - retry`
> 关联:本目录 `CLOUD_RECALL_LIVELOCK_20261012.md`(云端同型事故·13.2h·1809 次拒绝)

## 一、症状与链路 [实测]

```
Claude Code 会话 hook(注入)  →  本地 daemon 127.0.0.1:9876  →  记忆库(memory/*.md)
MCP tools/call recall        →  同一 daemon
```

- 本轮会话启动:hook 自报「daemon 未就绪,本轮跳过注入(不阻塞)」→ **注入链死**
- MCP recall:返 `Error: daemon overloaded - retry`
- 直连 9876 发 recall:同样 `{"ok":false,"error":"daemon overloaded - retry"}`
- 本地 8097 MCP HTTP:探活 200(门与 token 无辜)· 8400 embed 代理 200 · 8401 rerank health ok

## 二、时间线 [实测]

| 时刻 | 事件 |
|---|---|
| 19:29 前后 | 会话 hook 报「daemon 未就绪」·MCP recall 报 overloaded |
| 19:37 | 定位旧 daemon PID 69627(Sun01AM 起·0.0% CPU·累计 CPU 40:59)·in-flight 槽 32 全占满 → 每连接 reject-fast;进程上仍挂着 **30+ CLOSED 客户端套接字**;daemon.log 本轮拒绝约 244 行 |
| 19:36–19:38 | `daemon_start.sh` 连续 4 次「bind fail · Address already in use」·「❌ daemon 60s 内没起来」·`.cache/daemon.pid` 记 77653(**已死**)而实况是 69627(PID 失真) |
| 19:39:37 | **恢复动作**:`launchctl kickstart -k gui/$(id -u)/com.nautilus.compass-daemon`(watchdog 自带同款命令)→ 新 PID 80947·pkl warmup 0.7s·listening·`action=ping` 0.00s ok·重启后 overload 拒绝 **0 行**(log 161867→161881) |
| 19:40 起 | **但查询路径仍挂**:MCP recall 连续 2 次超时;带 token 直连 recall **150s socket 超时无响应**;`action=status` 0.0s 返 `sliding_5min.count_5min=0 / avg_ms=0 / p9 hit=0 miss=5` → **5 次请求无一完成**;CPU 0.0%;daemon **无任何出向 TCP**(不连 8400/8401) |

## 三、根因判定 [实测证据链 + 复发对照]

**10-12 云端事故档已定谳的根因**:同项目 fill 串行锁 `get_memory_entries` 持 `_mem_lock(proj_key)` **无时间预算** → 大项目冷 fill 霸锁分钟级 → 32 个 in-flight 槽被重试队列填满 → **全局死锁**(A 项目的慢 fill 杀死所有项目的 recall)。根修 v3.3.6 = `COMPASS_FILL_BUDGET_S`(默认 30s)+「缺 embedding 条目下游自动跳过」,**只落在云端 `daemon_v33.py`**(该件不在 git 仓)。

**本地核对 [实测]**:

| 位置 | 字节 | 含 `COMPASS_FILL_BUDGET_S` |
|---|---|---|
| `~/.claude/plugins/nautilus-compass/daemon.py`(在跑的那份) | md5 与仓内一致 | **无** |
| 仓内 `daemon.py`(git 跟踪·2186 行·mtime 11-02) | 同上 | **无** |

⇒ **本地从未拿到 10-12 的根修**,同型事故具备复发条件。今日复发与 10-12 定谳**同型**(槽耗尽 + 全局拒绝 + 自愈失灵)。

**自愈链三处盲点(全部 [实测])**:
1. `daemon_start.sh`:端口被占 → 「Address already in use」×4 → 起不来新实例(进程还活着但已废)
2. `.cache/daemon.pid` 记 77653(死)而实况 69627(活)→ PID 失真
3. **`scripts/mcp_watchdog.sh` 探活 = 裸 TCP connect**:端口仍 LISTEN → 判 `ok` → **不 kickstart** → 自愈链对「端口在听但全拒」完全盲(本轮 watchdog exit 0 而 recall 全挂)

**当前残留的查询路径挂起 [推断·阻塞原语级]**:
重启后 ping/status 秒回(说明 accept 循环与 handler 池活着),但 recall 一条不出、CPU 0.0%、**无出向连接**(不连 8400 embed 代理、不连 8401 rerank)⇒ 阻塞点在 daemon 进程内(锁等待),不在代理/隧道/网络。
`action=status` 报 `memory.pkl_count=3597 / pkl_total_mb=363` ⇒ 单项目缓存 3597 条(chunk 级),与 10-12 的「千级条目冷 fill 霸锁」量级吻合。
**精确阻塞点 [不可验]**:10-12 事故档留过一条行动项「候复发第一时间 py-spy 抓现场」,而本机 **py-spy 未安装、venv 无 pip、PATH 无 uv** → 只能用 macOS `sample`(无 Python 帧)→ 只能判到「锁等待」这一层。

## 四、本轮动作

| # | 动作 | 状态 |
|---|---|---|
| 1 | `launchctl kickstart -k gui/$(id -u)/com.nautilus.compass-daemon` 恢复传输层 | ✅ 已执行·PID 80947·ping/status 秒回·overload 归零 |
| 2 | **watchdog 探活口径升级**(仓内 `scripts/mcp_watchdog.sh`):裸 TCP connect → daemon 自带免鉴权 `{"action":"ping"}`,并把「过载/忙/死」三态分开 | ✅ 已改并单测(overloaded/ok/busy 三态判定 mock 实测全过)·busy 态**不重启**(避免打断正在做的 fill) |
| 3 | 精确阻塞点定位 | ❌ 卡在 py-spy 不可用 → 下一轮装诊断件后重做 |
| 4 | 移植 `COMPASS_FILL_BUDGET_S` 到本地 daemon.py | ⏸ 候用户拍板(见第五节) |

## 五、候拍板(带后果)

- **P1 装诊断件**:py-spy 不可用是本轮最大盲点。装法二选一:`brew install py-spy` / `python3 -m ensurepip --user` 后 `pip install --user py-spy`。属新增第三方件 → 需拍板。
- **P2 移植 10-12 根修**:给仓内 `daemon.py` 的 fill 循环加 `COMPASS_FILL_BUDGET_S`(默认 30s·超时记 `fill budget exceed … partial n/m` 并 break·缺 embedding 条目下游自动跳过)。**注意**:仓内 `daemon.py` 与插件副本 `~/.claude/plugins/nautilus-compass/daemon.py` 字节相同且需**同步**(插件副本 = 共享面·影响所有框)→ 需授权后一并改并复测。
- **P3 daemon.pid 失真**:启动脚本应写实际 PID 并校验存活(今天 pid 文件写的是死 PID 77653)。
- **P4 库体量**:pkl 3597 条 / 363MB、库 1419 张卡(噪声 1229 张=86.7%·R561 口径)——**fill 冷启动成本随噪声卡线性增长**,与「堵召回/清存量」是同一根因的两面,不能只做其一。

## 六、值守面(本轮其余,均 [实测])

RED to=platform 217→218(唯一新增 **id99489 soul-distress ×84**·人监门候用户不代删)·信箱 compass 0 未读 ·Gmail 401→直刷 REFRESH_OK 3599s→全量 7d **58 封**/未读 **33 封**与 R561 持平·逐封 sender 全甄零新面孔零新商务函·草稿 35 封零新 ·mentions 5 全旧 ·notifications 45 全旧 ·genesis 5 家零 REPLY ·dev.to 30 文 6+2=8 持平 ·CI 44189839879 success ·哨兵 exit0 recall_hit=102 ·快筛历轮全同(CS-513 过·CS-514~518 不过)·矩阵仍停 10-30 09:42 ·磁盘 97% avail **14Gi**(R561 17Gi −3Gi·仍 ≥10Gi 线)·**distill 又发布 1 张**(stats 353→354·库 1418→1419)→ R559「冻结被证伪」继续成立。

—— compass · 2026-11-17 · 证据标注 [实测]/[推断]/[不可验] · 阻塞点与代理无关已由「无出向连接 + 代理健康」双向排除
