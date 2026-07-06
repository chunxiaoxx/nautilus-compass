---
name: session_20260706_compass_ssot_drift_qixuw_cstart_orphan_mcp_restore
description: compass 7/6 · 一次两周回顾牵出的 4 条根因治理 · 三框 SSOT drift 是精神分裂病根 + qixuw 3 天重复劳动 + cstart compass 错映射目录 + cloud v1 orphan daemon 拖垮 + ~/.claude.json 清理后 MCP 全丢的恢复路径。全部 grounded 实测,附 commit/PID/文件路径。下 session 起手自检清单在末尾。
metadata:
  node_type: session
  type: session
  originSessionId: claude-opus-4-8[1m] (2026-07-06)
---

# Session 2026-07-06 · 两周回顾 + 4 条根因治理(全 grounded)

## TL;DR

用户要"全面回顾过去两周",拉三框(compass/nautilus-core/nautilus-v5)第一手 git+SSOT 后,牵出 4 条一直咬人的根因并逐个 grounded 处理。核心发现:**三份"单一真相源"自己就不同步 = 精神分裂病根在 SSOT 自身发作**。

## 1 · 三框 SSOT drift = 精神分裂病根(治 anchor #4)

三份 `LOOP_STATE_SSOT.md` 副本互相对不上:
- core(canonical)= 7/2 · compass = 7/3 · v5 = 7/3
- Kairos 状态:core 已 grounded 纠正"balance=8 被冻是过时推断 · income=0",但 compass/v5 副本仍写"balance 8 被冻"
- PoI 账本:compass 副本写"DORMANT→GREEN 待定",core 实测 `platform_nau_ledger +1250/24h 已 GREEN`
- **compass 副本的 7/3 双主线更新一直没 commit** · git HEAD 停在 6/29 版本(working tree 有改动没落库)= drift 的物理根

**已做**:commit `4747152` 把 compass 副本落库(7/3 双主线 + core grounded 实测块同步)。**未做**:core canonical(7/2 · binding-DONE 正文仍写 balance=8)+ v5 副本仍旧 = platform/v5 turf,compass 不越界代改。
**如何避免**:变更协议"先改 canonical 再同步"要真执行;改完 SSOT 立即 commit,别留 working tree。

## 2 · qixuw 3 天重复劳动 = 没读另两框 SSOT(治 anchor #6)

compass 7/4-5 从零重诊 qixuw 连不通(CC Switch 代理 `1780e4d` → 推翻 `afdb699` → "provider 死" → 7/5 才得 endpoint 错 `4abce49`),烧 10+ commit / 3 天。但:
- core SSOT(7/2)已写 `H800 端 qixuw OPENAI_BASE_URL 直连稳定`,JobShop/TSP GPT-5.5 N=3 数据早跑通
- v5 commit `1eb2608`(7/4)= "3 completer 加 reasoning_effort(治 qixuw 7/2 502 真根因)"

根因 = 没读另两框 SSOT/git,把已解决的问题当新问题重查。
**如何避免**:接到"X 坏了/连不通",起手先 grep 三框 SSOT + `git log` 看是否已解,再动手。

## 3 · cstart compass 错映射目录(session 反复不在对目录的根因)

`~/.claude/plugins/nautilus-compass/ops/compass_start.ps1` 第 34 行 `"compass" = "C:\Users\chunx"` → 每个 `cstart compass` 启动的 session 都落到 `C:\Users\chunx` 而非项目目录。这就是环境 "Primary working directory: C:\Users\chunx" + 多次"你应该在 nautilus-compass 目录"的根因。
**已做**:改为 `C:\Users\chunx\Projects\nautilus-compass` · commit `7c7572e`(plugin repo main)· `cstart paths` 验证 [OK]。

## 4 · cloud v1 orphan daemon 拖垮 = 手动 nohup 不清(治 anchor #6)

🚨 alert "ssh poll timeout 78x + COMPASS mcp fail" 的根因 = **compass 自己的老进程**,不是 MCP 死:
- `/opt/nautilus-compass-v1/daemon.py`(文件日期 5/25 = v1 老版本 · canonical 路径不带 `-v1`)
- 某过去 session `nohup python3 daemon.py &` 手动起 · orphan 2 天 · 卡在 `overload · reject conn` 空转死循环
- 194% CPU + 6.9GB → swap 撑到 99.96% → 2 核 cloud thrash → 任何新 ssh 握手 >20s 超时 → poller fail
- canonical 是 systemd:`compass-mcp-tcp.service`(9877 · PID≠orphan)/`compass.service`(8770)/`compass-t4-tunnel.service`

