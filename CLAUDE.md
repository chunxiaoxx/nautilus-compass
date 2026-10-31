# nautilus-compass · 项目指令

> 🗄️ **阿里出题一期已收官停工(10/30 用户拍)**:判断前三查/判据正本/出题纪律的会话默认注入已肃清(10/31)。正本/台账/复盘存 nautilus-core/docs/(CODESENSE_PHASE1_FINAL_RETRO_20261030 · ALI_LIVE_OR_SYNC_V1 · ALI_FEEDBACK_LEDGER_V1 · ALI_REQ_STANDARD_MAP_V1 · feishu/ 两原文)·判据锁/gate5/预筛器存本仓 `ops/ali30q/`+`runtime/pipeline_state/`,按需直读不再随会话加载。重启一期按复盘「下期启动前置5条」恢复注入。

> 🔴 开工第一动作(frame-upgrade-20260904-compass #2 · MetaGPT _observe 原则;10/19 F1 bootstrap一口):先取组织态再开始其他任何事(10/19 F1 升级 bootstrap 一口)——`curl -s "https://nautilus.social/api/platform/org/bootstrap?agent=compass"`(registry/未读函/goals/health 一口)→ 逐封 ack(需正文回函的按 trace 回函),然后才开工。本框状态自报见 `FRAME.yaml`(状态变化时顺手改)。

> 🔴 方向锚(2026-10-30 更新·24116 收敛令生效,与仓内任何文档冲突时以此为准):
> **当前业务 = 记忆 IO(M5 记忆门)+ 后训练(蒸馏)+ unipat/验证机构(CASSAY/JEV/VerifyPack)+ 判分值守与复判位**。
> **阿里 CodeSense 线(出题/判分/调档/交付)整体移交 nautilus-agent**(24116 用户拍板·回执函 24126·交割台账 `runtime/production_queue.md`);bait-loop/ali30q-loop/production-loop 已卸载;**CS-007 复判位保留**(v5 返工卷面来即判)。
> 10/29 锚(阿里出题生产+判据工程化)及更早的具身智能/垂域出题锚均为历史层——仓内 FDE/CHARTER/SSOT 为历史层,考古时手动读,读时牢记历史层 ≠ 现状。
> 判分值守红线不变:判据零放宽/证据分层不冒充/非实现者复算;**复判轮开工前照跑 gate0**(`python3 ops/ali30q/verify_criteria_lock.py`)。

> 🗄️ 判据正本/五条件/判据锁/gate5/预筛器等阿里一期内容已肃清不随会话加载(2026-10-31),坐标见上方停工锚(本仓 `ops/ali30q/`+`runtime/pipeline_state/`)。

> 🔴 报数纪律(2026-09-15 用户拍板,流程正本 `docs/soul/proposal_preregistered_recompute_20260914.md`,soul 提案 approved):
> 对外要报数字的任务(评测/跑分/数据产出/修复验收)——**开工先落预注册判据档**(判据只许更严),**收工走非实现者复算**(新鲜会话,只信判据与自测);交接档只给坐标与命令,**不给任何预期读数**(占位句也不写,留空白)。复算红灯先证伪自己探针。
> **判分证据分层(2026-10-03 用户拍板,正本 `docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md`)**:判分/复算/验收报告的每条结论性陈述必须标注 `[实测]/[推断]/[不可验]` 三层之一,推断不得冒充实测,推断发布即带 upgrade_path,U 态与证据层独立标注。

> 🔴 生产纪律(普适两条保留·阿里出题专项纪律已随一期停工肃清 2026-10-31,坐标见上方停工锚):
> - **/tmp 会周期性全灭**: 生产件一律放持久路径(`runtime/scratch_*`),不放 /tmp
> - **身份字符串 ≠ 机器位置**: 判断来源只看文件系统坐标,不看 agent 名

> 🔴 MCP 配置(2026-10-27 定型):
> - 项目级 `.mcp.json` = 本地 stdio(venv python + PYTHONPATH 仓根)·服务 8097 launchd 常驻+watchdog 5min 自愈
> - user 级 `~/.claude.json` = http://127.0.0.1:8097/mcp/(笔记本/cloud 侧 agent 经 Tailscale 100.84.23.45:8097/mcp/)
> - token 文件 `~/.claude/.cache/compass_mcp_tokens.json`(0600·20 token 合并)·**改 token 必须 kickstart 重启服务**

> 🔴 循环(10/30 收敛令后收紧·launchd):
> compass-loop(30min·含管道刷新)·pipeline-sync(30min)·mcp-watchdog(5min)·s5_receiver(watch)·判分矩阵(每时轮)·compass-daemon(9876)。~~bait-loop/ali30q-loop/production-loop~~ 已卸载(阿里线移交,plists 留 `~/Library/LaunchAgents/` 可复启)

> 🔴 值守报表锚行(10/30 收敛令修订): 每轮报一行"主线: M5·后训练·判分各一词状态";素材主线恒报"素材线: 已交割(24116)卡0题0门0"——23249 零进度亮牌规则不再适用(线已移交,亮牌只对现役主线)

<!-- COMPASS-KG-NODE · 2026-07-14 从 4 个历史会话提炼 · 完整见 ~/.claude/projects/<proj>/memory/session_NODE_nautilus-compass.md -->
## 📍 项目现状与复发陷阱(compass 记忆提炼)
本项目 4 段历史已提炼进 compass memory,开工用 `recall` 召回相关条目。复发陷阱速览:

- 自报不算,能独立复现才算(项目立身之本,连自家README也是'自报')。
- 探针/结论红灯先证伪自己,别默认被测物有病(去伪比抓病更高频有效)。
- 件数≠价值 / 活着≠可观测≠有产出(剧场识别核心尺子)。
- 改动前先 grep 仓库找旧实物(标准MCP/DB连接配方/探针都曾被重造);SSOT drift=精神分裂病根。
- **立项先问材料本体**(10/19 自举线定谳,勘误档 §四-3):攒语料/造数据集前先回答"这材料对人类专家有无客观对错"——没有就只能做检索/无监督,做不了监督训练燃料;数量里程碑(3000/4002 达标)在无外部真值校验时一律不算进展。
- **重启旧线先查前次终止原因**(10/20 对账新增,勘误档 §四-5 / EFFORT_ACCOUNTING_20261020):复活任何已停线/过期线前,必先找到该线上一次的终止记录与原因并对照"原因是否已消除"——8 月燃料原型当年自然过期,10 月重启无一处引鉴,教训未入 checklist 是再发条件。
<!-- /COMPASS-KG-NODE -->