**已做**(用户授权)：kill orphan PID 3437200 + V5 spinner PID 3968809(V5 main_singleton 的 `/tmp/tmpjl56clcy.py` 空转子进程)。验证:CPU idle 0%→69.6% · free 0.3GB→6.1GB · ssh 往返 6.7s · poller dry-run 成功 `b2_agents=4` · MCP 9877 未动。
**如何避免**:daemon 走 systemd,不手动 nohup;起了必清。下 session 起手 `ssh cloud "ps aux|grep daemon.py"` 查孤儿。

## 5 · ~/.claude.json 手动清理后 MCP 全丢 + 恢复路径

用户手动清 `~/.claude.json` 时把 `mcpServers` 清空({}),3 个 server 全丢 → `/mcp` "No MCP servers configured"。**与 cstart 目录 bug 无关**(mcpServers 是 top-level 全局,与 cwd 无关)。
- compass MCP = stdio bridge `ops/mcp_stdio_to_cloud.py`(env: COMPASS_CLOUD_HOST/PORT=9877/TOKEN/AGENT_TYPE)→ 9877 tunnel → cloud `compass-mcp-tcp.service`
- 恢复源 = `~/.claude.json.bak-pre-cleanup-20260705-210524`(63KB 完整)· 提取到 `~/.claude/mcp_servers_extracted_20260705.json`
- **已做**:3 server(MCP_DOCKER/MiniMax/nautilus-compass-cloud)merge 回当前 `~/.claude.json`(47 key 原样保留)· 备份 `.bak-pre-mcp-restore-20260706-084156`
- ⚠️ **必须重启 Claude Code 才加载 MCP**(启动时才读)· 且 clobber 风险:正在跑的 session 退出时可能把内存里的空 mcpServers 刷回覆盖 → 重启后 `/mcp` 若仍空,重跑 merge(幂等,提取文件在)

## 下 session 起手自检清单(治复发)

1. **在对目录吗**:pwd = nautilus-compass?(cstart 已修但确认)
2. **SSOT 一致吗**:三框 `LOOP_STATE_SSOT.md` last-updated 对齐吗?本框改动 commit 了吗?
3. **"X 坏了"先查再动**:grep 三框 SSOT + git log,别重查已解问题
4. **cloud 有孤儿吗**:`ssh cloud "ps aux|grep -E 'daemon.py|tmp.*\.py'|grep -v grep"` 查手动 nohup orphan
5. **MCP 在吗**:`/mcp` 空 → 从备份恢复 `mcpServers`,重启加载

## 🔄 重启序列(本 session 7/6 交接 · 防 MCP clobber)

新 session 由 `cstart compass`(已修 `7c7572e` → 进 nautilus-compass)启动。MCP 只在启动时加载,且**旧 session 退出可能把内存里的空 mcpServers 刷回 `~/.claude.json` 覆盖恢复**。稳序:
1. 退出旧 session
2. 普通 PowerShell(非 Claude Code)跑 re-apply,保证磁盘有 3 server:
   `python -c "import json;p=r'C:\Users\chunx\.claude.json';e=r'C:\Users\chunx\.claude\mcp_servers_extracted_20260705.json';d=json.load(open(p,encoding='utf-8'));d['mcpServers']=json.load(open(e,encoding='utf-8'));json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2);print('MCP restored',list(d['mcpServers']))"`
3. `cstart compass` → 新 session 读到好配置加载 MCP
4. 新 session `/mcp` 确认 3 个(尤其 `nautilus-compass-cloud`);若空=被 clobber,重跑步骤 2 再重启
- 备份:`~/.claude.json.bak-pre-mcp-restore-20260706-084156` + 提取 `~/.claude/mcp_servers_extracted_20260705.json`

## 🎯 主线唯一未闭:B = total_income=0

三条 binding-DONE(见 SSOT)里 #3 PoI 账本已 GREEN(+1250)、#2 Kairos 口径修正,**#1 `agent_survival.total_income` 因外部验证增长 = 唯一未闭缺口**。现状:GenOpt ~15 题入飞书(core 5 + v5 ~14),但没一条走完 soul canonical verify → 外部 reward 入账。新 session 起手 = grounded 查"已产题为何没转成外部验证收入"(compass turf 只读:fde_verdicts / ledger)· 不扩题(反 D)。

## 关联
[[session_20260705_compass_stop_hook_strategic_decision_pending]] · [[session_20260704_compass_qixuw_real_config_disclosed]] · [[session_20260704_compass_cc_switch_proxy_path_fix]] · [[session_20260704_compass_mcp_local_repaired]] · [[reference_compass_plugin_inventory]]
